# 2013.08.22 22:20:17 Pacific Daylight Time
# Embedded file name: toontown.estate.FlowerCollection
import GardenGlobals
from direct.directnotify import DirectNotifyGlobal
import FlowerBase

class FlowerCollection():
    __module__ = __name__
    notify = DirectNotifyGlobal.directNotify.newCategory('FlowerCollection')

    def __init__(self):
        self.flowerlist = []

    def __len__(self):
        return len(self.flowerlist)

    def getFlower(self):
        return self.flowerlist

    def makeFromNetLists(self, speciesList, varietyList):
        self.flowerlist = []
        for species, variety in zip(speciesList, varietyList):
            self.flowerlist.append(FlowerBase.FlowerBase(species, variety))

    def getNetLists(self):
        speciesList = []
        varietyList = []
        for flower in self.flowerlist:
            speciesList.append(flower.getSpecies())
            varietyList.append(flower.getVariety())

        return [speciesList, varietyList]

    def hasFlower(self, species, variety):
        for flower in self.flowerlist:
            if flower.getSpecies() == species and flower.getVariety() == variety:
                return 1

        return 0

    def hasSpecies(self, species):
        for flower in self.flowerlist:
            if flower.getSpecies() == species:
                return 1

        return 0

    def getInitialVariety(self, species):
        retVal = 100000
        for flower in self.flowerlist:
            if flower.getSpecies() == species:
                if flower.getVariety() < retVal:
                    retVal = flower.getVariety()

        if retVal == 100000:
            retVal = 0
        return retVal

    def __collect(self, newFlower, updateCollection):
        for flower in self.flowerlist:
            if flower.getVariety() == newFlower.getVariety() and flower.getSpecies() == newFlower.getSpecies():
                return GardenGlobals.COLLECT_NO_UPDATE

        if updateCollection:
            self.flowerlist.append(newFlower)
        return GardenGlobals.COLLECT_NEW_ENTRY

    def collectFlower(self, newFlower):
        return self.__collect(newFlower, updateCollection=1)

    def __str__(self):
        numFlower = len(self.flowerlist)
        txt = 'Flower Collection (%s flowers):' % numFlower
        for flower in self.flowerlist:
            txt += '\n' + str(flower)

        return txt
# okay decompyling C:\Users\Maverick\Documents\Visual Studio 2010\Projects\Unfreezer\py2\toontown\estate\FlowerCollection.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.08.22 22:20:18 Pacific Daylight Time
