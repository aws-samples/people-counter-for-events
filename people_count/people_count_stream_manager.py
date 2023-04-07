# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import datetime
import json
import logging
from stream_manager import (
    ExportDefinition,
    KinesisConfig,
    MessageStreamDefinition,
    ResourceNotFoundException,
    StrategyOnFull,
    StreamManagerException,
    StreamManagerClient,
)
import boto3
import asyncio
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class PeopleCountStreamManager:
    def __init__(self, count_stream:str, video_stream_id:int, timezone:datetime.timezone, useStreamManager:bool=True, alone:bool=False):
        self.count_stream = count_stream
        self.video_stream_id = video_stream_id
        self.timezone = timezone
        self.alone = alone

        # StreamManagerを使うかどうか
        if not self.alone:
            if useStreamManager:
                self.stream_client = StreamManagerClient()
            else:
                self.stream_client = boto3.client('kinesis')
                
        # streamが存在するか確認
        if not self.alone:
            try:
                logger.info(f"video_stream_id: {self.video_stream_id}, start list streams")
                list_streams = self.stream_client.list_streams()
                logger.info(f"video_stream_id: {self.video_stream_id}, list streams: {list_streams}")
            except StreamManagerException:
                logger.error(f"video_stream_id: {self.video_stream_id}, StreamManagerException")
            except ConnectionError:
                logger.error(f"video_stream_id: {self.video_stream_id}, ConnectionError")
            except:
                logger.error(f"video_stream_id: {self.video_stream_id}, Some Error while connecting to stream")
            
            # streamが存在しない場合はstreamを作成
            if count_stream not in list_streams:
                self.create_stream(count_stream)

    def create_stream(self, stream_name):
        exports = ExportDefinition(
            kinesis=[KinesisConfig(
                identifier="KinesisExport" + stream_name,
                kinesis_stream_name=stream_name,
                batch_size=2 # 確認しやすいように、10件溜まったら送信するようにする
            )]
        )
        logger.info(f"video_stream_id: {self.video_stream_id}, Creating stream: {stream_name}")
        try:
            self.stream_client.create_message_stream(
                MessageStreamDefinition(
                    name=stream_name,
                    strategy_on_full=StrategyOnFull.OverwriteOldestData,
                    export_definition = exports
                )
            )
        except StreamManagerException:
            logger.error('Stream manager exception')
        except ConnectionError or asyncio.TimeoutError:
            logger.error('Connection error')
    
    # データの送信
    def send_message(self, stream_name, data:str):
        if self.alone:
            try:
                self.stream_client.put_record(
                StreamName = stream_name,
                Data=data,
                PartitionKey = '0'
                )
            except:
                print('kinesis stream error')
            return 0

        try:
            self.stream_client.append_message(
            stream_name = stream_name,
            data = data.encode('utf-8')
            )   
        except StreamManagerException:
            logger.error(f"video_stream_id: {self.video_stream_id}, StreamManagerException")
        except ConnectionError:
            logger.error(f"video_stream_id: {self.video_stream_id}, ConnectionError")
        except:
            logger.error(f"video_stream_id: {self.video_stream_id}, Some Error while connecting to stream")


    def leave(self):
        send_json = json.dumps(
            {
                "camera_timestamp":datetime.datetime.now(self.timezone).isoformat(),
                "video_stream_id": self.video_stream_id,
                "event": "leave"
            }
        )
        self.send_message(self.count_stream, send_json)

    def enter(self):
        send_json = json.dumps(
            {
                "camera_timestamp":datetime.datetime.now(self.timezone).isoformat(),
                "video_stream_id": self.video_stream_id,
                "event": "enter"
            }
        )
        self.send_message(self.count_stream, send_json)
    