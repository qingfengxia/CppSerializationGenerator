**generate H5Type for any C++ data class, clang's python binding.**

Copyright Qingfeng Xia @ UKAEA, 2020  
License:  same as RAMP

## Tutorial
Usage:  `h5type_generator.py input_header.h output_header_filename.h  NameSpaceName`

The generated header file `output_header_filename.h` declares a serial of `H5::CompType <class_name>_h5type` and `init_h5types();` in the original input header's same namespace. `init_h5types();` insert field type  def into those complex type declared.

### Demo
In  the folder <../demo/>, there are 3 files
+ CodeGen_types.h:  input header files, 2 classes defined.
+ CodeGen_types_hdf5.h  generated output header files,  H5::CompType instanced declared and initialized for the 2 classes in the input headers
+ CodeGen_demo.cpp :   how to use API in HDF5IO.h with `CodeGen_types_hdf5.h`
  + `init_h5types();`
  + init a  `std::vector<ComplexData>
  + write `WriteVector<ComplexData>`
  


### header, class and field requirement:
+ c-style struct/ C++ trivial-copyable data class  with public member will be saved
+ all classes in the input_header must be in a single namespace
+ generate header-only, but it can be split into h and cpp in the future
field type supported
+ all builtin scalar types like `int, double`
+ 1D fixed-size C-style array e.g. `int[3]`
+ std::string

=== yet completed or tested ===
+ Non-trivial C++ class with the help of the generated `serializer` function
+ C++ class with member of `std::vector, std::array`
+ string types:  C string `char*` and `std::string` hdf5 string type is special
+ For 2D matrix, using `Eigen::Matrix HDF5_Eigen`

## Future plan:
+ generate unit test 
+ serializer and deserializer functions
+ only generate h5 types for a selected
+ template class
+ filter class by hint in comment  `@to_hdf5`
+ QT types, which has property
+ for private fields: inject code into original class,  or derive class to expose 

https://github.com/cool-RR/PySnooper

### impl of Variable length member is highly challenging

https://stackoverflow.com/questions/35477590/reading-a-hdf5-dataset-with-compound-data-type-containing-multiple-sets-with-var

https://github.com/dguest/hdf5-ntuples/blob/master/include/h5container.hh

How to write `std::vector<EERAModel::particle>`
A solution would be declare a new struct to hold several `hvl_t` for all varLen fields:  "vector<T>,  T&, T* pointer ",  c_str is not nessary, the length can be detected by `\0` NUL char. 
inside the `<clsss_name>serialize()`, fill the vlen at the runtime. 
then write into a sibling data set.

To read: h5.py


>  To get the type that the `VarLenType` is based on, I can run DataType::getSuper().getClass().  Then to actually construct the type (for example, if it is a CompType), then I can use `DataType::getSuper().getClass().getId()` in the CompType constructor.


## Install dependencies

HDF5 C++ official API. `<H5Cpp.h>` see 
The python module `clang` is clang C API's official python binding.

A third-party header, "Eigen_HDF5.h" has been copied into this repo.

Install 
1. using pip `pip3 install clang`, you will also need to install `libclang-6`
To ensure the shared lib can be found, set the path by 
`Config.set_library_file("/usr/lib/llvm-6.0/lib/libclang.so.1")`
in `clang_util.py`

2. using linux software manager command line:  `apt install python3-clang`
then there may be no need to `Config.set_library_file()`

