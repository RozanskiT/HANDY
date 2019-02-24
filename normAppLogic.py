#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import numpy as np
import pandas as pd
import copy
from scipy.interpolate import Akima1DInterpolator
import matplotlib.pyplot as plt
from PyAstronomy import pyasl

import spectrum as sp
import regionLogic
import radialVelocity
import specInterface
import gridDefinitionsRead

"""
DESCRIPTION

"""

class normAppLogic:

    def __init__(self,):
        self.folderHANDY = os.path.dirname(os.path.abspath(__file__))
        gridDefinitionsFile = self.folderHANDY+"/gridsDefinitions.yaml"

        self.continuumRegionsLogic = regionLogic.RegionLogic()
        self.radialVelocityEstimator = radialVelocity.RadialVelocity()
        self.specSynthesizer = specInterface.SynthesizeSpectrum()
        self.gridDefinitions = gridDefinitionsRead.gridDefinition(gridDefinitionsFile)

        self.spectrum = sp.Spectrum()
        self.theoreticalSpectrum = sp.Spectrum(wave=[],\
                                               flux=[])
        self.continuum = sp.Spectrum(wave=[],\
                                     flux=[])
        self.normedSpectrum = sp.Spectrum(wave=[],\
                                          flux=[])
        self.radialVelocity = 0.0
        self.oryginalWavelength = None


    def readSpectrum(self,fileName,colWave=0,colFlux=1,skipRows=0):
        """
        Reading spectrum in text or FITS format
        and update regions and points
        """
        if not ".fits" in fileName:
            self.spectrum = sp.readSpectrum(fileName,\
                                                  colWave=colWave,\
                                                  colFlux=colFlux,\
                                                  skipRows=skipRows)

        else:
            self.spectrum = sp.Spectrum()
            """ Check more at
            http://archive.eso.org/cms/eso-data/help/1dspectra.html
            https://www.hs.uni-hamburg.de/DE/Ins/Per/Czesla/PyA/PyA/pyaslDoc/aslDoc/readFitsSpec.html
            """
            self.spectrum.wave, self.spectrum.flux = pyasl.read1dFitsSpec(fileName)
            # self.spectrum.wave = self.spectrum.wave.byteswap().newbyteorder()
            self.spectrum.flux = self.spectrum.flux.byteswap().newbyteorder() #TODO PyAstronomy bug
            self.spectrum.name = fileName
        self.radialVelocity = 0.0
        self.oryginalWavelength = copy.deepcopy(self.spectrum.wave)


    def saveSpectrum(self,fileName):
        sp.saveSpectrum(fileName,self.spectrum)
        print("INFO : %s saved!"%fileName)

    def readTheoreticalSpectrum(self,fileName,colWave=0,colFlux=1,skipRows=0):
        self.theoreticalSpectrum = sp.readSpectrum(fileName,\
                                                   colWave=colWave,\
                                                   colFlux=colFlux,\
                                                   skipRows=skipRows)

    def computeTheoreticalSpectrum(self,teff,logg,vmic,me,vsini,vmac,resolution):
        parameters = teff,logg,vmic,me,vsini,vmac,resolution
        try:
            self.theoreticalSpectrum = self.specSynthesizer.synthesizeSpectrum(parameters,minWave = 3500, maxWave = 7000)
        except:
            print("Spectrum out of grid or some interpolation bug...")

    def saveNormedSpectrum(self,fileName,correctForRadialVelocity):
        saveSpectrum = copy.deepcopy(self.normedSpectrum)
        # print(correctForRadialVelocity)
        if not correctForRadialVelocity:
            print("Modifying to oryginal wavelength.")
            saveSpectrum.wave = self.oryginalWavelength
        else:
            print("Saving corrected for radial velocity.")
        sp.saveSpectrum(fileName,saveSpectrum)
        print("INFO : %s saved!"%fileName)

    def saveTheoreticalSpectrum(self,fileName):
        sp.saveSpectrum(fileName,self.theoreticalSpectrum)
        print("INFO : %s saved!"%fileName)

    def plotSpectrum(self):
        if self.spectrum.wave is not None:
            plt.plot(self.spectrum.wave,self.spectrum.flux)
            plt.show()
        else:
            print("WARNING: normAppLogic.plotSpectrum first read spectrum")

    def getValuesForPlotSpecialPoints(self):
        absPoints = self.continuumRegionsLogic.getAbsolutePoints(self.spectrum)
        x,y = zip(*absPoints)
        return x,y


    def getContinuumRangesForPlot(self):
        contRegionsWaveAndFlux = [[[[],[]]]]
        if self.spectrum.wave is not None:
            contRegionsWaveAndFlux = self.continuumRegionsLogic.waveToSpectrumParts(self.spectrum)
        else:
            print("WARNING: normAppLogic.getContinuumRangesForPlot:\n"\
                 +"first load spectrum for norming")
        return contRegionsWaveAndFlux


    def normSpectrum(self):
        sep = 1
        w,f = self.fitFunctionToRegions(separation = sep)
        # Insert special points before interpolation
        absolutePoints = self.continuumRegionsLogic.getAbsolutePoints(self.spectrum)
        for x,y in absolutePoints:
            idx = np.searchsorted(w,x,side='left')
            w.insert(idx,x)
            f.insert(idx,y)
        # -----
        if len(w)>1:
            interp = Akima1DInterpolator(w, f)
            self.continuum.wave = self.spectrum.wave
            self.continuum.flux = interp(self.spectrum.wave,extrapolate=False)
            self.normedSpectrum.flux = self.spectrum.flux / self.continuum.flux
            np.nan_to_num(self.normedSpectrum.flux,copy=False)
        else:
            self.continuum.wave = []
            self.continuum.flux = []
            self.normedSpectrum.flux = []
            self.normedSpectrum.wave = []

    def ifOnNormedSpectrum(self,workOnNormedSpectrum):
        if workOnNormedSpectrum:
            self.continuumRegionsLogic.clearAll()
            self.continuum.wave = []
            self.continuum.flux = []
            self.normedSpectrum = copy.deepcopy(self.spectrum)
        else:
            self.normedSpectrum.wave = []
            self.normedSpectrum.flux = []

    def fitFunctionToRegions(self,separation=1):
        self.normedSpectrum.wave = copy.deepcopy(self.spectrum.wave)
        contRegionsWaveAndFlux = self.continuumRegionsLogic.waveToSpectrumParts(self.spectrum)
        wOut = []
        fOut = []
        for region in contRegionsWaveAndFlux:
            wReg = []
            fReg = []
            for w,f in region:
                wReg.extend(w)
                fReg.extend(f)
            wRegOut = np.linspace(wReg[0],wReg[-1],max((wReg[-1]-wReg[0])/separation,1))
            fRegOut = self.fitFunction(wReg,fReg,wRegOut,1,3)
            wOut.extend(wRegOut)
            fOut.extend(fRegOut)
        # plt.plot(wOut,fOut,'.')
        # plt.show()
        return wOut,fOut


    def fitFunction(self,xIn,yIn,xOut,fitType,degree):
        """
        fitType = 1 : Chebyshev
        fitType = 2 : Legendre
        """
        yOut=[]
        if fitType == 1:
            fit = np.polynomial.chebyshev.chebfit(xIn,yIn, degree)
            yOut = np.polynomial.chebyshev.chebval(xOut,fit)
        else: #elif fitType == 2:
            fit = np.polynomial.legendre.Legendre.fit(xIn,yIn, degree)
            yOut = np.polynomial.legendre.legval(xOut,fit)
        return yOut

    def applyRadialVelocity(self,radVel):
        self.spectrum.wave, self.spectrum.flux = self.radialVelocityEstimator.applyRadialVelocity(\
                                                         self.spectrum.wave,\
                                                         self.spectrum.flux,\
                                                         radVel)
        self.radialVelocity+=radVel
################################################################################
### TESTS
################################################################################
def testLoadSaveSpectrum():
    nal=normAppLogic()

    nal.readSpectrum("exampleData/803432iuw.txt",skipRows=1)
    nal.saveSpectrum("exampleData/saveTest.txt")

    print(nal.spectrum)
    #nal.plotSpectrum()

def testGetContinuum():
    nal=normAppLogic()
    nal.readSpectrum("exampleData/803432iuw.txt",skipRows=1)

    nal.continuumRegionsLogic.addRegion([4850,4890])
    nal.continuumRegionsLogic.addRegion([5000,5100])
    nal.continuumRegionsLogic.addRegion([5500,5600])
    nal.continuumRegionsLogic.printRegions()
    indexRegions = nal.continuumRegionsLogic.waveToIndexRegions(nal.spectrum.wave)
    print(indexRegions)

    waveCont = []
    fluxCont = []
    for reg in indexRegions:
        for ran in reg:
            print(ran)
            waveCont.extend(nal.spectrum.wave[ran[0]:ran[1]])
            fluxCont.extend(nal.spectrum.flux[ran[0]:ran[1]])
    plt.plot(waveCont,fluxCont)
    plt.show()
def main():
    #testLoadSaveSpectrum()
    testGetContinuum()

if __name__ == '__main__':
	main()
