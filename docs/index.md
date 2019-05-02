# HANDY - Handy tool for spectra normalization

HANDY is interactive Python3 program for spectrum normalization. The normalization process is based on "regions" and "ranges". "Ranges" are continuum parts defined manually by user (or uploaded from file from previous program run) which will be used for continuum level fit. "Regions" are groups of ranges for whom single chebyshev polynomial of chosen order is fitted. Polynomial fits are connected with the use of Akima'a spline interpolation. The program offers graphical access to theoretical grid of spectra for obtaining an idea about processed star atmosphere parameters and interface for radial velocity correction. Different grids of spectra can be easly added by the user.

## Table of Contents
  * [Home](index.md)
  * [Install](install.md)
  * [Basics](basics.md)
  * [Regions and ranges](regions.md)
  * [Points](points.md)
  * [Radial velocity correction](radialVelocity.md)
  * [Grids](grids.md)

![Basic usage of HANDY](img/typicalUse.gif)

## Key Features

* Interactive normalization of spectrum in single run
* Portability of continuum ranges between different spectra
* Easy access to precomputed grid of NLTE stars spectra (computed with SYNSPEC, with use of BSTAR2006 models)
  - NLTE line blanketed model atmospheres of hot stars. I. Hybrid Complete Linearization/Accelerated Lambda Iteration Method, 1995, Hubeny, I., & Lanz, T., Astrophysical Journal, 439, 875
* Adding user defined grids
* Radial velocity correction
* Developed and tested on Linux
* Easy installation and easy to use
