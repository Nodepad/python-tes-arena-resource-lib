import os, sys, struct
from PIL import Image
from .Error import *

TESA_IMAGE_PALLETE_SIZE = 0x0300

class Palette:

	@staticmethod
	def fromFile(filename):
		paletteData = open(filename, "rb").read()
		palette = Palette(paletteData)
		palette.name = filename
		palette.internal = False

		return palette

	@staticmethod
	def fromData(data):
		palette = Palette(data)
		palette.internal = True

		return palette

	@staticmethod
	def fromRawData(data):
		return Palette("\x00\x00\x00\x00\x00\x00\x00\x00" + data)

	def __init__(self, paletteData):
		paletteData = bytearray(paletteData)
		paletteDataLen = len(paletteData)

		if paletteDataLen == TESA_IMAGE_PALLETE_SIZE:
			self.palette = [color << 2 for color in paletteData]
		elif paletteDataLen == TESA_IMAGE_PALLETE_SIZE + 8:
			self.palette = paletteData[8:]
		else:
			raise Error(WrongPaletteFormat)

	def data(self):
		return self.palette

	def data6bit(self):
		data = [color >> 2 for color in self.palette]
		return "".join([struct.pack("<B", i) for i in data])
