import os, struct
from .Error import *
from .Palette import Palette
from .ArenaImage import *
from .ResourceDatabase import ResourceDatabase

TESA_IMG_FILE_TYPE = "IMG"
TESA_CIF_FILE_TYPE = "CIF"

class CIFIMGInvalidOriginalNameException (Exception):
	def __init__(self, originalFilename):
		super(CIFIMGInvalidOriginalNameException, self).__init__(
		"Can't find original filename (%s) in resource database" % originalFilename
		)
class CIFIMGInvalidHeaderException (Exception):
	def __init__(self, filename):
		super(CIFIMGInvalidHeaderException, self).__init__(
		"IMG header in file %s is invalid" % filename
		)
class CIFIMGInvalidImageSize (Exception):
	def __init__(self, newWidth, newHeight, width, height):
		super(CIFIMGInvalidImageSize, self).__init__(
		"Old and new image sizes aren't the same: new:(%d, %d), old:(%d, %d)" % (newWidth, newHeight, width, height)
		)

class CIFIMGImage:

	@staticmethod
	def fromRGBAImages(images, originalFilename, palette = None, forceAlpha = None):

		resDb = ResourceDatabase()
		fileDescription = resDb.findFile(originalFilename)

		if fileDescription == None:
			raise CIFIMGInvalidOriginalNameException(originalFilename)

		if 'type' in fileDescription:
			imagetype = fileDescription['type']

		if 'rect' in fileDescription:
			x, y, width, height = fileDescription['rect']

		if palette == None:
			palette = fileDescription['palette']

		if forceAlpha == None:
			forceAlpha = fileDescription['alpha']

		noHeader = 'noHeader' in fileDescription and fileDescription['noHeader'] or False

		imageMap = 'map' in fileDescription and fileDescription['map'] or None

		aImages = []

		for i in xrange(len(images)):
			image = images[i]

			if 'images' in fileDescription:
				imageDescription = fileDescription['images'][i]

				x, y, width, height = imageDescription['rect']

				imagetype = imageDescription['type']

			newWidth, newHeight = image.size

			if noHeader and (width != newWidth or height != newHeight):
				raise CIFIMGInvalidImageSize(newWidth, newHeight, width, height)

			if imagetype & TESA_IMAGE_TYPE_DEFLATE:
				imagetype &= 0xFFF0
				imagetype |= TESA_IMAGE_TYPE_RLE

			aImage = ArenaImage.fromRGBAImage(image, palette, x, y, imagetype, forceAlpha, noHeader)

			aImages.append(aImage)

		fileType = os.path.splitext(originalFilename)[1].upper()[1:]

		return CIFIMGImage(originalFilename, fileType, aImages, forceAlpha, imageMap)

	@staticmethod
	def fromOriginalFile(filename, palette = None, forceAlpha = None):

		originalFilename = os.path.split(filename)[1]
		fileext = os.path.splitext(filename)[1].upper()[1:]

		if not (fileext == TESA_IMG_FILE_TYPE or fileext == TESA_CIF_FILE_TYPE):
			raise Error(WrongFileExtensionErrorMessage)

		fileType = fileext

		resDb = ResourceDatabase()
		fileDescription = resDb.findFile(originalFilename)

		if palette == None:
			palette = fileDescription['palette']

		if forceAlpha == None:
			forceAlpha = fileDescription['alpha']

		if 'noHeader' in fileDescription:
			noHeader = fileDescription['noHeader']
		else:
			noHeader = False

		images = []

		data = bytearray(open(filename, "rb").read())
		dataSize = len(data)

		while dataSize > 0:
			if not noHeader:
				x, y, width, height, imagetype, size = struct.unpack("<HHHHHH", str(data[:TESA_IMAGE_HEADER_SIZE]))

				if not ArenaImage.isHeaderValid(x, y, width, height, imagetype, size):
					raise CIFIMGInvalidHeaderException(filename)

				fullImageSize = TESA_IMAGE_HEADER_SIZE + size
				nextImagePointer = fullImageSize

				if imagetype & TESA_IMAGE_WITH_FULL_PALETTE:
					palette = Palette.fromData(data[fullImageSize:fullImageSize + TESA_IMAGE_PALLETE_SIZE])
					nextImagePointer += TESA_IMAGE_PALLETE_SIZE

				image = ArenaImage.fromData(data[TESA_IMAGE_HEADER_SIZE:fullImageSize], palette, width, height, x, y, imagetype, forceAlpha, noHeader)
				images.append(image)
			else:
				x, y, width, height = fileDescription['rect']
				imagetype = fileDescription['type']
				image = ArenaImage.fromData(data, palette, width, height, x, y, imagetype, forceAlpha, noHeader)
				images.append(image)

				break


			data = data[nextImagePointer:]
			dataSize = len(data)

		return CIFIMGImage(filename, fileType, images, forceAlpha, None)

	def __init__(self, name, fileType, images, forceAlpha, imageMap):

		self.name = name
		self.fileType = fileType
		self.images = images
		self.forceAlpha = forceAlpha
		self.imageMap = imageMap

	def getImages(self):
		return self.images

	def getRGBAImages(self):
		return [image.getRGBAImage() for image in self.images]

	def saveOriginalFile(self, filename):

		file = open(filename, "wb");

		for image in self.images:

			if image.noHeader:
				file.write(image.getData())
			else:
				data = image.getCompressedData()

				x, y = image.position
				width, height = image.size
				imagetype = image.imageType
				size = len(data)

				header = struct.pack("<HHHHHH", x, y, width, height, imagetype, size)

				file.write(header)
				file.write(data)

				if imagetype & TESA_IMAGE_WITH_FULL_PALETTE:
					file.write(image.palette.data6bit())

		if self.imageMap:
			file.write(self.imageMap)

		file.close()

#remove in future
class IMGImage:

	@staticmethod
	def fromRGBAImage(image, originalFilename):
		x, y, width, height = imageDescription["rect"]
		imagetype = imageDescription["type"]
		palette = imageDescription["palette"]
		forceAlpha = imageDescription["alpha"]
		x, y, width, height = int(x), int(y), int(width), int(height)

		print palette

		newWidth, newHeight = image.size

		if width != newWidth or height != newHeight:
			raise IMGInvalidImageSize, "Old and new image sizes aren't the same: new:(%d, %d), old:(%d, %d)" % (newWidth, newHeight, width, height)

		image = ArenaImage.fromRGBAImage(image, palette, width, height, x, y, imagetype, forceAlpha)

	@staticmethod
	def fromOriginalFile(filename, palette, forceAlpha = False):
		fileext = os.path.splitext(filename)[1].upper()
		if fileext != TESA_IMG_FILE_EXTENSION: raise Error, WrongFileExtensionErrorMessage

		data = bytearray(open(filename, "rb").read())

		x, y, width, height, imagetype, size = struct.unpack("<HHHHHH", str(data[:TESA_IMAGE_HEADER_SIZE]))

		if not ArenaImage.isHeaderValid(x, y, width, height, imagetype, size):
			raise IMGInvalidHeaderException, "IMG header in file %s is invalid" % filename

		fullImageSize = TESA_IMAGE_HEADER_SIZE + size

		if imagetype & TESA_IMAGE_WITH_FULL_PALETTE:
			palette = Palette(data[fullImageSize:fullImageSize + TESA_IMAGE_PALLETE_SIZE])
			palette.internal = True

		return IMGImage(ArenaImage.fromData(data[TESA_IMAGE_HEADER_SIZE:fullImageSize], palette, width, height, x, y, imagetype, forceAlpha))

	def __init__(self, image):
		self.image = image

	def getRGBAImage(self):
		return self.image.getRGBAImage()

	def saveOriginalFile(self, filename):
		data = self.image.getOriginalData()

		x = self.image.x
		y = self.image.y
		width, height = self.image.size
		imagetype = self.image.imageType
		size = len(data)

		header = struct.pack("<HHHHHH", x, y, width, height, imageType, size);

		file = open(filename, "wb");

		file.write(header);
		file.write(data);
		file.close();
