# C++ code generator for C++ data class serialization using clang's python binding

Copyright Qingfeng Xia 2020-2021
License: BSD 3-clause

## Introduction

Class definition in C++ header is parsed by clang, and glue code will be generated automatically.

This project is not completed, as only HDF5 serialization (no deserialization) has been implemented.

## Modular design

Module is selected from CMake "ENABLE_*" options

### Implemented C++ class serialization file format

HDF5: official cpp  API "H5Cpp.h"

HDF5 is most complicated file format, if this format is supported, other serialization data format like json will be fairly straight-forwrard.

### Potential module (serialization file format) to support

+ yaml: 
+ json.hpp header only C++ json: extensible to decode/encode user types
+ toml11: header only lib: https://github.com/ToruNiina/toml11#converting-a-table
+ xml: 


Tabular data/DataFrame
+ csv: header only https://github.com/vincentlaucsb/csv-parser#single-header

A more advanced C++ lib for data table as in R Table or Pandas.DataFrame
+ [xframe, towards a C++ dataframe](https://medium.com/@johan.mabille/xframe-towards-a-c-dataframe-26e1ccde211b)
+ <https://github.com/hosseinmoein/DataFrame>

### Third-party code included

Some header only libraries are downloaded and copied into this repository for the moment.  `git submodule add -b master https://github.com/ToruNiina/toml11.git`

+ [json.hpp](https://github.com/nlohmann/json): MIT licensed,  download as a copy
+ toml.hpp:    git submodule 
+ csv.hpp: download as a copy
+ [eigen3-hdf5.hpp](https://github.com/garrison/eigen3-hdf5): MIT licensed, download as a copy, with modification

### Module code structure

+ hdf5/HDF5IO.h:  helper functions to ease HDF5 IO
+ hdf5/HDF5_TypeTraits.h: 
+ demo/CodeGen_Types.h:  input testing class def
+ demo/hdf5 :  demo the usage of code generator for hdf5 IO

+ code_generator/hdf5_generator : an independent python code generation script

+ tests/ : unit tests


## HDF5



### Tutorial for HDF5
Usage:  `h5type_generator.py input_header.h output_header_filename.h  NameSpaceName`

The generated header file `output_header_filename.h` declares a serial of `H5::CompType <class_name>_h5type` and `init_h5types();` in the original input header's same namespace. `init_h5types();` insert field type  def into those complex type declared.

### Demo
In  the folder <../demo/>, there are 3 files
+ CodeGen_types.h:  input header files, 2 classes defined.
+ CodeGen_types_hdf5.h  generated output header files,  H5::CompType instanced declared and initialized for the 2 classes in the input headers
+ CodeGen_demo_hdf5.cpp :   how to use API in HDF5IO.h with `CodeGen_types_hdf5.h`
  + `init_h5types();`
  + init a  `std::vector<ComplexData>
  + write `WriteVector<ComplexData>`
  


### header, class and field requirement:
+ c-style struct/ C++ trivially-copyable data class  with public member will be saved
+ all classes in the input_header must be in a single namespace
+ generate header-only, but it can be split into h and cpp in the future
field type supported
+ all built-in scalar types like `int, double`
+ 1D fixed-size C-style array e.g. `int[3]`
+ `std::string`

=== non-trivially-copyable class need more tests ===

+  `std::vector, std::array`
+ For 2D matrix, using `Eigen::Matrix HDF5_Eigen`

=== yet completed or tested ===

+ Non-trivial C++ class with the help of the generated `serializer` function
+ string types:  C string `char*` and `std::string` hdf5 string type is special



### HDF5 support for Variable length member is highly challenging

https://stackoverflow.com/questions/35477590/reading-a-hdf5-dataset-with-compound-data-type-containing-multiple-sets-with-var

https://github.com/dguest/hdf5-ntuples/blob/master/include/h5container.hh

How to write `std::vector<EERAModel::particle>`
A solution would be declare a new struct to hold several `hvl_t` for all varLen fields:  "vector<T>,  T&, T* pointer ",  c_str is not nessary, the length can be detected by `\0` NUL char. 
inside the `<clsss_name>serialize()`, fill the vlen at the runtime. 
then write into a sibling data set.

To read: h5.py


>  To get the type that the `VarLenType` is based on, I can run DataType::getSuper().getClass().  Then to actually construct the type (for example, if it is a CompType), then I can use `DataType::getSuper().getClass().getId()` in the CompType constructor.


### Install dependencies

HDF5 C++ official API. `<H5Cpp.h>` see 
A third-party header, "Eigen_HDF5.h" has been copied into this repo.



The currently **workflow** for HDF5 IO (manual workflow)
+ copy all classes to written into HDF5,  e.g.  `particle` or later more general result c++ class type, into a header file `EERA_types.h`, as input to the `hdf5_generator.py`

+ `hdf5_generator.py` is a python code generator, aiming to generate H5:CompType instance for almost any C++ class
 see more in <code_generator/Readme.md>

+ `HDF5IO.h`  read and write any class with the generated H5:CompType instance in the generated `*_types_hdf5.h`

`HDF5IO.h` is a head-only lib, just put `include/` and `third-party/` of this repo as `include_directories()` in specific model project cmake, it should work. 

The workflow can be automated by cmake.




### HDF5 C++ libraries

1. Official C++ API
   	There are official C API and C++ wrapper `H5CPP`. 
   	**H5CPP is now MPI capable given c++17 capable MPI compiler**

	HDF5 v1.8 has significantly difference with HDF5 v1.10
   	https://support.hdfgroup.org/HDF5/doc/ADGuide/Changes.html

	For Eigen::Matrix support
	https://github.com/garrison/eigen3-hdf5  does not work with HDF5 1.10
	https://github.com/Gjacquenot/eigen3-hdf5 works with HDF5 1.10

2. HighFive  Header-only
	https://github.com/BlueBrain/HighFive
	 with `T[][], boost::ublas, Eigen::Matrix, XTensor` support

3. Eigen, Xtensor

### HDF5 file viewer on Ubuntu 18.04/20.04

Ubuntu 18.04 's **hdfview** from official repository has bug, it can not view the data.

`pip install h5pyViewer`  but it is python2 only, not updated since 2015.

On ubuntu 18.04 `pip3 install vitables` also have some problem, pip3 can not install PyQt5,  even  after PyQt5 has been installed from system package manager,  pip3 seems does not find it,  so I download vitables.3.0.2 source code,  comment out 2 lines in `setup.py` and install it.  On ubuntu 18.04, `vitables` can be installed by `apt-get`

Command line tool `h5dump` is working to check h5 data structure.



## Installation

This is C++ API is designed to be header-only, while dependency libraries need to be installed, see guide below. This API can be used  as a git submodule, or just copy this repo folder into specific model project, and then include this folder in the project root `CMakeLists.txt`.

Or git clone this repo as the sibling folder of model repo,it is just header include dictionary to be sorted out in CMake

note: as git module is used, add `--recursive`when clone this repo, i.e. `git clone --recursive this_repo`. read more on using submodule: <https://www.vogella.com/tutorials/GitSubmodules/article.html>

### Install clang's python binding

The python module `clang` is clang C API's official python binding.
Install either from

1. using pip `pip3 install clang`, you will also need to install `libclang-6`
   To ensure the shared lib can be found, set the path by 
   `Config.set_library_file("/usr/lib/llvm-6.0/lib/libclang.so.1")`
   in `clang_util.py`

2. using linux software manager command line:  `apt install python3-clang`
   then there may be no need to `Config.set_library_file()`



### Install HDF5 dependency on Ubuntu 18.04/20.04

`sudo apt install libhdf5-dev`
optional: 
`sudo apt install libeigen3-dev`

### RHEL/Centos 7
Centos versions are older than Ubuntu, sometimes versions cause trouble.
poco-devel-1.6.1-3.el7.x86_64.rpm
hdf5-devel-1.8.12-11.el7.x86_64.rpm
`yum install epel-release -y && yum install  cmake3 hdf5-devel -y`

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



## Future plan:

+ generate unit test 
+ serializer and deserializer functions
+ only generate h5 types for a selected
+ template class
+ filter class by hint in comment  `@to_hdf5`
+ QT types, which has property meta data
+ for private fields: inject code into original class,  or derive class to expose 

https://github.com/cool-RR/PySnooper



## **Note on license and copyright**

This repo starts as a personal trial of `code_generator` in the author's non-office hours when participating the BSD 3-clause project <https://github.com/ScottishCovidResponse/data_pipeline_api_cpp/>.  This `code_generator` was not a completed project yet, but it will be developed in the author's personal github to be some kind of usefulness.