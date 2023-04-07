## Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
## SPDX-License-Identifier: MIT-0

from __future__ import print_function
import base64
import boto3
import json
import os
import traceback
import requests
from datetime import datetime,timedelta, timezone

graphql_url = os.environ.get('GRAPHQL_URL')
api_key = os.environ.get('API_KEY')
session = boto3.session.Session()
credentials = session.get_credentials()
method= 'POST'
region = 'ap-northeast-1'
service= 'appsync'
endpoint = graphql_url
headers = {"x-api-key":api_key, "Content-Type": "application/json"}

'''
This Kinesis data(Json Image) is below
{    "video_stream_id": int,    
     "camera_timestamp": "2022-09-13T09:55:51.318009+09:00",
     "event" : "enter"
     }
'''

def decode_kinesis_data(data_list):
    '''
    Kinesis Data decoding process
    Args:
        data_list(list): kinesis raw data
    Returns:
        decoded_list(list): kinesis decoded data
    '''
    decoded_list = []
    try:
        for data in data_list:
            payload =  base64.b64decode(data['kinesis']['data'])
            print("kinesis_decode_data:{}".format(payload))
            decoded_list.append(payload)
        return decoded_list
    except Exception as e:
        print("Error on decodeKinesisData()")
        raise e
     
def check_item(str_data):
    """
    Dictionary data of converted kinesis data
    Args:
        str_data(str): kinesis decoded data
    Returns:
        resDict(dict): kinesis converted data
    """
    try:
        #String to Json object
        json_data = json.loads(str_data)
        print(json_data)
        # extract event key
        event_type =  json_data['event']
        # Convert event to metric
        if event_type == 'enter':
            event_int = 1
        else:
            event_int = -1
        # Create dictionary data
        resDict = {
            'video_stream_id': json_data['video_stream_id'],
            'event_int': event_int,
            'camera_timestamp': json_data['camera_timestamp']
            }       
        print("event_type:{}".format(event_type))
        print("resDict:{}".format(resDict))
        return resDict
    except Exception as e:
        print(traceback.format_exc())
        return None

def write_dict_info(datas):
    """
    Add Dictionary data to array
    Args:
        datas(str): kinesis converted data
    Returns:
        item_info_dictlist(list): Dictionary data
    """
    item_info_dictlist = []
    try:
        for data in datas:
            item_dict = check_item(data)
            if None != item_dict:
                item_info_dictlist.append(item_dict)
            # if data does not have key info, just pass
            else:
                print("Error data found:{}".format(data))
                pass
        return item_info_dictlist
    except Exception as e:
        print(traceback.format_exc())
        print("Error on write_dict_info()")
        raise e


def camera_put(timestamp, datas):
    """
    Aggregate data in array and send to AppSync
    Args:
        timestamp(str): kinesis converted data
        datas
    """
    try:
        update_item_dictlist = write_dict_info(datas)
        count_update_dict = {}
        total_update_dict = {}
        timestamp_update_dict = {}

        for update_item_dict in update_item_dictlist:
            #Add value to dictionary depending on presence or absence of 'video_stream_id' value
            if update_item_dict['video_stream_id'] not in count_update_dict:
                count_update_dict[update_item_dict['video_stream_id']] = 0
                total_update_dict[update_item_dict['video_stream_id']] = 0
                timestamp_update_dict[update_item_dict['video_stream_id']] = update_item_dict['camera_timestamp']
                count_update_dict[update_item_dict['video_stream_id']] += update_item_dict['event_int']
                #Add value to 'total_update_dict'
                if update_item_dict['event_int'] ==1:
                    total_update_dict[update_item_dict['video_stream_id']] += 1
            else:
                timestamp_update_dict[update_item_dict['video_stream_id']] = update_item_dict['camera_timestamp']
                count_update_dict[update_item_dict['video_stream_id']] += update_item_dict['event_int']
                if update_item_dict['event_int'] ==1:
                    total_update_dict[update_item_dict['video_stream_id']] += 1
                print("count_update_dict:{}".format(count_update_dict))
                print("total_update_dict:{}".format(total_update_dict))
                print("timestamp_update_dict:{}".format(timestamp_update_dict))

       #Send to AppSync
        for video_stream_id in count_update_dict.keys():
            params= {
                    "video_stream_id": str(video_stream_id),
                    "current_count": count_update_dict[video_stream_id],
                    "total_count": total_update_dict[video_stream_id],
                    "camera_timestamp": timestamp_update_dict[video_stream_id],
                    "update_timestamp": timestamp
            }
            
            mutation = """
                       mutation MyMutation ($input: UpdatevideostreamInput!){
                          updatevideostream(input: $input) {
                            camera_timestamp
                            current_count
                            total_count
                            update_timestamp
                            video_stream_id
                          }
                        }                       
                """           
            
            variables = {'input': params}
            payload = {"query": mutation , "variables": variables}
            
            response = requests.request(
            method,
            endpoint,
            json=payload,
            headers=headers
        )
        
        if 'errors' in response:
            print('Error attempting to query AppSync')
            print(response['errors'])
        else:
            return response
            
    except Exception as e:
        print(traceback.format_exc())
        print("Error on camera_put()")
        raise e      

#------------------------------------------------------------------------
# call by Lambda here.
#------------------------------------------------------------------------
def handler(event, context):
    
    print("handler start")
    try:
        print("---------------json inside----------------")
        #get current time
        tz = timezone(timedelta(hours=9))
        NOW_TIMESTAMP = datetime.now(tz).isoformat()
        #get kinesis data
        print(json.dumps(event))
        encode_kinesis_list = event['Records']
        #decode kinesis data
        decoded_kinesis_list = decode_kinesis_data(encode_kinesis_list)
        #Send to AppSync
        if 0 < len(decoded_kinesis_list):
            camera_put(NOW_TIMESTAMP,decoded_kinesis_list)                    
        else:
            print("there is no valid data in Kinesis stream, all data passed")

        return
    except Exception as e:
        print(traceback.format_exc())
        # This is sample source. When error occur this return success and ignore the error.
        raise e
