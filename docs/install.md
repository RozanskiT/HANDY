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
* Conda - recommended but not necessary

### Download

Two steps:
* Clone the repository or download it as the .zip file:
  - Clone by:
    ```
    git clone https://github.com/RozanskiT/HANDY.git
    ```
  - Download zip from:
  [HANDY-master.zip](https://github.com/RozanskiT/HANDY/archive/master.zip)
* Download and untar folders with grids in your project catalog, eg. `~/repos/HANDY/`
  - Can be downloaded from : [Grids](https://drive.google.com/open?id=1VH5hQ5toTWuPFA_6vIpD1aZxs6u0nmia)

### Installing
### HANDY
You need Python3 with all needed packages.

The easiest way to work with HANDY is with [Conda enviroment manager](https://conda.io/docs/user-guide/tasks/manage-environments.html#creating-an-environment-from-an-environment-yml-file):

Run in HANDY catalog, eg. `~/repos/HANDY/`:
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
### VidmaPy

Now you have to clone submodule VidmaPy by calling (from HANDY catalogue):
```
git submodule update --init
```
It should clone the vidmapy in to HANDY/vidmapy. The next step is the installation of VidmaPy that enable HANDY to use ATLAS/SYNTHE. To install the vidmapy in HANDY-env environment (you want that), you need to follow the description from VidmaPy [README](https://github.com/RozanskiT/vidmapy).

Shortly speaking:

* download [atomic data](https://drive.google.com/drive/folders/1H-lFH69fyWvwWydgO8uBS3TIAdZ9hWdc?usp=sharing) and place in directory (three distinct directories: ODF, molecules, and lines):
```
HANDY-extended/vidmapy/vidmapy/kurucz/atomic_data/
```
* run from HANDY/vidmapy directory:
```
pip install .
```

### Finally

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
