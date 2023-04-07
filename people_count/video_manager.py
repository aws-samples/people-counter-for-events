# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from typing import Tuple
import time

import cv2
import numpy as np


class VideoStreamManager:
    def __init__(self, input: str|int) -> None:
        self.videostream = cv2.VideoCapture(input)
        self.videolength = int(self.videostream.get(cv2.CAP_PROP_FRAME_COUNT))
        self.videolength = -2 if self.videolength == 0 or self.videolength == -1 else self.videolength
        self.input = input
        self.reconnect_count = 0

        self.MAX_RECONNECT = 5
        self.RECONNECT_INTERVAL = 1.0

    def read(self) -> Tuple[bool, np.ndarray]:
        '''
        戻り値: 読み込みの成否, frame
        '''
        retval, frame = self.videostream.read()
        
        # ビデオファイルの終わりに来た際は終了する
        if int(self.videostream.get(cv2.CAP_PROP_POS_FRAMES)) == self.videolength:
            return False, None

        # カメラの接続が途切れた際に再接続を試みる
        while not retval:
            if not self.reconnect():
                return False, None
            retval, frame = self.videostream.read()
            
        self.reconnect_count = 0
        return True, frame

    def reconnect(self) -> bool:
        '''
        戻り値: 再接続を続けるかどうか
        '''
        if self.reconnect_count > self.MAX_RECONNECT:
            print('[ERROR] could not read frame.')
            return False

        print(f'[INFO] reconnecting. count: {self.reconnect_count}')
        self.reconnect_count += 1
        self.videostream = cv2.VideoCapture(self.input)
        time.sleep(self.RECONNECT_INTERVAL)
        return True

    def release(self) -> None:
        self.videostream.release()
