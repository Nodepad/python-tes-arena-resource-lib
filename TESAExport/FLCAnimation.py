import os, struct, ctypes
from PIL import Image
# from .Error import *
from Error import *

FLC_FILE_EXTENSION = ".FLC"

class FLCObject:
	def __init__(self):
		self.parent = None
		self.setPaletteData(None)
	def getPaletteData(self):
		return self.paletteData
	def setPaletteData(self, data):
		self.paletteData = data

def __CEL_DATA_Handler(data, parent):
	print "__CEL_DATA_Handler"
	pass
def __COLOR_256_Handler(data, parent):
	print "__COLOR_256_Handler"
	del data[:6]
	parent.setPaletteData(unpackPalette(data, parent.getPaletteData(), 8))

def __DELTA_FLC_Handler(data, parent):
	print "__DELTA_FLC_Handler"
	del data[:6]
	frame = parent.getPreviousFrame().getImageData()[:]
	width = parent.width
	numberOfLines = struct.unpack("<H", str(data[:2]))[0]
	del data[:2]

	lineIndex = 0

	for i in xrange(numberOfLines):
		columnIndex = 0
		packetCountForLine, lastPixelOfLine, lineSkipCount = 0, 0, 0
		while True:
			opcode = struct.unpack("<h", str(data[:2]))[0]
			del data[:2]
			optype = (opcode & 0xC000) >> 14

			if optype == 0:
				packetCountForLine = opcode
				break
			if optype == 2:
				lastPixelOfLine = opcode & 0xFF
			if optype == 3:
				lineSkipCount = abs(opcode)

		lineIndex += lineSkipCount

		for j in xrange(packetCountForLine):
			skip, count = struct.unpack("<Bb", str(data[:2]))
			del data[:2]

			columnIndex += skip
			# dataStartPointer = lineIndex * width + columnIndex
			# dataEndPointer = dataStartPointer + count * 2

			if count < 0:
				count = abs(count)
				# frame[dataStartPointer:dataEndPointer] = list(data[:2]) * count
				packetData = list(data[:2]) * count
				del data[:2]
			else:
				# frame[dataStartPointer:dataEndPointer] = data[:count * 2]
				packetData = data[:count * 2]
				del data[:count * 2]

			dataStartPointer = lineIndex * width + columnIndex
			dataEndPointer = dataStartPointer + count * 2

			frame[dataStartPointer:dataEndPointer] = packetData

			columnIndex += count * 2

		lineIndex += 1

	parent.setImageData(frame)

def __COLOR_64_Handler(data, parent):
	print "__COLOR_64_Handler"
	del data[:6]
	parent.setPaletteData(unpackPalette(data, parent.getPaletteData(), 6))

def __DELTA_FLI_Handler(data, parent):
	print "__DELTA_FLI_Handler"
	pass

def __BLACK_Handler(data, parent):
	print "__BLACK_Handler"
	parent.setImageData([0] * (parent.width * parent.height))

def __BYTE_RUN_Handler(data, parent):
	print "__BYTE_RUN_Handler"
	del data[:6]
	frame = []
	width, height = parent.width, parent.height
	for i in xrange(height):
		leftDataToUnpack = width
		del data[0]

		while leftDataToUnpack > 0:
			count = data[0]
			del data[0]
			if count & 0x80:
				count = abs(ctypes.c_byte(count).value)
				frame.extend(data[:count])
				del data[:count]
			else:
				value = data[0]
				del data[0]
				frame.extend([value] * count)

			leftDataToUnpack -= count

	parent.setImageData(frame)

def __FLI_COPY_Handler(data, parent):
	print "__FLI_COPY_Handler"
	del data[:6]
	parent.setImageData(data[:parent.width * parent.height])

def __PSTAMP_Handler(data, parent):
	print "__PSTAMP_Handler"
	pass
def __DTA_BRUN_Handler(data, parent):
	print "__DTA_BRUN_Handler"
	pass
def __DTA_COPY_Handler(data, parent):
	print "__DTA_COPY_Handler"
	pass
def __DTA_LC_Handler(data, parent):
	print "__DTA_LC_Handler"
	pass
def __LABEL_Handler(data, parent):
	print "__LABEL_Handler"
	pass
def __BMP_MASK_Handler(data, parent):
	print "__BMP_MASK_Handler"
	pass
def __MLEV_MASK_Handler(data, parent):
	print "__MLEV_MASK_Handler"
	pass
def __SEGMENT_Handler(data, parent):
	print "__SEGMENT_Handler"
	pass
def __KEY_IMAGE_Handler(data, parent):
	print "__KEY_IMAGE_Handler"
	pass
def __KEY_PAL_Handler(data, parent):
	print "__KEY_PAL_Handler"
	del data[:6]
	parent.setPaletteData(unpackPalette(data, None, 8))

def __REGION_Handler(data, parent):
	print "__REGION_Handler"
	pass
def __WAVE_Handler(data, parent):
	print "__WAVE_Handler"
	pass
def __USERSTRING_Handler(data, parent):
	print "__USERSTRING_Handler"
	pass
def __RGN_MASK_Handler(data, parent):
	print "__RGN_MASK_Handler"
	pass
def __LABELEX_Handler(data, parent):
	print "__LABELEX_Handler"
	pass
def __SHIFT_Handler(data, parent):
	print "__SHIFT_Handler"
	pass
def __PATHMAP_Handler(data, parent):
	print "__PATHMAP_Handler"
	pass
def __PREFIX_TYPE_Handler(data, parent):
	print "__PREFIX_TYPE_Handler"
	parent.prefix = FLCPrefix(data, parent)
	pass
def __SCRIPT_CHUNK_Handler(data, parent):
	print "__SCRIPT_CHUNK_Handler"
	pass
def __FRAME_TYPE_Handler(data, parent):
	print "__FRAME_TYPE_Handler"
	# self.width, self.height = struct.unpack("<HH", str(data[12:16]))
	# print "%d = %d" % (self.width, self.height)
	parent.appendFrame(FLCFrame(data, parent))
	# del data[:16]
	# while len(data) > 0:
	# 	self.__unpackChunk(data)
	pass
def __SEGMENT_TABLE_Handler(data, parent):
	print "__SEGMENT_TABLE_Handler"
	pass
def __HUFFMAN_TABLE_Handler(data, parent):
	print "__HUFFMAN_TABLE_Handler"
	pass

chunkHandlers = {	3 		: __CEL_DATA_Handler,
					4 		: __COLOR_256_Handler,
					7 		: __DELTA_FLC_Handler,
					11 		: __COLOR_64_Handler,
					12 		: __DELTA_FLI_Handler,
					13 		: __BLACK_Handler,
					15 		: __BYTE_RUN_Handler,
					16 		: __FLI_COPY_Handler,
					18 		: __PSTAMP_Handler,
					25 		: __DTA_BRUN_Handler,
					26 		: __DTA_COPY_Handler,
					27 		: __DTA_LC_Handler,
					31 		: __LABEL_Handler,
					32 		: __BMP_MASK_Handler,
					33 		: __MLEV_MASK_Handler,
					34 		: __SEGMENT_Handler,
					35 		: __KEY_IMAGE_Handler,
					36 		: __KEY_PAL_Handler,
					37 		: __REGION_Handler,
					38 		: __WAVE_Handler,
					39 		: __USERSTRING_Handler,
					40 		: __RGN_MASK_Handler,
					41 		: __LABELEX_Handler,
					42 		: __SHIFT_Handler,
					43 		: __PATHMAP_Handler,
					0xF100 	: __PREFIX_TYPE_Handler,
					0xF1E0 	: __SCRIPT_CHUNK_Handler,
					0xF1FA 	: __FRAME_TYPE_Handler,
					0xF1FB 	: __SEGMENT_TABLE_Handler,
					0xF1FC 	: __HUFFMAN_TABLE_Handler}

def unpackChunk(data, parent):
	chunkSize, chunkType = struct.unpack("<IH", str(data[:6]))

	if chunkSize % 2 != 0: chunkSize += 1

	if not chunkType in chunkHandlers:
		raise Error, WrongFLCFileFormat

	chunkHandlers[chunkType](data[:chunkSize], parent)

	del data[:chunkSize]

def unpackPalette(data, currentPalette = None, bitsize = 8):
	palette = currentPalette
	if palette == None or len(palette) != 768:
		palette = [0, 0, 0] * 256

	packetsCount = struct.unpack("<H", str(data[:2]))[0]
	del data[:2]

	paletteIndex = 0

	for i in xrange(packetsCount):
		skip, count = struct.unpack("<BB", str(data[:2]))
		del data[:2]

		if count == 0: count = 256
		paletteIndex += skip

		palettePacketSize = count * 3
		palettePacketOffset = paletteIndex * 3
		palettePacket = data[:palettePacketSize]
		if (bitsize < 8): palettePacket = [color << (8 - bitsize) for color in palettePacket]
		palette[palettePacketOffset:palettePacketOffset + palettePacketSize] = palettePacket
		del data[:palettePacketSize]

	return palette

class FLCPrefix(FLCObject):

	def __init__(self, data, parent):
		self.parent = parent
		self.chunks = struct.unpack("<H", str(data[6:8]))[0]
		del data[:16]

class FLCFrame(FLCObject):

	def getPaletteData(self):
		if self.paletteData != None: return self.paletteData
		return self.parent.getPaletteData()
	def setPaletteData(self, data):
		FLCObject.setPaletteData(self, data)
		if self.parent != None: self.parent.setPaletteData(data)

	def __init__(self, data, parent):
		FLCObject.__init__(self)
		self.setImageData(None)
		self.setPaletteData(parent.getPaletteData())

		self.parent = parent
		self.chunks, self.delay = struct.unpack("<HH", str(data[6:10]))
		self.width, self.height = struct.unpack("<HH", str(data[12:16]))
		if self.delay == 0: self.delay = parent.delay
		if self.width == 0: self.width = parent.width
		if self.height == 0: self.height = parent.height
		del data[:16]
		for i in xrange(self.chunks):
			unpackChunk(data, self)

	def getPreviousFrame(self):
		return self.parent.getLastFrame()
	def getImageData(self):
		return self.imageData
	def setImageData(self, data):
		self.imageData = data

	def exportImage(self):
		image = Image.new("P", (self.width, self.height))
		image.putpalette(self.getPaletteData())
		image.putdata(self.getImageData())
		return image.convert("RGBA")

class FLCAnimation(FLCObject):

	def __init__(self, data):
		FLCObject.__init__(self)

		self.exportedImages = None
		self.frames = []

		self.delay = 0
		data = bytearray(data)

		self.__parseHeader(data[:128])
		del data[:128]

		while len(data) > 0:
			unpackChunk(data, self)

	def __parseHeader(self, data):
		self.width, self.height = struct.unpack("<HH", str(data[8:12]))
		pass

	def getLastFrame(self):
		return self.frames[-1]
	def appendFrame(self, frame):
		self.frames.append(frame)

	def exportImages(self):
		if self.exportedImages == None:
			self.exportedImages = [frame.exportImage() for frame in self.frames]
		return self.exportedImages

	def exportFinishPaletteData(self):
		return self.paletteData

if __name__ == "__main__":
	# vision = FLCAnimation(open("END01.FLC", "rb").read())
	scroll = FLCAnimation(open("SCROLL.FLC", "rb").read())

	i = 0
	for image in scroll.exportImages():
		image.save("ares_intro_scroll_%2.2d.png" % i)
		i += 1
