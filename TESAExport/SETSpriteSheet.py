import os
from .Palette import *
from .Error import *

TESA_SET_FILE_EXTENSION = ".SET"
TESA_SET_SPRITE_SIZE = 64

TESA_SET_SPRITE_IMAGE_SIZE = TESA_SET_SPRITE_SIZE * TESA_SET_SPRITE_SIZE

class SETSpriteSheet:

	def __init__(self, filename, palette):

		fileext = os.path.splitext(filename)[1].upper()
		if fileext != TESA_SET_FILE_EXTENSION:
			raise Error(WrongFileExtensionErrorMessage)

		data = bytearray(open(filename, "rb").read())

		if len(data) % TESA_SET_SPRITE_SIZE != 0:
			raise Error(WrongSpriteSizeErrorMessage)

		self.images = []

		for i in xrange(len(data) / TESA_SET_SPRITE_SIZE):
			sprite = Image.new("P", (TESA_SET_SPRITE_SIZE, TESA_SET_SPRITE_SIZE))
			sprite.putpalette(palette.data())
			sprite.putdata(data[TESA_SET_SPRITE_IMAGE_SIZE * i: TESA_SET_SPRITE_IMAGE_SIZE * (i + 1)])
			self.images.append(sprite)

	def getRGBAImages(self):
		return [image.convert("RGBA") for image in self.images]