#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
DESCRIPTION

definition of Spectrum class
"""
import numpy as np
import spectrum as sp
import copy

class RegionLogic:

    def __init__(self):

        self.regions=[]
        self.orders=[]
        self.specialPoints=[]
        self.activeRegionNumber=0

        self.lastRegions=[]
        self.lastOrders=[]
        self.lastActiveRegionNumber=[]

        self.defaultOrder = 3
    #===========================================================================
    # REGIONS
    def addRegion(self,newRange,ifCreateNewRegion=False):
        """
        It is possible to add new range to existing region
        or while creating new region.
        Lastly added region become active region.
        Ranges in between newRange and active region become
        regions of active region.
        """
        self.saveLast()
        changeActiveRegion=0
        if self.regions == []: # If there are no regions just create one with one range
            self.regions.append([newRange])
            self.orders.append(self.defaultOrder)
        else:
            if ifCreateNewRegion:
                for region  in self.regions: # modify region by region
                    rangesForRemove=[]
                    newRegion=[]
                    if newRange[0] <= region[-1][-1]\
                       and newRange[1] >= region[0][0]:
                       # newRange and region have common parts
                        for tmin,tmax in region: # modify range by range
                            if tmin<=newRange[1]\
                               and tmax>=newRange[0]:# if new range is sub-range
                                newRange[1]=max(tmax,newRange[1])
                                newRange[0]=min(tmin,newRange[0])
                                rangesForRemove.append([tmin,tmax])
                            elif tmax<newRange[0]:
                                pass
                            elif tmin>newRange[1]:
                                newRegion.append([tmin,tmax])
                        for i in newRegion + rangesForRemove:
                            # Remove ranges which would be doubled
                            region.remove(i)
                    if newRegion:
                        self.regions.append(newRegion)
                        # self.orders.append(self.defaultOrder)
                        self.orders.append(self.orders[self.activeRegionNumber])
                for i in sorted([i for i, x in enumerate(self.regions) if x  == []], reverse=True):
                    del self.regions[i]
                    del self.orders[i]
                self.regions.append([newRange])
                self.orders.append(self.defaultOrder)
                self.regions, self.orders = (list(t) for t in zip(*sorted(zip(self.regions, self.orders))))
                self.activeRegionNumber = self.regions.index([newRange])
            else:
                ifReplaceAllActiveRange=False
                # [indmin,indmax] = newRange
                for region in self.regions: # modify region by region
                    rangesForRemove=[]
                    if region[-1][-1] > newRange[0]\
                       and region[-1][-1] < self.regions[self.activeRegionNumber][-1][-1]:
                       # if region is between active part and newRange on the left
                        for tmin,tmax in region:
                            if tmin<=newRange[1] and tmax>=newRange[0]:
                                # Overlapping
                                rangesForRemove.append([tmin,tmax])
                                newRange[1]=max(tmax,newRange[1])
                                newRange[0]=min(tmin,newRange[0])
                            elif newRange[1] < tmin:
                                # Not overlapping
                                rangesForRemove.append([tmin,tmax])
                                self.regions[self.activeRegionNumber].append([tmin,tmax])
                                self.regions[self.activeRegionNumber].sort()
                        if (rangesForRemove==region):
                            changeActiveRegion-=1
                        for i in rangesForRemove:
                            region.remove(i)
                    elif region[0][0]<newRange[1]\
                         and self.regions[self.activeRegionNumber][0][0]<region[0][0]:
                        # if region is between active part and newRange on the right
                        for tmin,tmax in region:
                            if tmin<=newRange[1] and tmax>=newRange[0]:
                                # Overlapping
                                rangesForRemove.append([tmin,tmax])
                                newRange[1]=max(tmax,newRange[1])
                                newRange[0]=min(tmin,newRange[0])
                            elif newRange[0] > tmax:
                                # Not overlapping
                                rangesForRemove.append([tmin,tmax])
                                self.regions[self.activeRegionNumber].append([tmin,tmax])
                        for i in rangesForRemove:
                            region.remove(i)
                    else: # Easy case, do not overlapping any other region
                        for tmin,tmax in region:
                            if((tmin<=newRange[1] and tmax>=newRange[0])):
                                rangesForRemove.append([tmin,tmax])
                                newRange[1]=max(tmax,newRange[1])
                                newRange[0]=min(tmin,newRange[0])
                        if rangesForRemove==self.regions[self.activeRegionNumber]:
                            ifReplaceAllActiveRange=True
                        else:
                            for i in rangesForRemove:
                                region.remove(i)
                if ifReplaceAllActiveRange:
                    del(self.regions[self.activeRegionNumber])
                    self.regions.append([newRange])
                else:
                    self.regions[self.activeRegionNumber].append(newRange)
                self.regions[self.activeRegionNumber].sort()
                self.regions, self.orders = (list(t) for t in zip(*sorted(zip(self.regions, self.orders))))
            for i in sorted([i for i, x in enumerate(self.regions) if x == []], reverse=True):
                del self.regions[i]
                del self.orders[i]
            self.activeRegionNumber+=changeActiveRegion

    def deleteRegionOrPoint(self,x,y):
        self.saveLast()
        minDinstancePoint=np.inf
        minDinstanceRange=np.inf
        minIdxReg=0
        minIdxRan=0
        f = lambda x1,y1,x2,y2 : (x1-x2)**2 + (y1-y2)**2
        if len(self.specialPoints) != 0:
            idxPoint,minDinstancePoint = self.nearest(x,y,f)
        for idxReg,region in enumerate(self.regions):
            for idxRan,r in enumerate(region):
                newDistance = min(f(x,0,r[0],0),f(x,0,r[1],0))
                if newDistance < minDinstanceRange:
                    minDinstanceRange = newDistance
                    minIdxReg = idxReg
                    minIdxRan = idxRan
                else:
                    break
                    # Because ranges are sorted
        if minDinstanceRange < minDinstancePoint:
            del self.regions[minIdxReg][minIdxRan]
            if not self.regions[minIdxReg]:
                if minIdxReg<=self.activeRegionNumber\
                    and self.activeRegionNumber:
                    self.activeRegionNumber-=1
                del self.regions[minIdxReg]
                del self.orders[minIdxReg]
        else:
            if len(self.specialPoints) != 0:
                del self.specialPoints[idxPoint]
        return

    def changeActiveRegion(self,x,y):
        minDistanceRegion=np.inf
        minIdxReg = 0
        f = lambda x1,y1,x2,y2 : (x1-x2)**2 + (y1-y2)**2
        for idxReg,region in enumerate(self.regions):
            newDistance = min(f(x,0,region[0][0],0),f(x,0,region[-1][-1],0))
            if newDistance < minDistanceRegion:
                minDistanceRegion = newDistance
                minIdxReg = idxReg
            else:
                break
        self.activeRegionNumber = minIdxReg

    def indexToWaveRanges(self,wave):
        waveRegions=[]
        for region in self.regions:
            waveRegions.append([[wave[l],wave[r]] for l,r in region ])
        return waveRegions

    def waveToIndexRegions(self,wave):
        indexRegions=[]
        for region in self.regions:
            ran=[]
            for r in region:
                indmin, indmax = np.searchsorted(wave, r)
                indmax = min(len(wave) - 1, indmax)
                indmin = min(len(wave) - 1, indmin)
                ran.append([indmin,indmax])
            indexRegions.append(ran)
        return indexRegions

    def waveToSpectrumParts(self,spectrum):
        contRegionsWaveAndFlux = []
        forRemove = [] # Remove ranges wich are empty
        idxRegions = self.waveToIndexRegions(spectrum.wave)
        for region in idxRegions:
            contRegion = []
            for r in region:
                fluxRange = [spectrum.wave[r[0]:r[1]], spectrum.flux[r[0]:r[1]]]
                if len(fluxRange[0]) == 0:
                    print("Empty range {:.5f} - {:.5f} will be removed.".format(r[0],r[1]))
                    forRemove.append(np.mean(r))
                else:
                    contRegion.append(fluxRange)
            contRegionsWaveAndFlux.append(contRegion)
        for wMean in forRemove:
            self.deleteRegionOrPoint(wMean,0.0)
        return contRegionsWaveAndFlux

    def saveLast(self):
        self.lastRegions.append(copy.deepcopy(self.regions))
        self.lastOrders.append(copy.deepcopy(self.orders))
        self.lastActiveRegionNumber.append(self.activeRegionNumber)

    def restoreLast(self):
        try:
            self.regions = copy.deepcopy(self.lastRegions.pop())
            self.orders = copy.deepcopy(self.lastOrders.pop())
            self.activeRegionNumber = self.lastActiveRegionNumber.pop()
        except:
            self.regions = []
            self.orders = [ ]
            self.activeRegionNumber = 0

    #===========================================================================
    # ORDERS

    def setOrderOfActiveRegion(self,order):
        if self.orders:
            self.orders[self.activeRegionNumber] = order

    #===========================================================================
    # POINTS
    def addPoint(self,x, y,spectrum):
        l=np.searchsorted(spectrum.wave,x-1,side='left')
        r=np.searchsorted(spectrum.wave,x+1,side='right')
        median=np.median(spectrum.flux[l:r])
        ratio=y/median
        self.specialPoints.append([x, ratio])

    def nearest(self,x,y,f):
        index=0
        minimum=np.inf
        for i,(w,z) in enumerate(self.specialPoints):
            a=f(x,0,w,0)                 # NEAREST IN X
            if(a<minimum):
                index=i
                minimum=a
        return index,minimum

    def getAbsolutePoints(self,spectrum):
        absPoints = []
        if spectrum.wave is not None:
            for x,y in self.specialPoints:
                l=np.searchsorted(spectrum.wave,x-1,side='left')
                r=np.searchsorted(spectrum.wave,x+1,side='right')
                median=np.median(spectrum.flux[l:r])
                yAbs=y*median
                absPoints.append([x,yAbs])
        return absPoints

    def autoFitPoints(self,theoreticalSpectrum):
        if theoreticalSpectrum.wave != []:
            for i,[x,y] in enumerate(self.specialPoints):

                l = np.searchsorted(theoreticalSpectrum.wave,x-1,side='left')
                r = np.searchsorted(theoreticalSpectrum.wave,x+1,side='right')
                #averageTheoretical = (theoreticalSpectrum.flux[l]+theoreticalSpectrum.flux[r])/2
                averageTheoretical = np.median(theoreticalSpectrum.flux[l:r])

                self.specialPoints[i][1] = 1./averageTheoretical

    def applyRadialVelocity(self,radialVelocity):
        #vrad KM/S
        beta = radialVelocity/299792.458
        conts = np.sqrt((1+beta)/(1-beta))
        for i, region in enumerate(self.regions):
            for j,r in enumerate(region):
                self.regions[i][j][0]=r[0]*conts
                self.regions[i][j][1]=r[1]*conts
        for i,p in enumerate(self.specialPoints):
            self.specialPoints[i][0]=p[0]*conts
    #===========================================================================
    # SAVE AND LOAD

    def readRegionsFile(self,spectrum,fileName):
        # try:
        with open(fileName, 'r') as f:
            lines=f.readlines()
            ifReadPoints=False
            ifReadOrders=False
            tempOrders = []
            tempRegions = []
            tempSpecialPoints = []
            for line in lines:
                if line[0:16]=='# SeparatePoints':
                    ifReadPoints=True
                    continue
                if line[0:8]=='# Orders':
                    ifReadPoints=False
                    ifReadOrders=True
                    continue
                if line.startswith('#') or line.startswith(' '):
                    continue
                elements=str.split(line)
                if ifReadPoints:
                    w = float(elements[0])
                    if w > min(spectrum.wave) and w < max(spectrum.wave):
                        tempSpecialPoints.append([w,float(elements[1])])
                elif ifReadOrders:
                    for v in elements:
                        tempOrders.append(int(v))
                else:
                    tempRange = []
                    for i in range(int(len(elements)/2)):
                        l = float(elements[2*i])
                        r = float(elements[2*i+1])
                        if r<=min(spectrum.wave) or l>=max(spectrum.wave):
                            continue
                        tempRange.append([l,r])
                    if tempRange: # If not empty
                        tempRegions.append(tempRange)
            if not tempOrders and ifReadOrders==False:
                tempOrders = [self.defaultOrder for _ in tempRegions]
            self.regions = tempRegions
            self.specialPoints = tempSpecialPoints
            self.orders = tempOrders
        # except:
        #     print("WARNING: RegionLogic.readRegionsFile\n"\
        #           +"Unable to load continuum from this file")

    def saveRegionsFile(self,spectrum,fileName):
        with open(fileName, 'w') as f:
            f.write('# Continuum definition file\n')
            f.write('#====================================\n')
            f.write('# Ranges grouped in regions\n')
            for region in self.regions:
                for r in region:
                    f.write("%8.3f %8.3f "%(r[0],r[1]))
                f.write('\n')
            f.write('#====================================\n')
            f.write('# SeparatePoints\n')
            for p in self.specialPoints:
                f.write("%7.3f %7.3f\n"%(p[0],p[1]))
            f.write('#====================================\n')
            f.write('# Orders\n')
            for p in self.orders:
                f.write("%d "%(p,))
            f.write('\n#====================================\n')
            print("SAVED: %s"%(fileName))

    def updateRegionsAndPoints(self,spectrum):
        tempRegions = []
        tempSpecialPoints = []
        for region in self.regions:
            tempRegion=[]
            for r in region:
                if r[1]<=min(spectrum.wave) or r[0]>=max(spectrum.wave):
                    continue
                tempRegion.append(r)
            if tempRegion:
                tempRegions.append(tempRegion)
        for p in self.specialPoints:
            if p[0] > min(spectrum.wave) and p[0] < max(spectrum.wave):
                tempSpecialPoints.append(p)
        self.regions = tempRegions
        self.specialPoints = tempSpecialPoints

    def clearAll(self):
        self.regions = []
        self.specialPoints = []
        self.activeRegionNumber = 0

        self.lastRegions = []
        self.lastActiveRegionNumber = []

    def getOrderOfActiveRegion(self):
        if self.orders:
            return self.orders[self.activeRegionNumber]
        else:
            return self.defaultOrder

    #===========================================================================
    # PRINTING
    def printRegions(self):
        print(self.regions)

    def printSpecialPoints(self):
        print(self.specialPoints)

    def printOrders(self):
        print(self.orders)

################################################################################
### TESTS
################################################################################

def testRegions():
    regionInterface = RegionLogic()
    regionInterface.addRegion([104.23,300])
    # regionInterface.printRegions()
    assert(regionInterface.regions == [[[104.23,300]]])
    assert(regionInterface.orders == [3])
    regionInterface.setOrderOfActiveRegion(5)

    regionInterface.addRegion([700,900])
    assert(regionInterface.regions == [[[104.23,300],[700,900]]])
    assert(regionInterface.orders == [5])

    regionInterface.addRegion([1100,1300],ifCreateNewRegion=True)
    assert(regionInterface.regions == [[[104.23,300],[700,900]],[[1100,1300]]])
    assert(regionInterface.orders == [5,3])

    regionInterface.addRegion([1400,1500])
    assert(regionInterface.regions == [[[104.23,300],[700,900]],[[1100,1300],[1400,1500]]])
    assert(regionInterface.orders == [5,3])

    regionInterface.addRegion([1200,1450])
    assert(regionInterface.regions == [[[104.23,300],[700,900]],[[1100,1500]]])
    assert(regionInterface.orders == [5,3])

    regionInterface.addRegion([10,50],ifCreateNewRegion=True)
    # regionInterface.printRegions()
    assert(regionInterface.regions == [[[10,50]],[[104.23,300],[700,900]],[[1100,1500]]])
    assert(regionInterface.orders == [3,5,3])

    regionInterface.changeActiveRegion(20,0)
    regionInterface.setOrderOfActiveRegion(4)
    assert(regionInterface.regions == [[[10,50]],[[104.23,300],[700,900]],[[1100,1500]]])
    assert(regionInterface.orders == [4,5,3])

    regionInterface.addRegion([40,1410],ifCreateNewRegion=True)
    # regionInterface.printRegions()
    # regionInterface.printOrders()
    assert(regionInterface.regions == [[[10, 1500]]])
    assert(regionInterface.orders == [3])

    regionInterface.deleteRegionOrPoint(400,0)
    assert(regionInterface.regions == [])
    assert(regionInterface.orders == [])

    regionInterface.addRegion([1100,1300],ifCreateNewRegion=True)
    regionInterface.setOrderOfActiveRegion(4)
    assert(regionInterface.regions == [[[1100,1300]]])
    assert(regionInterface.orders == [4])

    regionInterface.addRegion([800,1000],ifCreateNewRegion=True)
    regionInterface.setOrderOfActiveRegion(5)

    regionInterface.addRegion([1400,1500])

    assert(regionInterface.regions == [[[800,1000],[1100,1300],[1400,1500]]])
    assert(regionInterface.orders == [5])

    regionInterface.addRegion([1020,1080],ifCreateNewRegion=True)
    regionInterface.printRegions()
    regionInterface.printOrders()

def main():
    testRegions()


if __name__ == '__main__':
	main()
