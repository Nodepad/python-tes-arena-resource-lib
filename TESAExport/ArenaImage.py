import sys
from PIL import Image
from .Algorithm import *
from .Palette import Palette

TESA_IMAGE_TYPE_NOCOMPRESSION = 0x0000
TESA_IMAGE_TYPE_RLE = 0x0001
TESA_IMAGE_TYPE_RLE_ALPHA = 0x0002
TESA_IMAGE_TYPE_LZSS = 0x0004
TESA_IMAGE_TYPE_DEFLATE = 0x0008

TESA_IMAGE_WITH_FULL_PALETTE = 0x0100
TESA_IMAGE_WITH_IMAGE_MAP = 0x0800
TESA_IMAGE_WITH_00h_ALPHA = 0x8000

TESA_IMAGE_HEADER_SIZE = 12

def decodeData(data, type):
	unpackedData = None
	type = type & 0x000F

	if type == TESA_IMAGE_TYPE_RLE:
		unpackedData = decodeRLEImageCompression(data)
	elif type == TESA_IMAGE_TYPE_RLE_ALPHA:
		unpackedData = decodeRLEImageCompression(data)
	elif type == TESA_IMAGE_TYPE_LZSS:
		unpackedData = decodeLZSSBasedImageCompression(data)
	elif type == TESA_IMAGE_TYPE_DEFLATE:
		unpackedData = decodeDeflateBasedImageCompression(data)
	elif type == TESA_IMAGE_TYPE_NOCOMPRESSION:
		unpackedData = data

	return unpackedData

def findColor(color, table):
	findTable = []

	for colorEntry in table:
		colorValue = colorEntry[0]

		red = abs(color[0] - colorValue[0])
		green = abs(color[1] - colorValue[1])
		blue = abs(color[2] - colorValue[2])

		findTable.append((max(red, green, blue), colorEntry[1]))

	minDeviation = sys.maxint

	for entry in findTable:
		if minDeviation > entry[0]:
			minDeviation = entry[0]
			index = entry[1]

	return index

def imageQuantize(image, palette):
	image = image.convert("RGBA")
	paletteData = palette.data()
	findTable = []
	table = [[]] * 768

	index = 0

	while len(paletteData) > 0:
		key = paletteData[0] + paletteData[1] + paletteData[2]

		tableEntry = table[key][:]
		tableEntry.append((tuple(paletteData[:3]), index))
		table[key] = tableEntry

		findTable.append((tuple(paletteData[:3]), index))

		paletteData = paletteData[3:]

		index += 1

	imageData = list(image.getdata())
	quaternizedImageData = []

	newIndex = 0

	for pixel in imageData:

		if pixel[3] == 0:
			quaternizedImageData.append(0)
			continue

		key = pixel[0] + pixel[1] + pixel[2]

		for color in table[key]:
			if pixel == color[0]:
				quaternizedImageData.append(color[1])
				break
		else:
			newColor = findColor(pixel, findTable)

			tableEntry = table[key][:]
			tableEntry.append((pixel, newColor))
			table[key] = tableEntry

			quaternizedImageData.append(newColor)
			# raise Exception("WTF %d %d %s" % (key, newIndex, str(list(pixel))))

		newIndex += 1

	quaternizedImage = Image.new("P", image.size)
	quaternizedImage.putpalette(palette.data())
	quaternizedImage.putdata(quaternizedImageData)

	return quaternizedImage

class ArenaImage:

	@staticmethod
	def isHeaderValid(x, y, width, height, imagetype, size):

		imageTypes = [TESA_IMAGE_TYPE_NOCOMPRESSION,
			TESA_IMAGE_TYPE_RLE,
			TESA_IMAGE_TYPE_RLE_ALPHA,
			TESA_IMAGE_TYPE_LZSS,
			TESA_IMAGE_TYPE_DEFLATE]

		if x + width > 320 or width == 0 or y + height > 200 or height == 0:
			return False

		tmpImageType = imagetype & 0xFFF0
		tmpImageType &= (~ TESA_IMAGE_WITH_FULL_PALETTE)
		tmpImageType &= (~TESA_IMAGE_WITH_00h_ALPHA)
		tmpImageType &= (~ TESA_IMAGE_WITH_IMAGE_MAP)

		if tmpImageType != 0:
			return False

		if not ((imagetype & 0x000F) in imageTypes):
			return False

		return True

	@staticmethod
	def fromRGBAImage(image, palette, x = 0, y = 0, imageType = None, forceAlpha = False, noHeader = False):
		convertedImage = imageQuantize(image, palette)

		return ArenaImage(convertedImage, palette, x, y, imageType, forceAlpha, noHeader)

	@staticmethod
	def fromData(data, palette, width, height, x = 0, y = 0, imageType = 0, forceAlpha = False, noHeader = False):
		image = Image.new("P", (width, height))
		print len(list(palette.data()))
		print len(palette.data())
		print list(palette.data())
		image.putpalette(list(palette.data()))

		decodedImageData = decodeData(data, imageType)
		image.putdata(decodedImageData)

		return ArenaImage(image, palette, x, y, imageType, forceAlpha, noHeader)

	def __init__(self, image, palette, x = 0, y = 0, imageType = 0, forceAlpha = False, noHeader = False):
		self.imageType, self.image, self.forceAlpha = imageType, image, forceAlpha
		self.position = (x, y)
		self.size = image.size
		self.palette = palette
		self.noHeader = noHeader

		if imageType & TESA_IMAGE_WITH_00h_ALPHA or imageType & TESA_IMAGE_TYPE_RLE_ALPHA:
			self.forceAlpha = True

		if self.forceAlpha:
			self.alpha = getAlphaImage(self.image.getdata(), *self.size)

	def getCompressedData(self):
		if self.imageType & TESA_IMAGE_TYPE_RLE or self.imageType & TESA_IMAGE_TYPE_RLE_ALPHA:
			return self.getRLEData()
		elif self.imageType & TESA_IMAGE_TYPE_LZSS:
			return self.getLZSSData()
		elif self.imageType & TESA_IMAGE_TYPE_DEFLATE:
			return self.getRLEData()
		else:
			return self.getData()

	def getRLEData(self):
		return encodeRLEImageCompression(self.image.getdata())

	def getLZSSData(self):
		return encodeLZSSBasedImageCompression(self.image.getdata())

	def getData(self):
		data = list(self.image.getdata())
		return "".join([struct.pack("<B", i) for i in data])

	def getRGBAImage(self):
		bitmap = self.image.convert("RGBA")
		if self.forceAlpha: bitmap.putalpha(self.alpha)
		return bitmap
