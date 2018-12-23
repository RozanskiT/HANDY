# HANDY - Handy tool for spectra normalization

HANDY is interactive python3 program for spectrum normalization. The normalization process is based on "regions" and "ranges". "Ranges" are continuum parts defined manually by user (or uploaded from file from previous program run) which will be used for continuum level fit. "Regions" are groups of ranges for whom single chebyshev polynomial are fitted. Polynomial fits are connected with the use of Akima'a spline interpolation. The program offers graphical access to theoretical grid of spectra for obtaining an idea about processed star atmosphere parameters and interface for radial velocity correction. 

<p align="center">
  <a href="#key-features">Key Features</a> •
  <a href="#how-to-use">How To Use</a> •
  <a href="#how-to-use">How To Use</a> •
  <a href="#download">Download</a> •
  <a href="#credits">Credits</a> •
  <a href="#related">Related</a> •
  <a href="#license">License</a>
</p>

![Basic usage of HANDY](docsFiles/usageMovie1.gif)

## Key Features

* Interactive normalization of spectrum in single run
* Portability of continuum ranges between different spectra
* Easy access to precomputed grid of NLTE stars spectra (computed with SYNSPEC, with use of BSTAR2006 models)
  - NLTE line blanketed model atmospheres of hot stars. I. Hybrid Complete Linearization/Accelerated Lambda Iteration Method, 1995, Hubeny, I., & Lanz, T., Astrophysical Journal, 439, 875
* Radial velocity correction 
* Developed and tested on Linux


## Getting Started

### Prerequisites

* Python3
* Conda - usefull but not necessary

### Download

Two steps:
* Clone the repository or download it as the .zip file
* Download and untar folder with grid into your project catalogue
  - Can be downloaded from : https://drive.google.com/open?id=1HoGdsCiT7-sRO5a_YqBjVRrTetkxNvwg
  
### Installing

You need python3 with all needed packages.

The easiest way to work with HANDY is with [Conda enviroment manager](https://conda.io/docs/user-guide/tasks/manage-environments.html#creating-an-environment-from-an-environment-yml-file):

Run in HANDY folder:
```
conda env create -f environment.yml
```
Activate the HANDY-env enviroment:
```
source activate HANDY-env
```
Verify if enviroment is installed correctly:
```
conda list
```

## Deployment

Add additional notes about how to deploy this on a live system


## License

This project is licensed under the MIT License - see the [LICENSE.txt](LICENSE.txt) file for details

## Acknowledgments

* Hat tip to anyone whose code was used
* Inspiration
* etc
<!---
-->
