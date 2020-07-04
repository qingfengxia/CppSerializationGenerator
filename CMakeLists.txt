cmake_minimum_required(VERSION 2.8 FATAL_ERROR)

project(cpp_code_generator)

enable_language(CXX)

option(ENABLE_HDF5 "Enable HDF5 support" ON)
#option(ENABLE_HDF5_GENERATOR "Enable python genetor to gen HDF5 types" OFF)
option(ENABLE_TOML "Enable toml  support" ON)
option(ENABLE_JSON "Enable json  support" ON)
option(ENABLE_XML "Enable xml  support" ON)

option(ENABLE_XTENSOR "Enable Xtensor support for multidimension array" OFF)
option(ENABLE_EIGEN "Enable Eigen vector and matrix support" ON)
#option(ENABLE_NETWORKING "Enable RESTFUL network get and put support" OFF)

option(ENABLE_CODE_COVERAGE "Enable coverage reporting" OFF)
option(ENABLE_DEMO "use demo module" ON)
option(ENABLE_TEST "use unit test module" OFF)

######################################################
# for json.hpp, catch.h
include_directories("${CMAKE_CURRENT_SOURCE_DIR}/third-party")
# header-only library toml11 as submodule in third-party folder

##############################################################
# supply env variable to cmake for other parameters:  `CXX=clang++  cmake ..`
# std can and should be applied to target only, here is the default C++11
if (NOT  CMAKE_CXX_STANDARD)
    set(CMAKE_CXX_STANDARD 14)
endif()
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if (NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Debug)
endif()

## put all targets in bin and lib
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${PROJECT_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${PROJECT_BINARY_DIR}/lib)
link_directories(${CMAKE_LIBRARY_OUTPUT_DIRECTORY})

##########################################################

if(ENABLE_CODE_COVERAGE AND CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
	message(STATUS "Including Code Coverage")
	set(COVERAGE_COMPILER_FLAGS "-g -fprofile-arcs -ftest-coverage")
	set(CMAKE_CXX_FLAGS "${COVERAGE_COMPILER_FLAGS} ${CMAKE_CXX_FLAGS}")
endif()


# adapted from https://github.com/bast/hdf5-cmake-example/blob/master/CMakeLists.txt
#  https://cmake.org/cmake/help/v3.6/module/FindHDF5.html
if(ENABLE_HDF5)
    # HL: high-level API: Table, Image data structure
    # NOTE: CXX not CPP for C++ in cmake lang naming
    # prefer serial if both serial and parallel versions are found
    # setting the variable HDF5_PREFER_PARALLEL to true, before FIND_PACKAGE()
    FIND_PACKAGE(HDF5 COMPONENTS C CXX HL REQUIRED)
    if(HDF5_FOUND)
        message(STATUS "Found HDF5 version ${HDF5_VERSION}, ${HDF5_CXX_LIBRARIES}, ${HDF5_C_LIBRARIES}")
        include_directories(${HDF5_INCLUDE_DIR})
        link_directories(${HDF5_INCLUDE_DIRS})  # it is not installed to default lib folder
        set(_hdf5_libs ${HDF5_C_LIBRARIES})
        list(APPEND _hdf5_libs ${HDF5_CXX_LIBRARIES})
        list(APPEND _hdf5_libs ${HDF5_CXX_HL_LIBRARIES})
    else()
        # we did not find it so we fetch it from the web, configure, compile, and link
        # not tested!!!
        include(ExternalProject)
        set(ExternalProjectCMakeArgs
            -DHDF5_BUILD_CPP_LIB=ON
            )
        # need to check the download link to find out the current/latest version
        set(_hdf5_version "1.10.5")  # Ubuntu 18.04 -> version 1.10.0.1
        # for the download and local built, must link to the static lib, not shared
        file(MAKE_DIRECTORY ${PROJECT_BINARY_DIR}/hdf5_local/src)
        ExternalProject_Add(hdf5_local
            DOWNLOAD_COMMAND curl http://www.hdfgroup.org/ftp/HDF5/current/src/hdf5-${_hdf5_version}.tar.gz | tar xvz -C ${PROJECT_BINARY_DIR}/hdf5_local/src
            CMAKE_ARGS ${ExternalProjectCMakeArgs}
            SOURCE_DIR ${PROJECT_BINARY_DIR}/hdf5_local/src/hdf5-${_hdf5_version}
            BINARY_DIR ${PROJECT_BINARY_DIR}/hdf5_local/build
            STAMP_DIR  ${PROJECT_BINARY_DIR}/hdf5_local/stamp
            TMP_DIR    ${PROJECT_BINARY_DIR}/hdf5_local/tmp
            INSTALL_COMMAND ""
            )
        include_directories(
            ${PROJECT_BINARY_DIR}/hdf5_local/src/hdf5-${_hdf5_version}/src
            ${PROJECT_BINARY_DIR}/hdf5_local/src/hdf5-${_hdf5_version}/c++/src
            ${PROJECT_BINARY_DIR}/hdf5_local/build
            )
        set(_hdf5_libs
            ${PROJECT_BINARY_DIR}/hdf5_local/build/bin/libhdf5_cpp.a
            ${PROJECT_BINARY_DIR}/hdf5_local/build/bin/libhdf5.a
            -ldl
            )
    endif()
endif()

##############################################################

if(ENABLE_EIGEN)
    find_package(Eigen3 NO_MODULE)
    if(EIGEN3_FOUND)
        message("found Eigen version: ${EIGEN3_VERSION}")
        include_directories(${EIGEN3_INCLUDE_DIRS})
        add_definitions("-DDATA_USE_EIGEN")
    else()
    message(" Eigen3 lib not found, optional feature will not be compiled")
        ## may download to third-party from git
    endif()
endif()

# the sequence of include_directories() and add_subdirectory() is crucial
if(ENABLE_XTENSOR)
    #if not exist, download by git submodule

    if( NOT EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/third-party/xtl")
    execute_process(
        COMMAND git submodule add https://github.com/xtensor-stack/xtl
        WORKING_DIRECTORY {PROJECT_SOURCE_DIR}/third-party
    )
    endif()
    if( NOT EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/third-party/xtensor")
    execute_process(
        COMMAND git submodule add https://github.com/xtensor-stack/xtensor
        WORKING_DIRECTORY {PROJECT_SOURCE_DIR}/third-party
    )
    endif()
    add_definitions("-DDATA_USE_XTENSOR")
    include_directories("${CMAKE_CURRENT_SOURCE_DIR}/third-party/xtl/include")
    include_directories("${CMAKE_CURRENT_SOURCE_DIR}/third-party/xtensor/include")
    message(STATUS "header-only lib xtensor has been enabled for this project"
        "as git submodule at `${CMAKE_CURRENT_SOURCE_DIR}/third-party/xtensor`")

endif()

if(ENABLE_TOML)
    if( NOT EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/third-party/toml11")
    execute_process(
        COMMAND git submodule add https://github.com/ToruNiina/toml11
        WORKING_DIRECTORY {PROJECT_SOURCE_DIR}/third-party
    )
    endif()
endif()

# either use the download single header or download the latest by git submodule
if(ENABLE_JSON  AND NOT EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/third-party/json.hpp")
    if( NOT EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/third-party/json")
    execute_process(
        COMMAND git submodule add https://github.com/nlohmann/json/
        WORKING_DIRECTORY {PROJECT_SOURCE_DIR}/third-party
    )
    endif()
    include_directories("${CMAKE_CURRENT_SOURCE_DIR}/third-party/json/single_include/nlohmann")
endif()

if(ENABLE_HDF5)
    include_directories("${CMAKE_CURRENT_SOURCE_DIR}/hdf5")
    add_definitions("-DDATA_USE_HDF5_GENERATOR")
    # run command to generate some code
endif()

if(ENABLE_DEMO)
    include_directories("${CMAKE_CURRENT_SOURCE_DIR}/demo")  # shared header files for demo
    add_subdirectory("demo")
endif()

if(ENABLE_TEST)
    add_subdirectory(tests)  # disable it since there is compiling error
endif()