# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

class TrackableObject:
	def __init__(self, objectID, centroid):
		# オブジェクトIDと中心座標の履歴を定義
		self.objectID = objectID
		self.centroids = [centroid]
		# すでにカウントされたかどうか保存
		self.counted = False
		self.enter_counted = False
		self.leave_counted = False