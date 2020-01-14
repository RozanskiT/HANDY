#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
# try:
#     from yaml import CLoader as Loader, CDumper as Dumper
# except ImportError:
#     from yaml import Loader, Dumper
"""
DESCRIPTION

"""
class gridDefinition:

    def __init__(self,configurationFile):
        self.gridDefinitions = self.loadConfigurationFile(configurationFile)
        self.choosenGrid = None

    def loadConfigurationFile(self,configurationFile):
        data = None
        try:
            with open(configurationFile,'r') as f:
                data = f.read()
            data = yaml.load(data, Loader=yaml.FullLoader)
        except Exception as e:
            print("ERRORS in configuration file {}!!!".format(configurationFile))
            sys.stderr.write("Exception: %s\n" % str(e))
            sys.exit(1)
        return data

    def listAvailibleGrids(self):
        return list(self.gridDefinitions.keys())

    def setChoosenGrid(self,gridName):
        if  self.gridDefinitions is None:
            print("First load configuration file correctly!")
            return
        if gridName in self.gridDefinitions:
            self.choosenGrid = self.gridDefinitions[gridName]
            if "/" in self.choosenGrid["folderName"]:
                self.choosenGrid["folderName"] = self.choosenGrid["folderName"].replace("/", "")
        else:
            print("Chosen grid doesn't exist")

    def getAllParamtersOfGrid(self):
        allReturn = (
                        self.choosenGrid["folderName"],
                        self.choosenGrid["teff"],
                        self.choosenGrid["logg"],
                        self.choosenGrid["vmic"],
                        self.choosenGrid["me"],
                        self.choosenGrid["fluxFilesFilter"],
                        self.choosenGrid["fluxNameToParameters"],
                        self.choosenGrid["multiplicationFactors"],
                        self.choosenGrid["waveFile"],
                        self.choosenGrid["skipRows"],
                        self.choosenGrid["waveColumn"],
                        self.choosenGrid["fluxColumn"],
                        self.choosenGrid["comments"],
                        )
        return allReturn

    def setGridParams(self):
        paramsList = [ k for k in ["teff","logg","vmic","me"] if self.choosenGrid[k] == True]
        folder = self.choosenGrid["folderName"]
        refWave = self.choosenGrid["waveFile"]
        paramsNum = self.choosenGrid["fluxNameToParameters"]
        paramsMult = self.choosenGrid["multiplicationFactors"]
        fluxFilesFilter = self.choosenGrid["fluxFilesFilter"]
        skipColumns = self.choosenGrid["skipRows"]
        waveColumn = self.choosenGrid["waveColumn"]
        fluxColumn = self.choosenGrid["fluxColumn"]
        comments = self.choosenGrid["comments"]
        return paramsList, folder, refWave, paramsNum, paramsMult, fluxFilesFilter, skipColumns, waveColumn, fluxColumn, comments

    def getDefinedVariables(self):
        r = {k:self.choosenGrid[k] for k in ["teff","logg","vmic","me"]}
        return r

def testYaml1():
    yamlName = "gridsDefinitions.yaml"
    gd = gridDefinition(yamlName)
    print(gd.listAvailibleGrids())
    gd.setChoosenGrid("basicGrid")
    allParams = gd.getAllParamtersOfGrid()

    print(allParams)

def main():
    testYaml1()


if __name__ == '__main__':
	main()
