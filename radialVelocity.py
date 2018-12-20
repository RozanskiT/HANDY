#!/usr/bin/python3
# -*- coding: utf-8 -*-

import matplotlib.pyplot as plt
import numpy as np
import scipy.ndimage
import scipy.constants
import pandas as pd

class RadialVelocity(object):

    def __init__(self,refSpecW=[],refSpecF=[],specW=[],specF=[]):

        self.refSpecW=refSpecW
        self.refSpecF=refSpecF
        self.specW=specW
        self.specF=specF

        #----- VELOCITY AND CFF
        self.velCCF=[]
        self.ccf=[]
        #-----
        self.refFlux=[]
        self.flux=[]
        self.logLambdaWave=np.array([])
        self.vStep=-1
        #-----
        self.fitRoots=[]

    def addRefSpec(self,refSpecW,refSpecF):
        self.refSpecW=refSpecW
        self.refSpecF=refSpecF

    def addSpec(self,specW,specF):
        self.specW=specW
        self.specF=specF

    def cutInWaves(self,minWave,maxWave):
        if minWave>maxWave:
            print("maxWave must be greater than minWave")
            return

        l,r = np.searchsorted(self.refSpecW,minWave), np.searchsorted(self.refSpecW,maxWave)
        self.refSpecW = self.refSpecW[l:r]
        self.refSpecF = self.refSpecF[l:r]

        l,r = np.searchsorted(self.specW,minWave), np.searchsorted(self.specW,maxWave)
        self.specW = self.specW[l:r]
        self.specF = self.specF[l:r]

    def logLambdaResamble(self,vStep=-1):
        """ vStep [km/s]
        """
        if vStep == -1:
            vStep = scipy.constants.c/1000*min(self.specW[1]/self.specW[0]-1,self.refSpecW[1]/self.refSpecW[0]-1)
            vStep /= 4.23
        self.vStep = vStep
        r = vStep/(scipy.constants.c/1000)

        minWave=max(self.specW[0],self.refSpecW[0])
        maxWave=min(self.specW[-1],self.refSpecW[-1])
        n=int(np.log(maxWave/minWave)/np.log(1+r))
        if n%2 == 1:
            n-=1
        self.logLambdaWave=minWave*(1+r)**(np.arange(n))

    def interpolate(self):
        """ Interpoluje do self.logLambdaWave ale też wykonuje operacje fluxN=1.-flux
        """
        self.refFlux=1.-self.refSpecF
        self.flux=1.-self.specF

        self.refFlux=np.interp(self.logLambdaWave,self.refSpecW,self.refFlux)
        self.flux=np.interp(self.logLambdaWave,self.specW, self.flux)

    def crossCorrelate(self,maxlags=1000,normed=False):
        Nx=len(self.refFlux)
        lag = np.arange(-maxlags-1, maxlags)
        ccf=np.correlate(self.refFlux,self.flux, mode=2)
        if normed:
            ccf /= np.sqrt(np.dot(self.refFlux,self.refFlux ) * np.dot(self.flux,self.flux))
        self.ccf=ccf[Nx - 2 - maxlags:Nx + maxlags-1]
        self.velCCF=lag*self.vStep
        return self.velCCF, self.ccf


    def plotInterpolated(self):
        fig=plt.figure()
        plt.plot(self.logLambdaWave,self.flux,'k-')
        plt.plot(self.logLambdaWave,self.refFlux,'b-')

    def fitCCF(self,levels=[0.5,0.7,0.9],quiet=False):
        if self.velCCF == []:
            print("First compute CCF")
            return
        x=self.velCCF
        y=self.ccf
        return self.fit(x,y,levels,quiet=quiet)

    def fit(self,x,y,levels=[0.5,0.75,0.25],quiet=False):
        from scipy.interpolate import UnivariateSpline

        maxy = np.max(y)
        miny = np.min(y)
        self.fitRoots=[]
        for divide in levels:
            spline = UnivariateSpline(x, y-(maxy-miny)*divide-miny, s=0)
            roots = spline.roots() # find the roots
            if len(roots)!=2:
                print("ERROR: must be 2 roots on every level.")
                print("Redefine levels and run again")
                return
            r1,r2=roots
            self.fitRoots.append(roots)
        #---------
        print("SECTION MEAN  : ", np.mean(self.fitRoots))
        #PLOT:
        if not quiet:
            fig=plt.figure()
            for divide,(r1,r2) in zip(levels,self.fitRoots):
                plt.plot([r1,r2],[(maxy-miny)*divide+miny,(maxy-miny)*divide+miny],'k-')
                plt.plot([(r1+r2)/2,(r1+r2)/2],[(maxy-miny)*divide+miny-maxy/20,(maxy-miny)*divide+miny+maxy/20],'k-')
            plt.plot(x,y,'k-')

        return np.round(np.mean(self.fitRoots),1)

    def applyRadialVelocity(self,wave,flux,vrad):
        #vrad KM/S
        beta=vrad/299792.458
        wave*=np.sqrt((1+beta)/(1-beta))
        return wave,flux

    def getRadialVelocity(self,wave,flux,rWave,rFlux,\
                          minWave=None,maxWave=None,\
                          velocityMax=100,velocityStep=0.5,\
                          levels=[0.5,0.7,0.9],quiet=False):
        if wave is not None:
            self.addSpec(wave,flux)
            self.addRefSpec(rWave,rFlux)
        if minWave is not None and maxWave is not None:
            self.cutInWaves(minWave,maxWave)
        self.logLambdaResamble(velocityStep)
        self.interpolate()
        points = int(velocityMax/velocityStep)
        if not points%2: # Should be odd
            points+=1
        self.crossCorrelate(points)
        velocity = self.fitCCF(levels=levels,quiet=quiet)
        return velocity

def main():
    inFileR = "exampleData/53Per_average_HIDES_bestFit.txt"
    inFile = "exampleData/53Per_average_HIDES.txt"
    dfR=pd.read_table(inFileR,header=None, skiprows=0,delim_whitespace=True,comment='#')
    df=pd.read_table(inFile,header=None, skiprows=0,delim_whitespace=True,comment='#')

    waveCol=0
    fluxcol=1
    dfR=dfR.loc[dfR[fluxcol] != 0]
    df=df.loc[df[fluxcol] != 0]
    waveRef=np.array(dfR[waveCol])
    fluxRef=np.array(dfR[fluxcol])
    wave=np.array(df[waveCol])
    flux=np.array(df[fluxcol])

    radVel = RadialVelocity()
    radVel.getRadialVelocity(wave,flux,waveRef,fluxRef,\
                             minWave=4550,maxWave=4605,\
                             velocityMax=200,velocityStep=0.2)

    plt.show()

if __name__ == '__main__':
    main()
