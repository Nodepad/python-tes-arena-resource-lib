import os, struct
from PIL import Image
from .Palette import *
from .Algorithm import *
from .Error import *

TESA_DFA_HEADER_SIZE = 12
TESA_DFA_FILE_EXTENSION = ".DFA"

class DFAAnimation:

	def __init__(self, filename, palette):

		fileext = os.path.splitext(filename)[1].upper()
		if fileext != TESA_DFA_FILE_EXTENSION: raise Error, WrongFileExtensionErrorMessage

		data = bytearray(open(filename, "rb").read())

		self.framesCount, self.x, self.y, self.width, self.height, firstFrameDataSize = struct.unpack("<HHHHHH", str(data[:TESA_DFA_HEADER_SIZE]))
		self.frames = []
		self.palette = palette

		del data[:TESA_DFA_HEADER_SIZE]

		self.__unpackFirstFrame(data[:firstFrameDataSize])

		del data[:firstFrameDataSize]

		for i in xrange(1, self.framesCount):
			self.__unpackNextFrame(data)

	def getRGBAFrames(self):

		rgbaFrames = []

		for frame in self.frames:
			frame.convert("RGBA")
			width, height = frame.size
			frame.putalpha(getAlphaImage(frame.getdata(), width, height))
			rgbaFrames.append(frame)

		return rgbaFrames

	def __unpackFirstFrame(self, frameData):

		image = Image.new("P", (self.width, self.height))
		image.putpalette(self.palette.data())
		image.putdata(decodeRLEImageCompression(frameData))

		self.frames.append(image)

	def __unpackNextFrame(self, frameData):

		image = self.frames[0].copy()
		unpackedData = bytearray(image.getdata())

		packedImageSize, relocationEntriesCount = struct.unpack("<HH", str(frameData[:4]))
		del frameData[:4]

		for i in xrange(0, relocationEntriesCount):
			dataOffset, dataLength = struct.unpack("<HH", str(frameData[:4]))
			unpackedData[dataOffset:dataOffset + dataLength] = frameData[4:dataLength + 4]
			del frameData[0:dataLength + 4]

		image.putdata(unpackedData)
		self.frames.append(image)
