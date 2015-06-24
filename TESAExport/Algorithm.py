import sys, struct
from PIL import Image

TESA_IMAGE_WITH_FULL_PALETTE = 0x0100
TESA_IMAGE_WITH_00h_ALPHA = 0x8000

TESA_IMAGE_PALLETE_SIZE = 0x0300

TESA_IMAGE_HEADER_SIZE = 12
TESA_DFA_HEADER_SIZE = 10

def getAlphaImage(data, width, height):

	alphaData = []

	for i in xrange(width * height):
		if data[i] == 0: alphaData.append(0x00)
		else: alphaData.append(0xFF)

	alphaImage = Image.new("L", (width, height))
	alphaImage.putdata(alphaData)
	return alphaImage

def decodeRLEImageCompression(data):

	dataToDecode = bytearray(data)
	unpackedData = bytearray()
	packedImageSize = len(dataToDecode)

	while packedImageSize > 0:
		leadByte = dataToDecode.pop(0)

		if leadByte & 0x80:
			pixelsCount = (leadByte & 0x7F) + 1
			packedImageSize -= 2

			pixelColor = dataToDecode.pop(0)

			unpackedData.extend([pixelColor] * pixelsCount)
		else:
			pixelsCount = leadByte + 1

			packedImageSize -= pixelsCount + 1

			unpackedData.extend(dataToDecode[:pixelsCount])
			del dataToDecode[:pixelsCount]

	return unpackedData

def encodeRLEImageCompression(data):

	def findNextRun(data):
		if len(data) > 3:
			i = 2

			if data[i] == data[i - 1] and data[i] == data[i - 2]:
				runValue = data[i]

				while i < len(data) and data[i] == runValue:
					i += 1

				return (i, [runValue])
			else:
				while i < len(data):
					if data[i] == data[i - 1] and data[i] == data[i - 2]:
						i -= 2
						break
					else:
						i += 1

				return (i, data[:i])

		return (len(data), data[:])

	dataToEncode = bytearray(data)
	packedData = bytearray()

	while len(dataToEncode):
		length, value = findNextRun(dataToEncode)
		dataToEncode = dataToEncode[length:]

		if len(value) == 1:
			while length > 0:
				lenVal = min(length, 128)
				length -= lenVal

				lenVal -= 1
				lenVal |= 0x80

				packedData.append(lenVal)
				packedData.extend(value)
		else:
			while length > 0:
				lenVal = min(length, 128)
				length -= lenVal

				dataVal = value[:lenVal]
				value = value[lenVal:]

				lenVal -= 1
				packedData.append(lenVal)
				packedData.extend(dataVal)

	return packedData

class Dictionary:
	def __init__(self, array, index):
		self.data = []
		self.dictionary = array
		self.index = index
	def appendCodeWord(self, codeWord):
		self.data.append(codeWord)
		self.dictionary[self.index] = codeWord
		self.index = (self.index + 1) & 0x0FFF
	def appendCodeString(self, index, length):
		for i in xrange(index, index + length): self.appendCodeWord(self.dictionary[i & 0xFFF])

def decodeLZSSBasedImageCompression(data):
	dataToDecode = bytearray(data)
	dictionary = Dictionary([0x20] * 0x1000, 0xFEE)
	codeWordType = 0

	while len(dataToDecode) != 0:
		codeWordType = codeWordType >> 1

		if (codeWordType & 0xFF00) == 0: codeWordType = (dataToDecode.pop(0) | 0xFF00)

		if (codeWordType & 0x0001) != 0: dictionary.appendCodeWord(dataToDecode.pop(0))
		else:
			if len(dataToDecode) < 2: break

			codeWordIndex = dataToDecode.pop(0)
			codeWordLength = dataToDecode.pop(0)

			codeWordIndex |= (codeWordLength & 0x00F0) << 4
			codeWordLength = (codeWordLength & 0x000F) + 3

			dictionary.appendCodeString(codeWordIndex, codeWordLength)

	return dictionary.data

class EncodeDictionary:
	def __init__(self, dictionary, index):
		self.codes = []
		self.dictionary = dictionary
		self.index = index
	def addData(self, data):
		dct = self.dictionary
		if self.index + len(data) > 0xFFF:
			separator = 0x1000 - self.index
			start = len(data) - separator
			self.dictionary = data[separator:] + dct[start:self.index] + data[:separator]
		else:
			self.dictionary = dct[:self.index] + data + dct[self.index + len(data):]
		self.index = (self.index + len(data)) & 0xFFF
	def addCodeString(self, codeString):
		length = len(codeString[1])
		hi = (length - 3) | (codeString[0] & 0x0F00) >> 4
		lo = codeString[0] & 0x00FF
		self.codes.append(struct.pack("<BB", lo, hi))
		self.addData(codeString[1])
	def addCodeWord(self, codeWord):
		self.codes.append(codeWord)
		self.addData(codeWord)
	def findCodeString(self, data):
		result = None
		def checkRegion(one, two):
			oneEnd = one[0] + one[1]
			twoEnd = two[0] + two[1]
			return (two[0] < one[0] or two[0] > oneEnd) and (one[0] < two[0] or one[0] > twoEnd)
		for i in xrange(3, min(18, len(data))):
			dataPart = data[:i]
			res = self.dictionary.find(dataPart)
			while res != -1 and not checkRegion((res, i), (self.index, i)):
				res = self.dictionary.find(dataPart, res + 1)
			if res == -1:
				break
			result = (res, dataPart)
		return result
	def getResult(self):
		result = ""
		codesCount = len(self.codes)
		for i in xrange(0, codesCount, 8):
			codeType = 0
			codePart = ""
			for j in xrange(min(8, codesCount - i)):
				code = self.codes[i + j]
				if len(code) == 1:
					codeType |= 1 << j
				codePart += code
			result += chr(codeType)
			result += codePart
		return result

def encodeLZSSBasedImageCompression(data):
	dataToEncode = bytearray(data)
	dictionary = EncodeDictionary(" " * 0x1000, 0xFEE)

	while len(dataToEncode) != 0:
		codeString = dictionary.findCodeString(dataToEncode)

		if codeString:
			dictionary.addCodeString(codeString)
			dataToEncode = dataToEncode[len(codeString[1]):]
		else:
			dictionary.addCodeWord(chr(dataToEncode.pop(0)))

	return dictionary.getResult()

def decodeDeflateBasedImageCompression(data):

	class ComplexLZ77BasedCompressedImage:

		byte_46C2E = [0] * 0x20 + [1] * 0x10 + [2] * 0x10 + [3] * 0x10 + [4] * 8 + [5] * 8 + [6] * 8 + [7] * 8 + [8] * 8 + [9] * 8 + [0xA] * 8 + \
					 [0xB] * 8 + [0xC] * 4 + [0xD] * 4 + [0xE] * 4 + [0xF] * 4 + [0x10] * 4 + [0x11] * 4 + [0x12] * 4 + [0x13] * 4 + [0x14] * 4 + \
					 [0x15] * 4 + [0x16] * 4 + [0x17] * 4 + [0x18] * 2 + [0x19] * 2 + [0x1A] * 2 + [0x1B] * 2 + [0x1C] * 2 + [0x1D] * 2 + [0x1E] * 2 + \
					 [0x1F] * 2 + [0x20] * 2 + [0x21] * 2 + [0x22] * 2 + [0x23] * 2 + [0x24] * 2 + [0x25] * 2 + [0x26] * 2 + [0x27] * 2 + [0x28] * 2 + \
					 [0x29] * 2 + [0x2A] * 2 + [0x2B] * 2 + [0x2C] * 2 + [0x2D] * 2 + [0x2E] * 2 + [0x2F] * 2 + [0x30, 0x31, 0x32] + \
					 [0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3A, 0x3B, 0x3C, 0x3D, 0x3E, 0x3F]
		byte_46D2E = [3] * 0x20 + [4] * 0x30 + [5] * 0x40 + [6] * 0x30 + [7] * 0x30 + [8] * 0x10

		def __init__(self, data):

			self.dataToDecode = bytearray(data)

			self.dynHaffmanTreeReverse = [0] * 941
			self.dynHaffmanTreeMain = [0] * 627
			self.dynHaffmanTreeCost = [0] * 628

			self.loadedBitsCount = 0
			self.bitsArray = 0

			dataLengthToUnpack = struct.unpack("<H", str(self.dataToDecode[:2]))[0] # Overall data length after unpack
			del self.dataToDecode[:2]

			if dataLengthToUnpack == 0:
				raise Error

			self.initHaffmanTree()

			self.dictionary = Dictionary([0x20] * 4036 + [0x00] * 119, 4036)

			actualUnpackedDataLength = 0
			while actualUnpackedDataLength < dataLengthToUnpack:
				codeWord = self.getNextCodeWord() # Get color type descriptor

				if codeWord < 0x100:
					self.dictionary.appendCodeWord(codeWord)
					actualUnpackedDataLength += 1
				else:
					codeWordIndex = (self.dictionary.index - self.getDictionaryOffset() - 1) & 0x0FFF
					codeWordLength = (codeWord & 0xFF) + 3

					self.dictionary.appendCodeString(codeWordIndex, codeWordLength)
					actualUnpackedDataLength += codeWordLength

		def getUnpackedData(self):
			return self.dictionary.data

		def getDictionaryOffset(self):
			v1 = self.getBitsFromStream(8)

			var2 = self.byte_46C2E[v1] << 6

			for i in xrange(0, self.byte_46D2E[v1] - 2):
				v1 = v1 << 1 | self.getBitsFromStream(1)

			return (v1 & 0x3F) | var2

		def initHaffmanTree(self):
			for i in xrange(314):
				self.dynHaffmanTreeCost[i], self.dynHaffmanTreeMain[i], self.dynHaffmanTreeReverse[i + 627] = (1, i + 627, i)

			for i in xrange(314, 627):
				j = (i - 314) * 2 # xrange(0, 627, 2)

				self.dynHaffmanTreeCost[i], self.dynHaffmanTreeMain[i], self.dynHaffmanTreeReverse[j + 1], self.dynHaffmanTreeReverse[j] = (self.dynHaffmanTreeCost[j] + self.dynHaffmanTreeCost[j + 1], j, i, i)

			self.dynHaffmanTreeCost[627] = 0xFFFF
			self.dynHaffmanTreeReverse[626] = 0

		def getNextCodeWord(self):
			i = self.dynHaffmanTreeMain[626]

			while i < 627: i = self.dynHaffmanTreeMain[i + self.getBitsFromStream(1)]

			i -= 627

			self.rebuildHaffmanTree(i)

			return i

		def rebuildHaffmanTree(self, arg1):
			i = self.dynHaffmanTreeReverse[arg1 + 627]

			while True:
				self.dynHaffmanTreeCost[i] += 1
				keyLeafCost = self.dynHaffmanTreeCost[i]

				j = i + 1
				if self.dynHaffmanTreeCost[j] < keyLeafCost:

					while True:
						if self.dynHaffmanTreeCost[j] >= keyLeafCost: break
						j += 1

					j -= 1
					self.dynHaffmanTreeCost[i] = self.dynHaffmanTreeCost[j]
					self.dynHaffmanTreeCost[j] = keyLeafCost
					keyLeafValue = self.dynHaffmanTreeMain[i]
					self.dynHaffmanTreeReverse[keyLeafValue] = j

					if keyLeafValue < 627:
						self.dynHaffmanTreeReverse[keyLeafValue + 1] = j

					replaceLeafValue = self.dynHaffmanTreeMain[j]
					self.dynHaffmanTreeMain[j] = keyLeafValue
					self.dynHaffmanTreeReverse[replaceLeafValue] = i

					if replaceLeafValue < 627:
						self.dynHaffmanTreeReverse[replaceLeafValue + 1] = i

					self.dynHaffmanTreeMain[i] = replaceLeafValue

					i = j

				i = self.dynHaffmanTreeReverse[i]

				if i == 0: break

		def getBitsFromStream(self, bitsize = 1):
			while self.loadedBitsCount <= 8:
				byte = self.getNextByte()

				self.bitsArray |= byte << (8 - self.loadedBitsCount)
				self.loadedBitsCount += 8

			tmpBits = self.bitsArray
			self.bitsArray = (self.bitsArray << bitsize) & 0xFFFF
			self.loadedBitsCount -= bitsize

			return tmpBits >> (16 - bitsize)

		def getNextByte(self):
			if len(self.dataToDecode) == 0: return 0
			else: return self.dataToDecode.pop(0)

	return ComplexLZ77BasedCompressedImage(data).getUnpackedData()
