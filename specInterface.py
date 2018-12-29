#!/usr/bin/python3
# -*- coding: utf-8 -*-

import time
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import gaussian, fftconvolve
import os
import subprocess

import pandas as pd
import multiprocessing as mp
import itertools
import collections

import bigGridInterface
from spectrum import Spectrum, readSpectrum, saveSpectrum

"""
DESCRIPTION

"""


class SynthesizeSpectrum:
    def __init__(self):

        self.grid = bigGridInterface.BigGridSynthesizer()

    def synthesizeSpectrum(self,parameters,minWave = 3500, maxWave = 7000):

        teff,logg,vmic,me,vsini,vmac,resolution = parameters
        # change units of metallicity, to units used in SYNSPEC
        me = 10**me

        spectrum = self.grid.interpolateSpectrum(teff,logg,me,vmic)

        # get anly needed range in wavelength
        mask = (minWave <= spectrum.wave ) & (spectrum.wave <= maxWave)
        spectrum.flux = spectrum.flux[mask]
        spectrum.wave = spectrum.wave[mask]

        # vsini and vmac CONVOLUTION
        spectrum.flux = self.addBroadeningToSpectrum(spectrum,vsini=vsini,vmac=vmac,limb_darkening_coeff=0.6)
        spectrum.vsini = vsini
        spectrum.vmac = vmac

        # instrumental broadening CONVOLUTION
        FWHM_before = spectrum.wave[1] - spectrum.wave[0]
        instrumentalFWHM = 5000. / resolution
        spectrum.flux = self.instrumentalSmooth(spectrum.flux,FWHM_before,instrumentalFWHM)

        return spectrum

    #---------------------------------------------------------------------------
    # VSINI, VMAC and instrumental broadening methods
    def instrumentalSmooth(self,flux,FWHM_before,FWHM_after):
        if FWHM_after < FWHM_before:
            print("FWHM can only grow. ",FWHM_before ,FWHM_after )
            return flux
        sigma = np.sqrt(FWHM_after**2 - FWHM_before**2)
        N_sigma = sigma/FWHM_before
        N = int(10*N_sigma)
        if not N%2:
            N += 1
        gaussianKernel = gaussian(N,std=N_sigma)
        gaussianKernel /= sum(gaussianKernel)

        smoothed = fftconvolve(1.0 - flux,gaussianKernel, mode='same')
        smoothed = 1.0 - smoothed

        return smoothed
    #FROM ISPEC
    #-----------------------------------------------------------------------
    def vmac_broadening(self, flux, velocity_step, vmac):
        """
        FROM ISPEC , S. Blanco-Cuaresma :
        #-----------------------------------------------------------------------
        velocity_step: fluxes should correspond to a spectrum homogeneously sampled in velocity space
                    with a fixed velocity step [km/s]
        vmac   : macroturbulence velocity [km/s]

        Based on SME's rtint
        It uses radial-tangential instead of isotropic Gaussian macroturbulence.
        """
        if vmac is not None and vmac > 0:
            # mu represent angles that divide the star into equal area annuli,
            # ordered from disk center (mu=1) to the limb (mu=0).
            # But since we don't have intensity profiles at various viewing (mu) angles
            # at this point, we just take a middle point:
            m = 0.5
            # Calc projected simga for radial and tangential velocity distributions.
            sigma = vmac/np.sqrt(2.0) / velocity_step
            sigr = sigma * m
            sigt = sigma * np.sqrt(1.0 - m**2.)
            # Figure out how many points to use in macroturbulence kernel
            nmk = max(min(round(sigma*10), (len(flux)-3)/2), 3)
            # Construct radial macroturbulence kernel w/ sigma of mu*vmac/sqrt(2)
            if sigr > 0:
                xarg = (np.arange(2*nmk+1)-nmk) / sigr   # exponential arg
                #mrkern = np.exp(max((-0.5*(xarg**2)),-20.0))
                mrkern = np.exp(-0.5*(xarg**2))
                mrkern = mrkern/mrkern.sum()
            else:
                mrkern = np.zeros(2*nmk+1)
                mrkern[nmk] = 1.0    #delta function

            # Construct tangential kernel w/ sigma of sqrt(1-mu**2)*vmac/sqrt(2.)
            if sigt > 0:
                xarg = (np.arange(2*nmk+1)-nmk) /sigt
                mtkern = np.exp(-0.5*(xarg**2))
                mtkern = mtkern/mtkern.sum()
            else:
                mtkern = np.zeros(2*nmk+1)
                mtkern[nmk] = 1.0

            ## Sum the radial and tangential components, weighted by surface area
            area_r = 0.5
            area_t = 0.5
            mkern = area_r*mrkern + area_t*mtkern

            # Convolve the flux with the kernel
            #start=time.time()
            flux_conv = 1 - fftconvolve(1-flux, mkern, mode='same') # Fastest
            #print("vmac convolve: ",time.time()-start)
            #import scipy
            #flux_conv = scipy.convolve(flux, mkern, mode='same') # Equivalent but slower

            return flux_conv
        else:
            return flux

    def lsf_rotate(self,deltav,vsini,epsilon=0.6):
        # Based on lsf_rotate.pro:
        #  http://idlastro.gsfc.nasa.gov/ftp/pro/astro/lsf_rotate.pro
        #
        # Adapted from rotin3.f in the SYNSPEC software of Hubeny & Lanz
        # http://nova.astro.umd.edu/index.html    Also see Eq. 17.12 in
        # "The Observation and Analysis of Stellar Photospheres" by D. Gray (1992)
        e1 = 2.0*(1.0 - epsilon)
        e2 = np.pi*epsilon/2.0
        e3 = np.pi*(1.0 - epsilon/3.0)

        npts = np.ceil(2*vsini/deltav)
        if npts % 2 == 0:
            npts += 1
        nwid = np.floor(npts/2)
        x = np.arange(npts) - nwid
        x = x*deltav/vsini
        x1 = np.abs(1.0 - x**2)

        velgrid = x*vsini
        return velgrid, (e1*np.sqrt(x1) + e2*x1)/e3
    def vsini_broadening_limbdarkening(self,flux, velocity_step, vsini, epsilon):
        """
            FROM ISPEC , S. Blanco-Cuaresma :
            #-----------------------------------------------------------------------
            velocity_step: fluxes should correspond to a spectrum homogeneously sampled in velocity space
                        with a fixed velocity step [km/s]
            vsini   : rotation velocity [km/s]
            epsilon : numeric scalar giving the limb-darkening coefficient,
                   default = 0.6 which is typical for  photospheric lines.

            Based on lsf_rotate.pro:
            http://idlastro.gsfc.nasa.gov/ftp/pro/astro/lsf_rotate.pro

            Adapted from rotin3.f in the SYNSPEC software of Hubeny & Lanz
            http://nova.astro.umd.edu/index.html    Also see Eq. 17.12 in
            "The Observation and Analysis of Stellar Photospheres" by D. Gray (1992)
        """
        if vsini is not None and vsini > 0:
            if epsilon is None:
                epsilon = 0.
            kernel_x, kernel_y = self.lsf_rotate(velocity_step, vsini, epsilon=epsilon)
            kernel_y /= kernel_y.sum()

            #-- convolve the flux with the kernel
            #start=time.time()
            flux_conv = 1 - fftconvolve(1-flux, kernel_y, mode='same') # Fastest
            #print("vsini convolve: ",time.time()-start)
            #import scipy
            #flux_conv = 1 - scipy.convolve(1-flux, kernel_y, mode='same') # Equivalent but slower
            return flux_conv
        else:
            return flux

    def determine_velocity_step(self,wave,flux):
        # FROM ISPEC , S. Blanco-Cuaresma :
        #-----------------------------------------------------------------------
        # Determine step size for a new model wavelength scale, which must be uniform
        # in velocity to facilitate convolution with broadening kernels. The uniform
        # step size is the largest of:
        wave_base = wave[0]
        wave_top = wave[-1]
        wmid = (wave_top + wave_base) / 2. # midpoint
        wspan = wave_top - wave_base # width
        # Light speed in vacuum
        #c = 299792458.0 # m/s
        c = 299792.4580 # km/s


        # [1] smallest wavelength step considering the wavelength sampling
        wave_diff = wave[1:] - wave[:-1]
        min_wave_step = np.min(wave_diff)
        min_wave_step_index = np.argmin(wave_diff)
        vstep1 = min_wave_step / (wave[min_wave_step_index] * c)

        # [2] 10% the mean dispersion
        vstep2 = 0.1 * wspan / len(wave) / (wmid * c)

        # [3] 0.05 km/s, which is 1% the width of solar line profiles
        vstep3 = 0.05e0

        # Select the largest between 1, 2 and 3:
        velocity_step = np.max((vstep1, vstep2, vstep3))

        return velocity_step

    def sampling_uniform_in_velocity(self,wave_base, wave_top, velocity_step):
        """
        FROM ISPEC , S. Blanco-Cuaresma :
        #-----------------------------------------------------------------------
        Create a uniformly spaced grid in terms of velocity:

        - An increment in position (i => i+1) supposes a constant velocity increment (velocity_step).
        - An increment in position (i => i+1) does not implies a constant wavelength increment.
        - It is uniform in log(wave) since:
              Wobs = Wrest * (1 + Vr/c)^[1,2,3..]
              log10(Wobs) = log10(Wrest) + [1,2,3..] * log10(1 + Vr/c)
          The last term is constant when dealing with wavelenght in log10.
        - Useful for building the cross correlate function used for determining the radial velocity of a star.
        """
        # Speed of light in km/s
        c = 299792.4580

        ### Numpy optimized:
        # number of elements to go from wave_base to wave_top in increments of velocity_step
        i = int(np.ceil( (c * (wave_top - wave_base)) / (wave_base*velocity_step)))
        grid = wave_base * np.power((1 + (velocity_step / c)), np.arange(i)+1)

        # Ensure wavelength limits since the "number of elements i" tends to be overestimated
        wfilter = grid <= wave_top
        grid = grid[wfilter]

        return np.asarray(grid)

    def addBroadeningToSpectrum(self,s,vsini=10,vmac=0,limb_darkening_coeff=0.6):
        """
            To given grid spectrum apply rotational broadening, macroturbulences and
            instrumental resolution smooth.
            --------------------------------------------------------------------
            Written with iSpec apply_post_fundamental_effects() function
        """
        flux=s.flux
        if (vmac is not None and vmac > 0) or (vsini is not None and vsini > 0):
            #prepare equal spacing in velocity
            wave_base = s.wave[0]
            wave_top = s.wave[-1]
            velocity_step = self.determine_velocity_step(s.wave,s.flux)
            waveobs_uniform_in_velocity = self.sampling_uniform_in_velocity(wave_base, wave_top, velocity_step)
            fluxes_uniform_in_velocity = np.interp(waveobs_uniform_in_velocity, s.wave, s.flux, left=0.0, right=0.0)

            # Apply broadening
            fluxes_uniform_in_velocity = self.vsini_broadening_limbdarkening(fluxes_uniform_in_velocity, velocity_step, vsini, limb_darkening_coeff)
            fluxes_uniform_in_velocity = self.vmac_broadening(fluxes_uniform_in_velocity, velocity_step, vmac)

            # Resample to origin wavelength grid
            flux = np.interp(s.wave, waveobs_uniform_in_velocity, fluxes_uniform_in_velocity)
        return flux


def testInterpolateSpectrum():
    bg = SynthesizeSpectrum()
    teff = 25100
    logg = 3.6
    me = 0.4
    vmic = 5
    vsini = 0
    vmac = 0
    resolution = 10000

    parameters = teff,logg,vmic,me,vsini,vmac,resolution
    start=time.time()
    s = bg.synthesizeSpectrum(parameters)
    end=time.time()
    print("TIME : ", end-start)
    plt.plot(s.wave,s.flux)
    plt.show()

def main():
    testInterpolateSpectrum()

if __name__ == '__main__':
	main()
