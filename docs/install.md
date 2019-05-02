# HANDY - Install

## Table of Contents
  * [Home](index.md)
  * [Install](install.md)
  * [Basics](basics.md)
  * [Regions and ranges](regions.md)
  * [Points](points.md)
  * [Radial velocity correction](radialVelocity.md)
  * [Grids](grids.md)
  
### Prerequisites

* Python3
* Conda - usefull but not necessary

### Download

Two steps:
* Clone the repository or download it as the .zip file:
  - Clone by:
    ```
    git clone https://github.com/RozanskiT/HANDY.git
    ```
  - Download zip from:
  [HANDY.zip](https://github.com/RozanskiT/HANDY/archive/master.zip)
* Download and untar folders with grids in your project catalog
  - Can be downloaded from : [Availible grids](https://drive.google.com/open?id=1VH5hQ5toTWuPFA_6vIpD1aZxs6u0nmia)
  
  It is a very good idea to create special directory with grids (eg. ~/grids/), keep all needed grids there, and only links those folders to HANDY main directory by:
    ```
    ln -s ~/grids/gridDirectoryName ~/path/to/HANDY/gridDirectoryName
    ```
  
### Installing

You need Python3 with all needed packages.

The easiest way to work with HANDY is with [Conda enviroment manager](https://conda.io/docs/user-guide/tasks/manage-environments.html#creating-an-environment-from-an-environment-yml-file):

Run in HANDY catalog:
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
After that you may want to make symbolic link in your ~/bin/ directory to HANDY.sh file to be able to easly run the program in whole system. Eg. on my system:
```
ln -s ~/repos/HANDY/HANDY.sh ~/bin/HANDY
```
Then you should be able to simply run the program by executing:
```
HANDY
```
in your terminal.

### Update

If you used git to install HANDY you can easy update HANDY just by pulling changes from remote:
```
git pull
```
Otherwise you need to re-install HANDY from newly downloaded .zip file.
