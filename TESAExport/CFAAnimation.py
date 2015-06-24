import os
from PIL import Image
from .ArenaImage import *
from .Palette import *
from .Error import *

TESA_CFA_FILE_EXTENSION = ".CFA"

class CFAAnimation:

	def __init__(self, filename, palette):

		fileext = os.path.splitext(filename)[1].upper()
		if fileext != TESA_CFA_FILE_EXTENSION:
			raise Error(WrongFileExtensionErrorMessage)

		data = bytearray(open(filename, "rb").read())

		self.height, self.width = struct.unpack("<HH", str(data[2:6]))
		framesCount = struct.unpack("<B", str(data[11]))

		self.palette = palette

		frameDataList = []

		for i in xrange(framesCount):
			frameArrayOffset = 12 + i * 2
			dataOffset = struct.unpack("<H", str(data[frameArrayOffset:frameArrayOffset + 2]))
			frameArrayOffset += 2
			nextDataOffset = struct.unpack("<H", str(data[frameArrayOffset:frameArrayOffset + 2]))

			if (i == framesCount - 1):
				nextDataOffset = len(data)

			frameData = data[dataOffset:nextDataOffset]
			frameDataList.append(frameData)

		self.__unpackFrames(frameDataList)

	def __unpackFrames(self, frameDataList):
		width, height = self.width, self.height
		palette = self.palette
		self.images = []

		for frameData in frameDataList:
			image = ArenaImage(frameData, palette, width, height, 0, 0, TESA_IMAGE_TYPE_RLE)
			self.images.append(image)

	def getRGBAImages(self):
		return [image.getRGBAImage() for image in self.images]
