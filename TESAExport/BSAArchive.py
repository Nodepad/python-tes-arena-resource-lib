import sys, os, struct

def cryptTextFileData(data):
	cryptPass = [0xEA, 0x7B, 0x4E, 0xBD, 0x19, 0xC9, 0x38, 0x99]
	charIndex = 0
	cryptIndex = 0
	dataIndex = 0

	cryptData = []

	while dataIndex < len(data):
		symbol = struct.unpack("<B", data[dataIndex])[0]
		symbol = symbol ^ (charIndex + cryptPass[cryptIndex])
		symbol &= 0xFF
		cryptData.append(symbol)
		dataIndex += 1
		cryptIndex = (cryptIndex + 1) & 0x07
		charIndex = (charIndex + 1) & 0xFF

	return "".join([struct.pack("<B", symbol) for symbol in cryptData])

class BSAArchive:

	def __init__(self, filename):

		archiveFile = open(filename, "rb")
		archiveData = archiveFile.read()

		fileEntriesCount = struct.unpack("<H", archiveData[:2])[0]

		fileTableLength = fileEntriesCount * 18

		fileTable = archiveData[-fileTableLength:]

		archiveOffset = 2

		files = {}

		for fileEntryIndex in xrange(fileEntriesCount):
			fileEntryOffset = fileEntryIndex * 18
			fileTableEntry = fileTable[fileEntryOffset:fileEntryOffset + 18]
			fileName = fileTableEntry[:14].replace('\x00', '')
			fileSize = struct.unpack("<I", fileTableEntry[14:])[0]
			fileData = archiveData[archiveOffset:archiveOffset + fileSize]
			archiveOffset += fileSize

			files[fileName] = fileData

		self.archiveFiles = files

	def exportFile(self, filename, exportFilename):
		exportData = self.exportFileData(filename)

		if exportData != None:
			exportFile = open(exportFilename, "wb")
			exportFile.write(exportData)
			exportFile.close()

	def exportFileData(self, filename):
		if filename in self.archiveFiles.keys():
			fileExtension = os.path.splitext(filename)[1]
			if fileExtension == ".TXT" or fileExtension == ".INF":
				return cryptTextFileData(self.archiveFiles[filename])
			return self.archiveFiles[filename]

	def getFilenamesWithExtension(self, extension):
		result = []

		for filename in self.archiveFiles.keys():
			if os.path.splitext(filename)[1] == extension:
				result.append(filename)

		return result