import struct, codecs, re

from TESAExe import translation, reverseTable, mergedTable, standardTable

def createTemplatePointersData(templateFilename):
	textFile = open(templateFilename, "rb")
	textData = textFile.read()

	textFile.close()

	tokenData = []
	pointerData = []

	index = textData.find('#')
	while index != -1:
		tokenIndex = int(textData[index + 1:index + 5])
		tokenChar = textData[index + 5]
		if tokenChar.isalpha():
			tokenChar = bytearray(tokenChar)[0] - 0x61
			tokenIndex |= 0x8000 | (tokenChar << 8)
		tokenData.append(tokenIndex)
		pointerData.append(index + 1)

		index = textData.find('#', index + 1)

	tokensString = "".join([struct.pack("<H", token) for token in tokenData]).ljust(0x2710, '\x00')
	pointersString = "".join([struct.pack("<I", pointer) for pointer in pointerData]).ljust(0x2710, '\x00')

	return tokensString + pointersString

def unpackNameChnkFile(filename, localeFilename):
	file = open(filename, "rb")
	fileData = file.read()

	result = []

	while len(fileData) > 0:
		chunkSize, count = struct.unpack("<HB", fileData[:3])
		stringsData = fileData[3:chunkSize]
		fileData = fileData[chunkSize:]

		translate = translation(reverseTable(standardTable()))
		strings = translate(stringsData).split("\\x00")
		result.append(strings)

	localeFile = open(localeFilename, "wb")

	for strings in result:
		localeFile.write(",".join(strings)[:-1] + "\n")

	localeFile.close()

def packNameChnkFile(localeFilename, filename, localeTable):
	file = codecs.open(localeFilename, "r", "utf-8")
	fileData = file.read()

	result = []
	translate = translation(mergedTable(standardTable(), localeTable))

	for line in fileData.split("\n"):
		if len(line.strip()) > 0:
			newLine = line.replace(",", "\\x00") + "\\x00"
			result.append(translate(newLine))

	file = open(filename, "wb")

	for line in result:
		header = struct.pack("<HB", len(line) + 3, line.count("\x00"))
		file.write(header + line)

	file.close()

def unpackStringsFile(filename, localeFilename):
	file = open(filename, "rb")
	fileData = file.read()

	result = []

	for string in fileData.split("\x00"):
		translate = translation(reverseTable(standardTable()))
		localeString = translate(string)
		result.append(localeString)

	localeFile = open(localeFilename, "wb")
	localeFile.write("=======\n" + "\n=======\n".join(result))
	localeFile.close()

def packStringsFile(localeFilename, filename, localeTable):
	file = codecs.open(localeFilename, "r", "utf-8")
	fileData = file.read()

	regex = re.compile("={2}=*")

	strings = []
	start = 0

	for match in regex.finditer(fileData):
		data = fileData[start:match.start()]

		if len(data) > 0:
			strings.append(data)

		start = match.end()

	result = []
	translate = translation(mergedTable(standardTable(), localeTable))

	for string in [string.replace("\r\n", "\n") for string in strings]:
		result.append("\r".join([translate(line) for line in string.split("\n") if len(line) > 0]))

	file = open(filename, "wb")
	file.write("\x00".join(result) + "\x00")
	file.close()
