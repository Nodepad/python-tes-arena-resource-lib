import Image, struct, os, sys, getopt

def unpackSymbol(height, width, symbolData):
	symbolImageData = []
	for row in xrange(height):
		pixel = (symbolData[row * 2 + 1] << 8) + symbolData[row * 2]
		symbolImageData.extend([((pixel >> (15 - pixelPart)) & 0x01) for pixelPart in xrange(16)])

	symbolImage = Image.new("1", (16, height))
	symbolImage.putdata(symbolImageData)

	return symbolImage

def unpackFont(fontFilename):

	fontFile = open(fontFilename, "rb")
	fontData = bytearray(fontFile.read())

	fontHeight = fontData[0]

	if ((len(fontData) - 1) % (fontHeight * 2 + 1)) != 0:
		raise Exception("ERROR: Image width should be product of 16. Symbols with width 16 pixels each in one row.")

	charactersNumber = (len(fontData) - 1) / (fontHeight * 2 + 1)

	unpackedFontImage = Image.new("1", (16 * charactersNumber, fontHeight))

	for symbol in xrange(charactersNumber):
		symbolWidth = fontData[symbol + 1]
		startIndex = (charactersNumber + 1) + symbol * 2 * fontHeight
		endIndex = startIndex + 2 * fontHeight
		symbolData = fontData[startIndex:endIndex]

		symbolImage = unpackSymbol(fontHeight, symbolWidth, symbolData)

		unpackedFontImage.paste(symbolImage, (16 * symbol, 0))

		return unpackedFontImage

def packSymbol(symbolImage):
	height = symbolImage.size[1]

	symbolImageData = symbolImage.getdata()
	symbolWidth = 0
	symbolData = []
	for y in xrange(height):
		lineNumber = 0
		for x in xrange(16):
			if symbolImageData[y * 16 + x] != 0:
				lineNumber |= 0x01 << (15 - x)
				symbolWidth = max(symbolWidth, x + 2)
		symbolData.append(lineNumber)

	return (symbolWidth, "".join([struct.pack("<H", line) for line in symbolData]))

def packFont(fontImage):
	fontImage = fontImage.convert("1")

	imageWidth, fontHeight = fontImage.size

	if imageWidth % 16 != 0:
		raise Exception("ERROR: Image width should be product of 16. Symbols with width 16 pixels each in one row.")

	charactersNumber = imageWidth / 16

	widths = []
	datas = []
	for symbol in xrange(charactersNumber):
		symbolImage = fontImage.crop((symbol * 16, 0, (symbol + 1) * 16, fontHeight))
		width, data = packSymbol(symbolImage)
		widths.append(width)
		datas.append(data)

	widthsString = "".join([struct.pack("<B", width) for width in widths])
	datasString = "".join(datas)
	data = "".join([struct.pack("<B", fontHeight), widthsString, datasString])

	return data

class DATFont:
	@staticmethod
	def fromOriginalFile(filename):
		return DATFont(unpackFont(filename))

	@staticmethod
	def fromImage(image):
		return DATFont(image)

	def __init__(self, image):
		self.image = image

	def saveOriginalFile(self, filename):
		data = packFont(self.image)

		file = open(filename, "wb")
		file.write(data)
		file.close()

	def getImage(self):
		return self.image
