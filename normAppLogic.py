#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os, sys
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
import spectrumNote

from vidmapy.kurucz.atlas import Atlas
from vidmapy.kurucz.synthe import Synthe
from vidmapy.kurucz.parameters import Parameters
from vidmapy.kurucz.utility_functions import string_from_kurucz_code
from vidmapy.kurucz.parameters import _reference_composition

"""
DESCRIPTION

"""

class normAppLogic:

    def __init__(self,):
        self.folderHANDY = os.path.dirname(os.path.abspath(__file__))
        gridDefinitionsFile = os.path.join(self.folderHANDY, "gridsDefinitions.yaml")

        self.continuumRegionsLogic = regionLogic.RegionLogic()
        self.radialVelocityEstimator = radialVelocity.RadialVelocity()
        self.specSynthesizer = specInterface.SynthesizeSpectrum()
        self.gridDefinitions = gridDefinitionsRead.gridDefinition(gridDefinitionsFile)
        self.spectrumNote = spectrumNote.spectrumNote()

        self.spectrum = sp.Spectrum()
        self.theoreticalSpectrum = sp.Spectrum(wave=[],\
                                               flux=[])
        self.continuum = sp.Spectrum(wave=[],\
                                     flux=[])
        self.normedSpectrum = sp.Spectrum(wave=[],\
                                          flux=[])
        self.radialVelocity = 0.0
        self.oryginalWavelength = None

        self.minWave = 3500
        self.maxWave = 7000

        self.loadReferenceComposition(_reference_composition)


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

        self.spectrumNote.set_spectrum(fileName)

    def saveSpectrum(self,fileName):
        sp.saveSpectrum(fileName,self.spectrum)
        print("INFO : %s saved!"%fileName)

    def getLinesIdentification(self, threshold=None, shape=0):
        if threshold is not None:
            self.setLabelsThreshold(threshold)
        if self.theoreticalSpectrum.lines_identification is not None:
            mask = self.theoreticalSpectrum.lines_identification["strength"] < self._lines_label_threshold
            self._displayed_subset_of_lines = self.theoreticalSpectrum.lines_identification[mask].reset_index(drop=True)
        return self.defineIndicatorsShapes(shape)

    def setLabelsThreshold(self, threshold):
        self._lines_label_threshold = threshold

    def defineIndicatorsShapes(self, shape):
        # lines_wavelengths = self._displayed_subset_of_lines["wave"].values
        segments = []
        if shape == 1:
            self.getTextPositions()
            segments = [self.getSegment(row) for idx, row in self._displayed_subset_of_lines.iterrows()]
        elif shape == 2:
            segments = [self.getSimpleSegment(row) for idx, row in self._displayed_subset_of_lines.iterrows()]
        return segments


    def getTextPositions(self):
        self._displayed_subset_of_lines['text_x'] = np.linspace(self._displayed_subset_of_lines['wave'].min(),
                                                        self._displayed_subset_of_lines['wave'].max(),
                                                        num=len(self._displayed_subset_of_lines))   

    def getSegment(self, row):
        x = row['wave']
        depth = row['strength']
        text_x = row['text_x']
        segment = ((x,depth),(x, 1.0), (text_x, 1.1), (text_x, 2.1 - depth))
        return segment
    
    def getSimpleSegment(self, row):
        x = row['wave']
        depth = row['strength']
        segment = ((x,depth),(x, 1.05))
        return segment     

    def getLabelsAndPositions(self):
        if not 'text_x' in self._displayed_subset_of_lines:
            self.getTextPositions()
        positions = [(x, 1.1) for x in self._displayed_subset_of_lines['text_x']]
        texts = [self.getLineLabelTextIterrows(row) for idx, row in self._displayed_subset_of_lines.iterrows()]
        return texts, positions
    
    def getLineLabelTextIterrows(self, row):
        text = "{} {:.1f} {:.2f}".format(string_from_kurucz_code(row["atom_symbol"]), row["wave"],row["strength"])
        return text

    def getLineLabelText(self, index):
        row = self._displayed_subset_of_lines.loc[index,:]
        return self.getLineLabelTextIterrows(row)

    def readTheoreticalSpectrum(self,fileName,colWave=0,colFlux=1,skipRows=0):
        self.theoreticalSpectrum = sp.readSpectrum(fileName,\
                                                   colWave=colWave,\
                                                   colFlux=colFlux,\
                                                   skipRows=skipRows)

    def computeTheoreticalSpectrum(self,teff,logg,vmic,me,vsini,vmac,resolution):
        parameters = teff,logg,vmic,me,vsini,vmac,resolution
        # There was a bug - sometimes data from TKinter comes as string, so:
        parameters = [p if p is not str else float(p.replace(",","."))for p in parameters]
        try:
            self.theoreticalSpectrum = self.specSynthesizer.synthesizeSpectrum(parameters,
                                            minWave = self.minWave, 
                                            maxWave = self.maxWave)
        except:
            print("Unexpected error:", sys.exc_info()[0])
            print("Spectrum out of grid or some interpolation bug...")

    def computeSpectrumUsingSYNTHE(self,teff,logg,vmic,me,vsini,vmac,resolution,minWave=None,maxWave=None):
        resolution = min(resolution, 500000)
        if minWave is None:
            minWave = self.minWave
        if maxWave is None:
            maxWave = self.maxWave
        parameters = Parameters(teff=teff, 
                                logg=logg, 
                                metallicity=me, 
                                microturbulence=vmic,
                                vsini=vsini,
                                resolution=resolution,
                                wave_min=minWave,
                                wave_max=maxWave)
        try:
            if not (hasattr(self, '_atlas_model') and self._atlas_model.parameters == parameters):
                print("Start ATLAS model computation")
                atlasWorker = Atlas()
                self._atlas_model = atlasWorker.get_model(parameters)
                print("ALTAS model computation finished")

            syntheWorker = Synthe()
            print("Start SYNTHE spectrum computation")
            spectrum = syntheWorker.get_spectrum(self._atlas_model, parameters)
            print("SYNTHE spectrum computation finished")

            mask_wave = (spectrum.lines_identification['wave'] > minWave) & (spectrum.lines_identification['wave'] < maxWave)
            spectrum.lines_identification = spectrum.lines_identification[mask_wave]
            spectrum.lines_identification.sort_values('wave', inplace=True)

            self.theoreticalSpectrum = sp.Spectrum(wave=spectrum.wave, 
                                                    flux=spectrum.normed_flux, 
                                                    lines_identification=spectrum.lines_identification)
        except:
            print("ERROR: SYNTHE/ATLAS error!")
            print("Unexpected error:", sys.exc_info()[0])

        

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
        for ord,region in zip(self.continuumRegionsLogic.orders,contRegionsWaveAndFlux):
            wReg = []
            fReg = []
            for w,f in region:
                wReg.extend(w)
                fReg.extend(f)
            wRegOut = np.linspace(wReg[0],wReg[-1],int(max((wReg[-1]-wReg[0])/separation,1)))
            try:
                fRegOut = self.fitFunction(wReg,fReg,wRegOut,1,ord)
            except Exception as e:
                fRegOut = []
                wRegOut = []
                print(e)
                print("WARNING: Unable to fit, try making region shorter")
            wOut.extend(wRegOut)
            fOut.extend(fRegOut)

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

    def updateOrderOfActiveRegion(self,order):
        self.continuumRegionsLogic.setOrderOfActiveRegion(order)

    def analysisOutput(self, waveMin, waveMax):
        # TODO: Code routine that Ewa needs
        pass

    def getSpectrumBaseName(self):
        spectrumBaseName = ""
        if self.spectrum.name is not None:
            spectrumBaseName = os.path.basename(self.spectrumNote.spectrum_path)
        return spectrumBaseName

    def getNoteData(self):
        noteDataDict = self.spectrumNote.get_note_data()
        return noteDataDict

    def setNoteData(self, noteDataDict):
        self.spectrumNote.set_from_dict(noteDataDict)

    def loadReferenceComposition(self, referenceComposition):
        self.referenceComposition = copy.deepcopy(referenceComposition)
        # _reference_composition = [
        # [  1, 0.9204 , 'H' , 'Hydrogen'],
        # [  2, 0.07834, 'He', 'Helium'], ...

    def getElementsList(self):
        return [(x[0],x[2]) for x in self.referenceComposition]

    def relativeToAbsoluteAbundances(self, relativeAbundances):
        pass



################################################################################
### TESTS
################################################################################
def testLoadSaveSpectrum():
    nal=normAppLogic()

    nal.readSpectrum(os.path.join("exampleData", "803432iuw.txt"),skipRows=1)
    nal.saveSpectrum(os.path.join("exampleData", "saveTest.txt"))

    print(nal.spectrum)
    #nal.plotSpectrum()

def testGetContinuum():
    nal=normAppLogic()
    nal.readSpectrum(os.path.join("exampleData", "803432iuw.txt"),skipRows=1)

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
