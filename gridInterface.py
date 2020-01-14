#!/usr/bin/python3
# -*- coding: utf-8 -*-
import pandas as pd
import glob
import numpy as np
import re
import os
import time
import matplotlib.pyplot as plt
import itertools

from spectrum import Spectrum
"""
Spectrum grid interface which enable user to interpolate
in regular grid of spectra.
"""

class GridSynthesizer:
    def __init__(self,
                folder = "bigGrid",
                refWave = "refWave.dat",
                paramsList = ["teff","logg","vmic","me"],
                paramsNum = {"teff":1,"logg":2,"vmic":3,"me":0},
                paramsMult = {"teff":1,"logg":0.01,"vmic":1,"me":1},
                fluxFilesFilter = "*.norm",
                skipRows = 0,
                waveColumn = 0,
                fluxColumn = 0,
                comments = "#"
                ):

        self.paramsList = paramsList
        self.paramsNum = paramsNum
        self.paramsMult = paramsMult
        self.skipRows = skipRows # No of columns to skip in files with fluxes and wave
        self.waveColumn = waveColumn # count from 0
        self.fluxColumn = fluxColumn # count from 0
        self.comments = comments
        self.fluxFilesFilter = fluxFilesFilter

        dirname = os.path.normpath(os.path.dirname(os.path.abspath(__file__)))
        self.gridFolder = os.path.join(dirname, folder)
        self.wavelengthFileName = os.path.join(self.gridFolder, refWave)

        self.ifCommonWavelength = False if refWave is None else True
        if self.ifCommonWavelength:
            self.wave = self.loadRefWave()
        else:
            self.wave = None

        self.allFiles = self.getFileList()
        self.gridParams = self.getParams(self.allFiles)

        self.uniques = {k:np.unique(self.gridParams[:,i]) for i,k in enumerate(self.paramsList)}

    def getFileList(self):
        """
        List all model files available in grid
        """
        return glob.glob(os.path.join(self.gridFolder, self.fluxFilesFilter))


    def loadRefWave(self):
        # filename="./refWave.dat"
        df = pd.read_csv(self.wavelengthFileName,
                            header = None,
                            delim_whitespace = True,
                            comment = self.comments,
                            skiprows = self.skipRows,
                            )
        return df[0].values

    def getParams(self,fileNames):
        """
        Get model parameters from its name
        """
        regexNum = re.compile("[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)?")
        gridSpectra=[]
        for f in fileNames:
            f = os.path.basename(f)
            num = regexNum.findall(f)
            par = np.around([self.paramsMult[k]*float(num[self.paramsNum[k]]) for k in self.paramsList],3)
            gridSpectra.append(par)
        return np.asarray(gridSpectra)

    def findSurronding(self,pointDict):
        """
        Return surronding of model for interpolation,
        if out of grid returns None
        surronding may consists of 1,2,4,8 or 16 spectra
        """
        computedSurrondings = {
                                k:np.unique([self.findNearestLowerThan(pointDict[k],self.uniques[k]),
                                self.findNearestGreaterThan(pointDict[k],self.uniques[k])])
                                for k in self.paramsList
                              }
        computedSurrondings = [ [] if (len(computedSurrondings[k]) == 1 and computedSurrondings[k][0] != pointDict[k]) else computedSurrondings[k]  for k in self.paramsList ]

        # TODO low metalicity bug, problems with surrounding - not fully regular grid...
        surAll = list(itertools.product(*computedSurrondings))

        idx = 0
        for single in surAll:
            for i,s in enumerate(self.gridParams):
                #print(s ,single)
                if np.array_equal(single,s):
                    idx += 1
        ifAllTrue = True if (idx == len(surAll) and surAll!=[] ) else False

        if ifAllTrue:
            return surAll
        else:
            None

    def findNearestGreaterThan(self,searchVal, inputData):
        """FROM
        https://stackoverflow.com/questions/17118350/how-to-find-nearest-value-that-is-greater-in-numpy-array
        """
        diff = inputData - searchVal
        diff[diff<0] = np.amax(diff)-np.amin(diff) - diff[diff<0] #BigNumber - diff[diff<0]
        idx = diff.argmin()
        #return idx, inputData[idx]
        return inputData[idx]

    def findNearestLowerThan(self,searchVal, inputData):
        """FROM
        https://stackoverflow.com/questions/17118350/how-to-find-nearest-value-that-is-greater-in-numpy-array
        """
        diff = inputData - searchVal
        diff[diff>0] = -(np.amax(diff)-np.amin(diff)) - diff[diff>0] #-BigNumber - diff[diff<0]
        idx = diff.argmax()
        #return idx, inputData[idx]
        return inputData[idx]

    def multilinearInterpolation(self,points,values,point):
        """
        Do multilinear Interpolation
        """
        #Take ln af all data:
        point=np.asarray(point)
        points=np.asarray(points)
        values=np.asarray(values)
        #Iterpolate
        sizeOfCube=np.amax(points, axis=0) - np.amin(points, axis=0)
        sizeMask=sizeOfCube!=0
        sizeOfCube=sizeOfCube[sizeMask]
        solution=np.zeros_like(values[0])
        for p,v in zip(points,values):
            solution+=v*np.prod(sizeOfCube - np.abs(p[sizeMask]-point[sizeMask]))
        solution= solution/np.prod(sizeOfCube)
        return solution

    def interpolateSpectrum(self,pointDict):
        """
        Interpoalte on grid spectra in given parameters
        return spectrum object
        """

        if self.gridParams is None:
            print("First load GRID")
            return None

        surAll = self.findSurronding(pointDict)

        if surAll is None:
            print("Spectrum (%.0f %.2f %.2f %.1f) out of grid"%(pointDict["teff"],pointDict["logg"],pointDict["me"],pointDict["vmic"]) )
            return None

        point = [pointDict[k] for k in self.paramsList]
        data = []
        wave = self.wave
        for single in surAll:
            for i,(s,f) in enumerate(zip(self.gridParams,self.allFiles)):
                #print(s ,single)
                if np.array_equal(single,s):
                    spec = pd.read_csv(f,
                                        header = None,
                                        delim_whitespace = True,
                                        comment = self.comments,
                                        skiprows = self.skipRows,
                                        )
                    flux = spec[self.fluxColumn].values
                    if not self.ifCommonWavelength: #TODO: this needs to be tested
                        if wave is None:
                            wave = spec[self.waveColumn].values
                        else:
                            flux = np.interp(wave,spec[self.waveColumn].values,spec[self.fluxColumn].values)
                    data.append(flux)

        interpFlux = self.multilinearInterpolation(surAll, data, point)

        return Spectrum(wave = self.wave, flux = interpFlux)

    def getRanges(self,key):
        return min(self.uniques[key]),max(self.uniques[key])

def testInitClass():
    gs = GridSynthesizer()
    print(gs.getFileList()[0])
    # print(gs.gridParams()[0])
    print(gs.gridParams[0])

def testInitClass2():
    import matplotlib.pyplot as plt
    gs = GridSynthesizer(
        folder = "lowTempGrid",
        refWave = "waveRef.dat",
        paramsList = ["teff","logg"],
        paramsNum = {"teff":0,"logg":1},
        paramsMult = {"teff":1,"logg":0.1},
        fluxFilesFilter = "flux*",
    )
    print(gs.getFileList()[0])
    # print(gs.gridParams()[0])
    print(gs.gridParams[0])

    pointDict = {"teff": 9100,"logg": 3.85,"me":5}
    s = gs.findSurronding(pointDict)
    print(s)

    sp = gs.interpolateSpectrum(pointDict)
    plt.plot(sp.wave,sp.flux)
    plt.show()

    for l in np.arange(3.5,4,0.025):
        pointDict = {"teff": 9050,"logg": l,"me":5}
        sp = gs.interpolateSpectrum(pointDict)
        plt.plot(sp.wave,sp.flux)
    plt.show()

def main():
    testInitClass()
    testInitClass2()

if __name__ == '__main__':
	main()
