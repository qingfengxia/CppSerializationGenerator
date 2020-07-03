if(ENABLE_HDF5)
    # run command to generate _hdf5 header
    if(ENABLE_HDF5_GENERATOR)
        execute_process(
            COMMAND python3 ${PROJECT_SOURCE_DIR}/code_generator/h5type_generator.py "CodeGen_types.h"
            WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
        )
    endif()

    add_executable(CodeGen_demo
        CodeGen_demo.cpp
    )
    target_link_libraries(
        CodeGen_demo
        ${_hdf5_libs}
    )

endif()


if(ENABLE_XTENSOR)
    add_executable(demo_xtensor
        demo_xtensor.cpp
    )

endif()