#include "HDF5IO.h"

#include "CodeGen_types_hdf5.h"
using namespace CodeGen;

#include <cassert> // will be disabled if NDEBUG macro is defined

// https://support.hdfgroup.org/HDF5/doc/cpplus_RM/compound_8cpp-example.html

#define H5FILE_NAME "DS_CodeGen.h5"
#define DS_NAME "DataStruct"

void test_h5(std::shared_ptr<H5File> file)
{
    std::vector<CDataStruct> values;
    CDataStruct v1 = {1, 2.3, {1.0, 2.0, 3.0}};   // Aggregate initialization in C++17
    CDataStruct v2 = {10, 23.0, {4.0, 5.0, 6.0}}; // Aggregate initialization in C++17
    values.push_back(v1);                         // Aggregate initialization inside push_back() needs C++17
    values.push_back(v2);

    std::vector<ComplexData> cvalues;
    // Aggregate initialization inside push_back() needs C++17

#if DATA_USE_COMPLEX_FIELDS
    ComplexData cd1(1.0, v1, "std_string1", {1.1, 2.2, 3.2}, {1, 2});

    ComplexData cd2(2.0, v2, "std_string_value2", {4.4, 5.5, 6.6}, {1, 2, 3, 4});
#else
    ComplexData cd1(1.0, v1); // = {1.0, {1, 2, 3}, "complex", v1};
    ComplexData cd2(2.0, v2); //  = {2.0, {4, 5, 6}, "complex", v2};
#endif
    cvalues.push_back(cd1);
    cvalues.push_back(cd2);

    // std::array<> is trivially-copyable, so it is working
    data::IO::WriteAttribute<CDataStruct>(v1, file, "simple_data_attrib");

#if DATA_USE_COMPLEX_FIELDS
    data::IO::WriteVector<ComplexData>(cvalues, file, "complex_data");
    // writing is correct, but ReadVector() still fail
    // auto cv = data::IO::ReadVector<ComplexData>(file, "complex_data",
    //                                              ComplexData_deserialize);
    // for (const ComplexData &v : cv)
    // {
    //     std::cout << v.ds.integer << std::endl;
    // }
#else
    data::IO::WriteVector<ComplexData>(cvalues, file, "complex_data", ComplexData_h5type);
#endif

    std::vector<std::string> lines = {"line1", "line2"};
    data::IO::writeStringVectorAttribute(file.get(), "vector_of_string", lines);

    std::vector<std::vector<int>> mat = {{1, 2, 3}, {4, 5, 6}};
    data::IO::WriteMatrix<int>(mat, file, "IntMatrix");

    auto m = data::IO::ReadMatrix<int>(file, "IntMatrix");
    assert(m.size() == 2);

#if DATA_USE_EIGEN

    Eigen::Matrix3d emat;
    emat << 1, 2, 3, 4, 5, 6, 7, 8, 9;

    /// directly use EigenHDF5::save,  it is working
    EigenHDF5::save(*file, "EigenMatrixDataSet", emat); // first param is a reference  type

    // still some compiling error, anyway, just use EigenHDF5::save
    //data::IO::WriteEigen(emat, *file, "EigenMatrix");
    //auto em = data::IO::ReadEigen<Eigen::Matrix3d>(*file, "EigenMatrix");
#endif
}

int main()
{
    /// this part demo model result writting into HDF5
    std::shared_ptr<H5File> file = std::make_shared<H5File>(H5FILE_NAME, H5F_ACC_TRUNC);
    init_h5types();
    //test_vlen(file);  // error
    test_h5(file);

    file->close();
    std::cout << "HDF5 serialization demo completed successfully\n";
}