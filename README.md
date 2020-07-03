# Code generator for C++ using python clang

The currently **workflow** for HDF5 IO (manual workflow)
+ copy all classes to written into HDF5,  e.g.  `particle` or later more general result c++ class type, into a header file `EERA_types.h`, as input to the `hdf5_generator.py`

+ `hdf5_generator.py` is a python code generator, aiming to generate H5:CompType instance for almost any C++ class
 see more in <code_generator/Readme.md>

+ `HDF5IO.h`  read and write any class with the generated H5:CompType instance in the generated `*_types_hdf5.h`

`HDF5IO.h` is a head-only lib, just put `include/` and `third-party/` of this repo as `include_directories()` in specific model project cmake, it should work. 

The workflow can be automated by cmake.



## Third-party library selection

+ HDF5: for simulation result packing


+ yaml: 
+ json.hpp header only C++ json: extensible to decode/encode user types
+ toml11: header only lib: https://github.com/ToruNiina/toml11#converting-a-table


+ csv: header only https://github.com/vincentlaucsb/csv-parser#single-header

A more advanced C++ lib for data table as in R Table or Pandas.DataFrame
+ [xframe, towards a C++ dataframe](https://medium.com/@johan.mabille/xframe-towards-a-c-dataframe-26e1ccde211b)
+ <https://github.com/hosseinmoein/DataFrame>

### HDF5 C++ libraries

1. Official C++ aPI
   	There are official C API and C++ wrapper `H5CPP`. 
   	**H5CPP is now MPI capable given c++17 capable MPI compiler**

	HDF5 v1.8 has significantly difference with HDF5 v1.10
   	https://support.hdfgroup.org/HDF5/doc/ADGuide/Changes.html

	For Eigen::Matrix support
	https://github.com/garrison/eigen3-hdf5  does not work with HDF5 1.10
	https://github.com/Gjacquenot/eigen3-hdf5 works with HDF5 1.10

2. HighFive
	https://github.com/BlueBrain/HighFive
	Header-only, with `T[][], boost::ublas, Eigen::Matrix, XTensor` support

### HDF5 file viewer on Ubuntu 18.04/20.04

Ubuntu 18.04 's **hdfview** from official repository has bug, it can not view the data.

`pip install h5pyViewer`  but it is python2 only, not updated since 2015.

On ubuntu 18.04 `pip3 install vitables` also have some problem, pip3 can not install PyQt5,  even  after PyQt5 has been installed from system package manager,  pip3 seems does not find it,  so I download vitables.3.0.2 source code,  comment out 2 lines in `setup.py` and install it.  On ubuntu 18.04, `vitables` can be installed by `apt-get`

Command line tool `h5dump` is working to check h5 data structure.

## Installation

This is C++ API is designed to be header-only, while dependency libraries need to be installed, see guide below. This API can be used  as a git submodule, or just copy this repo folder into specific model project, and then include this folder in the project root CMakeLists.txt.
Or git clone this repo as the sibling folder of model repo, e.g. `EERAModel`, it is just header include directionary to be sorted out in CMake

note: as git module is used, add `--recursive`when clone this repo, i.e. `git clone --recursive this_repo`. read more on using submodule: <https://www.vogella.com/tutorials/GitSubmodules/article.html>


### Code structure


+ include/HDF5IO.h:  helper functions to ease HDF5 IO

+ code_generator/ : an independent python code generation script
+ demo/ :  demo the usage of code generator for hdf5 IO
+ tests/ : unit tests

Some header only libraries are downloaded and copied into this repository for the moment.  `git submodule add -b master https://github.com/ToruNiina/toml11.git`
+ json.hpp   download as a copy
+ toml.hpp    git submodule 
+ csv.hpp  download as a copy
+ eigen3-hdf5.hpp  download as a copy, with modification

### Install dependency on Ubuntu 18.04/20.04

`sudo apt install libssl-dev, libpoco-dev, libhdf5-dev`
optional: 
`sudo apt install libeigen3-dev`

### RHEL/Centos 7
Centos versions are older than Ubuntu, sometimes versions cause trouble.
poco-devel-1.6.1-3.el7.x86_64.rpm
hdf5-devel-1.8.12-11.el7.x86_64.rpm
`yum install epel-release -y && yum install poco-devel openssl-devel cmake3 hdf5-devel -y`

optional: `yum install install eigen3-devel`

This project's cmake can download and build latest HDF5 lib in local build folder. 

#### MacOS 
homebrew maybe is the way to go. The dependencies name and version can be checked online
https://formulae.brew.sh/formula/

If brew is not installed yet, run `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"`

Install dependencies: `brew update && brew install eigen  hdf5`

On macos-latest (?), the default HDF5 version is 1.12. It is possible to install `hdf5@1.10`, but cmake failed to find it, version 1.12 is used.

cmake could not find OpenSSL installation, however, networking code has been turn off, will be removed later.

###  build with cmake

Only 2 demo cpp to test out platform cmake configuration. 


