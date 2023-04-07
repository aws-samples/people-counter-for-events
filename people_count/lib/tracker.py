# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from collections import OrderedDict
import time
from scipy.spatial import distance as dist
import numpy as np


class Tracker:
	def __init__(self, maxDisappeared=50, maxDistance=50):
		self.nextObjectID = 0
		# active object
		self.active_centroids = OrderedDict()
		# disappeard object
		self.disapper_counter = OrderedDict()

		self.maxDisappeared = maxDisappeared
		self.maxDistance = maxDistance

	def register(self, centroid):
		self.active_centroids[self.nextObjectID] = centroid
		self.disapper_counter[self.nextObjectID] = 0
		self.nextObjectID += 1

	def deregister(self, objectID):
		del self.active_centroids[objectID]
		del self.disapper_counter[objectID]

	def update(self, rects):
		deregisters = OrderedDict()
		if len(rects) == 0:
			for objectID in list(self.disapper_counter.keys()):
				self.disapper_counter[objectID] += 1

				if self.disapper_counter[objectID] > self.maxDisappeared:
					deregisters[objectID] = self.active_centroids[objectID]
					self.deregister(objectID)

			return self.active_centroids, deregisters

		inputCentroids = np.zeros((len(rects), 2), dtype="int")

		for (i, (lx, ly, rx, ry)) in enumerate(rects):
			cx = (lx + rx) // 2
			cy = (ly + ry) // 2
			inputCentroids[i] = (cx, cy)

		# 初期化処理
		if len(self.active_centroids) == 0:
			for inputCentroid in inputCentroids:
				self.register(inputCentroid)

		# 既存のObjectが一つ以上存在するとき
		else:
			objectIDs = list(self.active_centroids.keys())
			objectCentroids = list(self.active_centroids.values())

			D = dist.cdist(np.array(objectCentroids), inputCentroids)

			# distanceの近い順に返す
			rows = D.min(axis=1).argsort()
			# 既存Objectsの中で、新規Objectに近いものを選択
			# 距離の近い順で新規Objectのindを並べる
			cols = D.argmin(axis=1)[rows]

			usedRows = set()
			usedCols = set()

			for (row, col) in zip(rows, cols):
				if row in usedRows or col in usedCols:
					continue

				if D[row, col] > self.maxDistance:
					continue

				objectID = objectIDs[row]
				self.active_centroids[objectID] = inputCentroids[col]
				self.disapper_counter[objectID] = 0

				usedRows.add(row)
				usedCols.add(col)

			unusedRows = set(range(0, D.shape[0])).difference(usedRows)
			unusedCols = set(range(0, D.shape[1])).difference(usedCols)

			# 消去処理
			if D.shape[0] >= D.shape[1]:
				for row in unusedRows:
					objectID = objectIDs[row]
					self.disapper_counter[objectID] += 1

					if self.disapper_counter[objectID] > self.maxDisappeared:
						deregisters[objectID] = self.active_centroids[objectID]
						self.deregister(objectID)

			else:
				for col in unusedCols:
					self.register(inputCentroids[col])

		return self.active_centroids, deregisters
