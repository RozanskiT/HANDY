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

from spectrum import Spectrum, readSpectrum, saveSpectrum
"""
DESCRIPTION

"""

class BigGridSynthesizer:
    def __init__(self,
                folder = "/bigGrid/",
                refWave = "refWave.dat",
                paramsDict = {"teff":True,"logg":True,"vmic":True,"me":True},
                paramsNum = {"teff":0,"logg":1,"vmic":3,"me":2},
                paramsMult = {"teff":1,"logg":100,"vmic":1,"me":1},
                ):
        self.paramsDict = paramsDict
        self.paramsNum = paramsNum
        self.paramsMult = paramsMult
        dirname = os.path.dirname(os.path.abspath(__file__))
        self.bigGridFolder = dirname + folder
        self.wavelengthFileName = self.bigGridFolder + refWave
        self.wave = self.loadRefWave()
        self.allFiles = self.getFileList()
        self.spectraList = self.getParams(self.allFiles)

    def getFileList(self):
        """
        List all model files available in grid
        """
        return glob.glob(self.bigGridFolder+"*.norm")

    def loadRefWave(self):
        # filename="./refWave.dat"
        df = pd.read_table(self.wavelengthFileName,
                            header=None,
                            delim_whitespace=True,
                            comment='#',
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
            num=regexNum.findall(f)
            gridSpectra.append([float(num[1]),float(num[2])/100.,float(num[0]),float(num[3])])
        return np.asarray(gridSpectra)

    def getFilenameFromPoint(self,point):
        teff = point[0]
        logg = point[1]*100
        me = point[2]
        vmic = point[3]
        return self.bigGridFolder+"m%3.2ft%dg%dv%.1f_3500_7000.norm"%(me,teff,logg,vmic)

    def readWave(self,point):
        name=self.getFilenameFromPoint(point)
        df=pd.read_table(name,header=None,delim_whitespace=True,comment='#')
        return df[0].values

    def findSurronding(self,teff,logg,me,vmic):
        """
        Return surronding of model for interpolation,
        if out of grid returns None
        surronding may consists of 1,2,4,8 or 16 spectra
        """
        allTeff = np.unique([s[0] for s in self.spectraList])
        alllogg = np.unique([s[1] for s in self.spectraList])
        allme = np.unique([s[2] for s in self.spectraList])
        allvmic = np.unique([s[3] for s in self.spectraList])

        surTeff = np.unique([self.findNearestLowerThan(teff,allTeff),self.findNearestGreaterThan(teff,allTeff)])
        surlogg = np.unique([self.findNearestLowerThan(logg,alllogg),self.findNearestGreaterThan(logg,alllogg)])
        surme = np.unique([self.findNearestLowerThan(me,allme),self.findNearestGreaterThan(me,allme)])
        survmic = np.unique([self.findNearestLowerThan(vmic,allvmic),self.findNearestGreaterThan(vmic,allvmic)])

        if len(surTeff) == 1 and surTeff[0] != teff:
            surTeff = []
        if len(surlogg) == 1 and surlogg[0] != logg:
            surlogg = []
        if len(surme) == 1 and surme[0] != me:
            surme = []
        if len(survmic) == 1 and survmic[0]!=vmic:
            survmic = []
        # TODO low metalicity bug, problems with surrounding
        surAll = list(itertools.product(surTeff,surlogg,surme,survmic))
        #abundances={'He':-0.1,'He':-0.5,'He':-1,'He':-2}

        idx = 0
        for single in surAll:
            for i,s in enumerate(self.spectraList):
                #print(s ,single)
                if np.array_equal(single,s):
                    idx += 1
        ifAllTrue = True if (idx == len(surAll) and surAll!=[] ) else False
        #ifAllTrue=any(any((np.asarray(self.spectraList) == np.asarray(single)).all(1)) for single in surAll)
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

    def interpolateSpectrum(self,teff,logg,me,vmic):
        """
        Interpoalte on grid spectra in parameters teff, logg ,me, vmic
        return spectrum object
        """
        if self.spectraList is None:
            print("First load GRID")
            return None

        surAll=self.findSurronding(teff,logg,me,vmic)
        if surAll is None:
            print("Spectrum (%.0f %.2f %.2f %.1f) out of grid"%(teff,logg,me,vmic) )
            return None

        point=[teff,logg,me,vmic]
        data=[]
        for single in surAll:
            for i,s in enumerate(self.spectraList):
                #print(s ,single)
                if np.array_equal(single,s):
                    data.append(self.readWave(single))

        interpFlux=self.multilinearInterpolation(surAll , data , point)

        return Spectrum(wave=self.wave,flux=interpFlux)

def testInterpolateSpectrum():
    bg=BigGridSynthesizer()
    teff=25100
    logg=3.6
    me=0.4
    vmic=5
    start=time.time()
    s = bg.interpolateSpectrum(teff,logg,me,vmic)
    end=time.time()
    print(s.wave,s.flux)
    # plt.plot(s.wave,s.flux)
    # plt.show()
    print("TIME : ", end-start)

def testFinSurronding():
    bg=BigGridSynthesizer()
    p=bg.spectraList[0]
    print(bg.findSurronding(*p))


def testInit():
    bg=BigGridSynthesizer()
    p=bg.spectraList[0]

    for p in bg.spectraList[0:10]:
        print(p)
        flux=bg.readWave(p)
        plt.plot(bg.wave,flux)
    plt.show()


def main():
    #testFinSurronding()
    testInterpolateSpectrum()
if __name__ == '__main__':
	main()
