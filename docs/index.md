# HANDY - Handy tool for spectra normalization

HANDY is interactive Python3 program for spectrum normalization. The normalization process is based on "regions" and "ranges". "Ranges" are continuum parts defined manually by user (or uploaded from file from previous program run) which will be used for continuum level fit. "Regions" are groups of ranges for whom single chebyshev polynomial of chosen order is fitted. Polynomial fits are connected with the use of Akima'a spline interpolation. The program offers graphical access to theoretical grid of spectra for obtaining an idea about processed star atmosphere parameters and interface for radial velocity correction. Different grids of spectra can be easly added by the user. 

### Adding new grid
* Compute your new grid (equally spaced in each dimension) in chosen number of parameters from among effective temperature, surface gravity, metallicity and microturbulence velocity. Code paramters of each spectrum in its file name. Your grid files can be of two types:
  - with wavelength and flux columns in each file,
  - only with flux column in each grid file but with common wavelength file,
* Define your grid in gridsDefinitions.yaml. This file is self explanatory.
* It's done!

### Play with regions end ranges creation/deletion

* Left mause button - create ranges
* Right mouse button - remove the neares range
* Scroll wheel click - change active region to the nearest to cursor 
