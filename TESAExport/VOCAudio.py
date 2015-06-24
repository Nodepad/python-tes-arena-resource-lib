
import struct, wave, math

class VOCAudio:

	class Error(Exception): pass

	InvalidFileHeaderExceptionMessage = "VOC header is invalid"
	InvalidFileFormatExceptionMessage = "File format is invalid"
	EndlessAudioFileExceptionMessage = "This audio file is endless"
	MarkerChunkExceptionMessage = "This file contains marker chunk"
	TextChunkExceptionMessage = "This file contains text chunk"

	VOCIdentifierString = "Creative Voice File\x1A"
	VOCIdentifierStringLen = len(VOCIdentifierString)
	VOCMainHeaderSize = 6
	VOCChunkHeaderSize = 4
	VOCDataChunkHeaderSize = 2

	def __dataChunkHandler(self, chunkData):
		frequencyDivisor, codecId = struct.unpack("<BB", str(chunkData[:self.VOCDataChunkHeaderSize]))
		sampleRate = 1000000 / (0x100 - frequencyDivisor)
		self.lastDataSampleRate, self.lastDataCodecId = (sampleRate, codecId)
		pcm = self.__convertPCMSamples(chunkData[self.VOCDataChunkHeaderSize:], sampleRate, codecId)
		self.unpackedPCM.extend(self.repeated and pcm * self.repeatCount or pcm)

	def __dataContinuationChunkHandler(self, chunkData):
		pcm = self.__convertPCMSamples(chunkData, self.lastDataSampleRate, self.lastDataCodecId)
		self.unpackedPCM.extend(self.repeated and pcm * self.repeatCount or pcm)

	def __silenceChunkHandler(self, chunkData):
		silenceLength, frequencyDivisor = struct.unpack("<HB", str(chunkData))
		sampleRate = 1000000 / (0x100 - frequencyDivisor)

	def __markerChunkHandler(self, chunkData):
		raise self.Error(self.MarkerChunkExceptionMessage)
	def __textChunkHandler(self, chunkData):
		raise self.Error(self.TextChunkExceptionMessage, str(chunkData))

	def __repeatStartChunkHandler(self, chunkData):
		repeated = True
		repeatCount = struct.unpack("<H", str(chunkData))[0]
		if (repeatCount == 0xFFFF):
			raise self.Error(self.EndlessAudioFileExceptionMessage)
		self.repeated = repeated
		self.repeatCount = repeatCount + 1

	def __repeatEndChunkHandler(self, chunkData = None):
		self.repeated = False

	chunkHandlers = {	0x01 : __dataChunkHandler,
						0x02 : __dataContinuationChunkHandler,
						0x03 : __silenceChunkHandler,
						0x04 : __markerChunkHandler,
						0x05 : __textChunkHandler,
						0x06 : __repeatStartChunkHandler,
						0x07 : __repeatEndChunkHandler}

	def __validateVOCHeader(self):

		if (self.data[:self.VOCIdentifierStringLen] != self.VOCIdentifierString): return False
		self.headerSize, versionNumber, validityCheck = struct.unpack("<HHH", self.data[self.VOCIdentifierStringLen:self.VOCIdentifierStringLen + self.VOCMainHeaderSize])
		if (0x1234 + ~versionNumber != validityCheck): return False

		return True

	def __convertPCMSamples(self, data, dataSampleRate, dataCodecId):
		audioDivisor = dataSampleRate / float(self.exportSampleRate)
		restoredPCM = []

		audioPointer = 0.0

		while audioPointer < len(data) - 1:
			leftPCMIndex = int(math.floor(audioPointer))
			rightPCMFactor = audioPointer - leftPCMIndex

			leftPCM = data[leftPCMIndex]
			rightPCM = data[leftPCMIndex + 1]
			middlePCM = leftPCM * (1.0 - rightPCMFactor) + rightPCM * rightPCMFactor

			finalPCM = int(round((middlePCM - 128.0) * 128.0))

			restoredPCM.append(finalPCM)

			audioPointer += audioDivisor
		
		return restoredPCM

	def __extractPCMData(self):
		
		dataToExtract = bytearray(self.data[self.headerSize:])
		self.unpackedPCM = []

		while len(dataToExtract) > 0:
			chunkType = struct.unpack("<B", str(dataToExtract[:1]))[0]

			if chunkType == 0x00: break

			chunkSize, chunkSizeUpper = struct.unpack("<HB", str(dataToExtract[1:self.VOCChunkHeaderSize]))
			chunkSize = chunkSizeUpper << 16 | chunkSize
			del dataToExtract[:self.VOCChunkHeaderSize]

			self.chunkHandlers[chunkType](self, dataToExtract[:chunkSize])
			del dataToExtract[:chunkSize]

	def __init__(self, filename):
		self.data = open(filename, "rb").read()
		if not self.__validateVOCHeader(): raise self.Error, self.InvalidFileHeaderExceptionMessage

	def exportPCMFrames(self, exportSampleRate):
		self.exportSampleRate = exportSampleRate
		self.repeated = False

		self.__extractPCMData()

		return "".join([struct.pack("<h", pcm) for pcm in self.unpackedPCM])

	def exportWaveFile(self, waveFilename, exportSampleRate):
		wav = wave.open(waveFilename, "wb")
		wav.setnchannels(1)
		wav.setsampwidth(2)
		wav.setframerate(exportSampleRate)
		wav.writeframes(self.exportPCMFrames(exportSampleRate))
		wav.close()

class VOCAudioSequence:

	def __init__(self, filenames):
		self.audioFiles = [VOCAudio(audioFilename) for audioFilename in filenames]

	def exportPCMFrames(self, exportSampleRate):
		return "".join([audioFile.exportPCMFrames(exportSampleRate) for audioFile in self.audioFiles])

	def exportWaveFile(self, waveFilename, exportSampleRate):
		wav = wave.open(waveFilename, "wb")
		wav.setnchannels(1)
		wav.setsampwidth(2)
		wav.setframerate(exportSampleRate)
		wav.writeframes(self.exportPCMFrames(exportSampleRate))
		wav.close()