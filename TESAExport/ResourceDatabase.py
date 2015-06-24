from xml.dom.minidom import parse
import base64, os
from string import split
from .Palette import Palette

class ResourceDatabase:
    def __init__(self):
        basepath = os.path.dirname(__file__)
        doc = parse(os.path.join(basepath, "db.xml"))
        xDatabase = doc.documentElement
        assert xDatabase.tagName == "database"

        self.__loadExternalPalettes(xDatabase)
        self.__loadImages(xDatabase)
        self.__loadCIFs(xDatabase)

    def __loadExternalPalettes(self, xDatabase):
        extPals = xDatabase.getElementsByTagName("external_palette")
        externalPalettes = []

        for xExternalPalette in extPals:
            name = xExternalPalette.getAttribute("name")

            paletteDataString = xExternalPalette.firstChild.nodeValue
            paletteData = base64.b64decode(paletteDataString)
            palette = Palette.fromRawData(paletteData)

            externalPalette = { "name" : name,
                                "palette" : palette}

            externalPalettes.append(externalPalette)

        self.externalPalettes = externalPalettes

    def __loadImage(self, xImg):
        name = xImg.getAttribute("name")

        noHeaderString = xImg.getAttribute("no-header")
        noHeader = noHeaderString.lower() == "true" and True or False

        rectString = xImg.getElementsByTagName("rect")[0].firstChild.nodeValue
        rect = split(rectString, ",")
        rect = [int(entry) for entry in rect]

        xPalette = xImg.getElementsByTagName("palette")[0]
        paletteName = xPalette.getAttribute("name")

        if paletteName != "":
            palette = self.findExternalPalette(paletteName)
        else:
            paletteDataString = xPalette.firstChild.nodeValue
            paletteData = base64.b64decode(paletteDataString)
            palette = Palette.fromRawData(paletteData)

        xMaps = xImg.getElementsByTagName("map")
        mapData = None

        if len(xMaps) > 0:
            xMap = xMaps[0]

            mapDataString = xMap.firstChild.nodeValue
            mapData = base64.b64decode(mapDataString)

        imageTypeString = xImg.getElementsByTagName("type")[0].firstChild.nodeValue
        imageType = int(imageTypeString, 0)

        alphaString = xImg.getElementsByTagName("alpha")[0].firstChild.nodeValue
        forceAlpha = alphaString.lower() == "true" and True or False

        image = {   "name"      : name,
                    "noHeader"  : noHeader,
                    "rect"      : rect,
                    "palette"   : palette,
                    "type"      : imageType,
                    "alpha"     : forceAlpha}

        if mapData:
            image["map"] = mapData

        return image

    def __loadImages(self, xDatabase):
        imgs = xDatabase.getElementsByTagName("img")
        images = []

        for xImg in imgs:
            images.append(self.__loadImage(xImg))

        mnus = xDatabase.getElementsByTagName("mnu")
        mnuDescriptions = []

        for xMnu in mnus:
            mnuDescriptions.append(self.__loadImage(xMnu))

        self.images = images
        self.mnus = mnuDescriptions

    def __loadCIFs(self, xDatabase):
        xCifs = xDatabase.getElementsByTagName("cif")
        cifs = []

        for xCif in xCifs:
            name = xCif.getAttribute("name")

            images = []

            for xImage in xCif.getElementsByTagName("image"):
                rectString = xImage.getElementsByTagName("rect")[0].firstChild.nodeValue
                rect = split(rectString, ",")
                imageTypeString = xImage.getElementsByTagName("type")[0].firstChild.nodeValue
                imageType = int(imageTypeString, 0)

                image = {   "rect"  : rect,
                            "type"  : imageType}

                images.append(image)

            xPalette = xCif.getElementsByTagName("palette")[0]
            paletteName = xPalette.getAttribute("name")

            if paletteName != "":
                palette = self.findExternalPalette(paletteName)
            else:
                paletteDataString = xPalette.firstChild.nodeValue
                paletteData = base64.b64decode(paletteDataString)
                palette = Palette.fromRawData(paletteData)

            alphaString = xCif.getElementsByTagName("alpha")[0].firstChild.nodeValue
            forceAlpha = alphaString.lower() == "true" and True or False

            cif = { "name"      : name,
                    "images"    : images,
                    "palette"   : palette,
                    "alpha"     : forceAlpha}

            cifs.append(cif)

        self.cifs = cifs

    def findExternalPalette(self, name):
        for externalPaletteDescription in self.externalPalettes:
            if externalPaletteDescription["name"] == name:
                return externalPaletteDescription["palette"]

        return None

    def findFile(self, filename):

        fileext = os.path.splitext(filename)[1].upper()[1:]

        if fileext == "IMG":
            for imageDescription in self.images:
                if imageDescription["name"] == filename:
                    return imageDescription
        elif fileext == "CIF":
            for cifDescription in self.cifs:
                if cifDescription["name"] == filename:
                    return cifDescription
        elif fileext == "MNU":
            for mnuDescription in self.mnus:
                if mnuDescription["name"] == filename:
                    return mnuDescription
