# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from typing import List

# targetがarea内にあるかどうか検知する関数
def is_in_area(area: List[int], target: List[int]) -> bool:
  if area[0] <= target[0] and target[0] <= area[2] and area[1] <= target[1] and target[1] <= area[3]:
    return True

  else:
    return False

# /で区切られた,文字列をintリストに変換
def sepparser(x):
    commalist = x.split('/')
    result = [list(map(int, x.split(','))) for x in commalist]
    return result 

# ,で区切られた文字列をintリストに変換する
def listparser(x): return list(map(int, x.split(',')))