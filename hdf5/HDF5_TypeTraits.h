/// this header file adapted form eigen3_hdf5.h
/// https://github.com/garrison/eigen3-hdf5
/// MIT license.

#pragma once

#include <complex>
#include <cstddef>
#include <cassert>
#include <string>
#include <vector>
#include <functional>

#include <H5Cpp.h>

namespace HDF5
{
    /// TODO: apply constness to the input parameter `const T& `
    template <class T>
    using Serializer = std::function<void(T &, H5::DataSet &, const H5::DataSpace *, const H5::DataSpace *)>;
    template <class T>
    using Deserializer = std::function<T(H5::DataSet &, const H5::DataSpace *, const H5::DataSpace *)>;

    template <typename T>
    struct to_h5serializer
    {
        static inline const Serializer<T> get(void)
        {
            return nullptr;
        }
    };

    template <typename T>
    struct to_h5deserializer
    {
        static inline const Deserializer<T> get(void)
        {
            return nullptr;
        }
    };

    template <typename T>
    struct to_h5type;

    // floating-point types

    template <>
    struct to_h5type<float>
    {
        static inline const H5::DataType *get(void)
        {
            return &H5::PredType::NATIVE_FLOAT;
        }
    };

    template <>
    struct to_h5type<double>
    {
        static inline const H5::DataType *get(void)
        {
            return &H5::PredType::NATIVE_DOUBLE;
        }
    };

    template <>
    struct to_h5type<long double>
    {
        static inline const H5::DataType *get(void)
        {
            return &H5::PredType::NATIVE_LDOUBLE;
        }
    };

    // integer types
    template <>
    struct to_h5type<char>
    {
        static inline const H5::DataType *get(void)
        {
            return &H5::PredType::NATIVE_CHAR;
        }
    };

    template <>
    struct to_h5type<unsigned char>
    {
        static inline const H5::DataType *get(void)
        {
            return &H5::PredType::NATIVE_UCHAR;
        }
    };

    template <>
    struct to_h5type<short>
    {
        static inline const H5::DataType *get(void)
        {
            return &H5::PredType::NATIVE_SHORT;
        }
    };

    template <>
    struct to_h5type<unsigned short>
    {
        static inline const H5::DataType *get(void)
        {
            return &H5::PredType::NATIVE_USHORT;
        }
    };

    template <>
    struct to_h5type<int>
    {
        static inline const H5::DataType *get(void)
        {
            return &H5::PredType::NATIVE_INT;
        }
    };

    template <>
    struct to_h5type<unsigned int>
    {
        static inline const H5::DataType *get(void)
        {
            return &H5::PredType::NATIVE_UINT;
        }
    };

    template <>
    struct to_h5type<long>
    {
        static inline const H5::DataType *get(void)
        {
            return &H5::PredType::NATIVE_LONG;
        }
    };

    template <>
    struct to_h5type<unsigned long>
    {
        static inline const H5::DataType *get(void)
        {
            return &H5::PredType::NATIVE_ULONG;
        }
    };

    template <>
    struct to_h5type<long long>
    {
        static inline const H5::DataType *get(void)
        {
            return &H5::PredType::NATIVE_LLONG;
        }
    };

    template <>
    struct to_h5type<unsigned long long>
    {
        static inline const H5::DataType *get(void)
        {
            return &H5::PredType::NATIVE_ULLONG;
        }
    };

    // complex types
    //
    // inspired by http://www.mail-archive.com/hdf-forum@hdfgroup.org/msg00759.html

    template <typename T>
    class ComplexH5Type : public H5::CompType
    {
    public:
        ComplexH5Type(void)
            : CompType(sizeof(std::complex<T>))
        {
            const H5::DataType *const datatype = to_h5type<T>::get();
            assert(datatype->getSize() == sizeof(T));
            // If we call the members "r" and "i", h5py interprets the
            // structure correctly as complex numbers.
            this->insertMember(std::string("r"), 0, *datatype);
            this->insertMember(std::string("i"), sizeof(T), *datatype);
            this->pack();
        }

        static const ComplexH5Type<T> *get_singleton(void)
        {
            // NOTE: constructing this could be a race condition
            static ComplexH5Type<T> singleton;
            return &singleton;
        }
    };

    template <typename T>
    struct to_h5type<std::complex<T>>
    {
        static inline const H5::DataType *get(void)
        {
            return ComplexH5Type<T>::get_singleton();
        }
    };

    // string types, to be used mainly for attributes

    template <>
    struct to_h5type<const char *>
    {
        static inline const H5::DataType *get(void)
        {
            static const H5::StrType strtype(0, H5T_VARIABLE);
            return &strtype;
        }
    };

    template <>
    struct to_h5type<char *>
    {
        static inline const H5::DataType *get(void)
        {
            static const H5::StrType strtype(0, H5T_VARIABLE);
            return &strtype;
        }
    };

    // XXX: for some unknown reason the following two functions segfault if
    // H5T_VARIABLE is used.  The passed strings should still be null-terminated,
    // so this is a bit worrisome.

    template <std::size_t N>
    struct to_h5type<const char[N]>
    {
        static inline const H5::DataType *get(void)
        {
            static const H5::StrType strtype(0, N);
            return &strtype;
        }
    };

    template <std::size_t N>
    struct to_h5type<char[N]>
    {
        static inline const H5::DataType *get(void)
        {
            static const H5::StrType strtype(0, N);
            return &strtype;
        }
    };
} // namespace HDF5