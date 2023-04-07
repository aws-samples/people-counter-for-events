# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import argparse
import time
import datetime
from typing import Tuple

import dlib
import numpy as np
import cv2
from imutils.video import FPS

from people_count_stream_manager import PeopleCountStreamManager
from video_manager import VideoStreamManager
from lib.tracker import Tracker
from lib.trackableObject import TrackableObject
import lib.utils as utils


def main(args):
    FRAME_WIDTH = 1000

    # 機械学習モデルのラベルリストをロード
    print("[INFO] loading labels...")
    with open(args["label"], "r") as f:
        CLASSES = f.read().split("\n")

    # 機械学習モデルのロード
    print("[INFO] loading model...")
    if args["model"][-10:] == "caffemodel":
        net = cv2.dnn.readNetFromCaffe(args["prototxt"], args["model"])
    else:
        net = cv2.dnn.readNetFromTensorflow(args["model"], args["prototxt"])

    # 動画読み込み元の指定
    # 指定がない場合は内蔵webカメラを、ある場合は指定先を読み込む
    if not args.get("input", False):
        print("[INFO] starting video stream...")
        video_stream = VideoStreamManager(0)
    else:
        print("[INFO] opening video file...")
        video_stream = VideoStreamManager(args["input"])

    # 検知エリアの指定
    area = args.get("area")

    # GUIで動画を表示するかの指定
    gui_show = args.get("gui")

    # video_stream_idの設定
    video_stream_id = 0
    if args.get("video_stream_id"):
        video_stream_id = args["video_stream_id"]

    # line検知指定
    line_y = args.get("line")

    if area:
        url = args.get("url")
        assert url != "", "url is not set"

    # StreamClientの初期化
    print(type(args["stream"]), args["stream"])
    if args["stream"] != "":
        stream_client = PeopleCountStreamManager(
            args.get("stream"),
            video_stream_id,
            datetime.timezone(datetime.timedelta(hours=args.get("timezone"))),
        )
    else:
        stream_client = PeopleCountStreamManager(
            "stream",
            video_stream_id,
            datetime.timezone(datetime.timedelta(hours=args.get("timezone"))),
            alone=True
        )

    video_writer = None

    # フレームサイズの初期化
    W = None
    H = None

    # Trackerの初期化
    ct = Tracker(
        maxDisappeared=args["max_disappeared"], maxDistance=args["max_distance"])
    trackers = []
    trackableObjects = {}

    # カウンタの初期化
    totalFrames = 0
    totalDown = 0
    totalUp = 0
    totalEnter = 0
    totalLeave = 0
    nowEnter = 0

    # frame skipのための計測
    last_detect_time = time.time()

    # FPSの計測
    fps = FPS().start()

    while True:
        result, frame = video_stream.read()

        if not result:
            break

        # frameのrgbを変換
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        if W is None or H is None:
            (H, W) = frame.shape[:2]

        # outputが指定されている場合はwriterを初期化
        if args["output"] is not None and video_writer is None:
            fourcc = cv2.VideoWriter_fourcc(*"MJPG")
            video_writer = cv2.VideoWriter(args["output"], fourcc, 30,
                                           (W, H), True)

        status = "Waiting"
        rects = []

        # 機械学習モデルでの検知を行うかどうか
        # 処理に時間がかかるため、フレームを間引いて実行
        if (time.time() - last_detect_time) * 1000 > args["skip_frames"]:
            status = "Detecting"
            trackers = []

            # 機械学習モデルでの検知
            blob = cv2.dnn.blobFromImage(frame, size=(300, 300), swapRB=True, crop=False)
            net.setInput(blob)
            detections = net.forward()

            # 検知結果についてループ
            for i in np.arange(0, detections.shape[2]):
                # 確信度を取得
                confidence = detections[0, 0, i, 2]

                # 確信度が一定値以上のものを取得
                if confidence > args["confidence"]:
                    idx = int(detections[0, 0, i, 1])

                    # if CLASSES[idx] != "person":
                    #     continue

                    # boxの座標取得
                    box = detections[0, 0, i, 3:7] * np.array([W, H, W, H])
                    (lx, ly, rx, ry) = box.astype("int")

                    # 類似度ベースのtracking
                    tracker = dlib.correlation_tracker()
                    rect = dlib.rectangle(lx, ly, rx, ry)
                    tracker.start_track(rgb, rect)

                    trackers.append(tracker)

            last_detect_time = time.time()
        # 機械学習によらない物体追跡
        else:
            # トラッカーに対するループ
            for tracker in trackers:
                status = "Tracking"

                tracker.update(rgb)
                pos = tracker.get_position()

                lx = int(pos.left())
                ly = int(pos.top())
                rx = int(pos.right())
                ry = int(pos.bottom())

                rects.append((lx, ly, rx, ry))

        # 検知した物体ボックスの描画
        for rect in rects:
            cv2.rectangle(frame, rect[0:2], rect[2:4], color=(0, 0, 200))

        # 検知ラインの描画
        if line_y:
            cv2.line(frame, (0, line_y), (W, line_y), (0, 255, 255), 2)

        # 検知エリアの描画
        if area:
            cv2.rectangle(frame, area[0:2], area[2:4], color=(200, 0, 0))

        # Trackerを更新
        objects, deregisters = ct.update(rects)

        nowEnter = 0

        # 領域内で物体が消失したときにtotalLeaveを+1
        if area:
            for (objectID, centroid) in deregisters.items():
                if utils.is_in_area(area, centroid):
                    totalLeave += 1
                    stream_client.leave()

        # 追跡対象のオブジェクトを取得
        for (objectID, centroid) in objects.items():
            trackable_object = trackableObjects.get(objectID, None)

            if trackable_object is None:
                trackable_object = TrackableObject(objectID, centroid)

            # 移動方向を計算
            else:
                # 追跡物体のこれまでのy座標のリスト
                xs = [c[0] for c in trackable_object.centroids]
                ys = [c[1] for c in trackable_object.centroids]

                # 領域検知
                if area:
                    if utils.is_in_area(area, centroid):
                        nowEnter += 1

                    # 過去5フレームのx,y座標の平均
                    xmean, ymean = np.mean(xs[:-5]), np.mean(ys[:-5])
                    # 新たに領域内に入った場合、enterイベントを送信する
                    if not trackable_object.enter_counted and utils.is_in_area(area, centroid):
                        totalEnter += 1
                        trackable_object.enter_counted = True
                        stream_client.enter()

                    # 領域から出た場合、leaveイベントを送信する
                    if not trackable_object.leave_counted and not utils.is_in_area(area, centroid) and utils.is_in_area(area, [xmean, ymean]):
                        totalLeave += 1
                        trackable_object.leave_counted = True
                        stream_client.leave()
                direction = centroid[1] - np.mean(ys)

                trackable_object.centroids.append(centroid)

                if not trackable_object.counted and line_y:
                    # 検知ラインを上向きにクロスした場合、退出としてカウント
                    if direction < 0 and centroid[1] < line_y and ys[-1] >= line_y:
                        totalUp += 1
                        trackable_object.counted = True
                        stream_client.leave()

                    # 検知ラインを下向きにクロスした場合、入場としてカウント
                    elif direction > 0 and centroid[1] > line_y and ys[-1] <= line_y:
                        totalDown += 1
                        trackable_object.counted = True
                        stream_client.enter()

            trackableObjects[objectID] = trackable_object

            # objectIDの描画
            text = f"ID {objectID}"
            cv2.putText(frame, text, (centroid[0] - 10, centroid[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            cv2.circle(frame, (centroid[0], centroid[1]), 4, (0, 255, 0), -1)

        # 各種情報を描画
        info = [
            ("InArea", nowEnter),
            ("Enter", totalEnter),
            ("Leave", totalLeave),
            ("Status", status)
        ]

        for (i, (k, v)) in enumerate(info):
            text = "{}: {}".format(k, v)
            cv2.putText(frame, text, (10, H - ((i * 20) + 20)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        # 動画の出力
        if video_writer is not None:
            video_writer.write(frame)

        if gui_show:
            # show the output frame
            cv2.imshow("Frame", frame)
            key = cv2.waitKey(1) & 0xFF

            # # if the `q` key was pressed, break from the loop
            if key == ord("q"):
                break

        totalFrames += 1
        fps.update()

    # FPS情報の表示
    fps.stop()
    print("[INFO] elapsed time: {:.2f}".format(fps.elapsed()))
    print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))

    # video writerの終了
    if video_writer is not None:
        video_writer.release()

    video_stream.release()

    if args.get("gui"):
        cv2.destroyAllWindows()


if __name__ == "__main__":
    # システム引数の追加
    argparser = argparse.ArgumentParser()
    argparser.add_argument("-p", "--prototxt", required=True,
                           help="path to Caffe 'deploy' prototxt file")
    argparser.add_argument("-m", "--model", required=True,
                           help="path to Caffe pre-trained model")
    argparser.add_argument("-t", "--label", required=True, type=str,
                           help="path to target object label file")
    argparser.add_argument("-i", "--input", type=str,
                           help="path to optional input video file")
    argparser.add_argument("-o", "--output", type=str,
                           help="path to optional output video file")
    argparser.add_argument("-c", "--confidence", type=float, default=0.4,
                           help="minimum probability to filter weak detections")
    argparser.add_argument("-s", "--skip-frames", type=int, default=1500,
                           help="time(ms) to skip detection between")
    argparser.add_argument("-a", "--area", required=False,
                           help="video area to count people (sx, sy, gx, gy)", type=utils.listparser)
    argparser.add_argument("-g", "--gui", action="store_true",
                           help="whether showing gui")
    argparser.add_argument("-l", "--line", type=int,
                           help="y coordinates for line based detection")
    argparser.add_argument("-vsid", "--video_stream_id", required=False, type=int,
                           help="video_stream_id to send to the stream")
    argparser.add_argument("-stream", "--stream", default="",
                           help="Stream name to send events")
    argparser.add_argument("-tz", "--timezone", type=int, default=9,
                           help="diffence between utc and local timezone (by default, JST)")
    argparser.add_argument("--max_disappeared", default=40, type=int,
                           help="tracking max_disappeard")
    argparser.add_argument("--max_distance", default=50, type=int,
                           help="tracking max distance")

    args = vars(argparser.parse_args())
    main(args)
