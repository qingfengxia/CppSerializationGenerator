#!/usr/bin/python3
# copyright Qingfeng Xia @ UKAEA, 2020
# License:  same as RAMP


"""
see folder Readme for more details

"""


import sys
import os.path
from collections import OrderedDict

# from . import clang_util
from clang_util import *


class code_generator(object):
    """ base class for all code generators
    """

    def __init__(self, input_header, output_header, ns_name=""):
        self.is_header_only = True
        # extract only filename, without path
        self.input_header_file = input_header

        index = cx.Index.create()
        self.root_cursor = index.parse(input_file, ["c++", "-std=c++11"]).cursor

        if output_header:
            self.output_header_file = output_header
        else:
            self.output_header_file = input_header.replace(".h", "_generated.h")
        self.output_source_file = output_header.replace(".h", ".cpp")
        self.unit_test_file = input_header.replace(".h", "_test.cpp")
        self.namespace_name = ns_name

        self.generated_types = {}
        self.header_codes = []
        basic_header = """#pragma once
        // this file is generated by a python script, do not edit manually
        """
        self.header_codes.append(basic_header)
        self.decl_codes = ["/// this code section declare types, put into header file"]
        self.impl_codes = ["/// implication code, put into cpp file"]
        self.extra_decl_codes = []  # decl code in another namespace

    def write_code(self):
        # currently header only mode
        with open(self.output_header_file, "w") as f:
            f.writelines("\n".join(self.header_codes))
            f.write("\n\n")

            if self.namespace_name:
                f.write(f"namespace {self.namespace_name}{{")

            f.writelines("\n".join(self.decl_codes))
            f.write("\n\n")
            f.writelines("\n".join(self.impl_codes))

            if self.namespace_name:
                f.write(f"\n}} // namespace {self.namespace_name}\n")

            if self.extra_decl_codes:
                f.write("\n\n")
                f.write("\n".join(self.extra_decl_codes))


class hdf5_generator(code_generator):
    """
    
    /* no diagnostic for this one */
    #pragma GCC diagnostic pop
    
    """

    # still error in C++
    string_template = r""" todo """

    def __init__(self, input_header, output_header, ns_name=""):
        super(hdf5_generator, self).__init__(input_header, output_header, ns_name)
        h5_headers = f"""#include <H5Cpp.h>
        #include <cstring>
        #include "{self.input_header_file}"
        #include "HDF5_TypeTraits.h"
        #define TO_H5T(type_name) \
        (*HDF5::to_h5type<type_name>::get())
        """
        self.header_codes.append(h5_headers)
        self.sio_codes = []
        self.init_codes = ["/// this code section init instances, put into cpp file"]
        self.type_trait_codes = []
        # print_ast(self.root_cursor)

    def prepare(self):
        self.init_codes.append(
            """
        #if defined(__GNUC__)
        #pragma GCC diagnostic ignored "-Winvalid-offsetof"
        #endif """
        )
        self.init_codes.append("void init_h5types(){")

    def post(self):
        self.init_codes.append("\n}  // end of function init_h5types() \n")
        self.init_codes.append(
            """
        #ifdef __GCC__
        #pragma GCC diagnostic pop
        #endif """
        )

        self.impl_codes = self.init_codes + self.sio_codes

        self.extra_decl_codes.append("namespace HDF5{")
        self.extra_decl_codes.append("\n".join(self.type_trait_codes))
        self.extra_decl_codes.append("} // namespace HDF5 ")

    def generate(self):
        self.prepare()
        self.walk(self.root_cursor)
        self.post()

    def walk(self, node):
        # node is also a Cursor type in clang nomenclature
        if node.kind == CursorKind.STRUCT_DECL or node.kind == CursorKind.CLASS_DECL:
            self.generate_class_code(node)

        if node.kind == CursorKind.ENUM_DECL:
            self.generate_enum_code(node)

        for c in node.get_children():
            self.walk(c)  # recursive

    def generate_enum_code(self, node):
        # it is possible to get value and name of enum by clang
        pass

    def generate_cstr_type(self, class_name, field):
        # std::string, std::u8string,  c_str() can get the NUL-terminated c-style string pointer
        # a per-field write serializer() is needed, inject meta data as Attribute like type
        # H5::StrType(H5::PredType::C_S1, H5T_VARIABLE)) to write char* string_array[],
        # std::vector<std::string>

        _h5type_name = f"{class_name}_{field.spelling}_h5type"
        # el_h5type_name = char or u8char_t
        _template = f"""
        auto {_h5type_name} = H5::StrType(H5::PredType::C_S1, H5T_VARIABLE);
        {self.get_h5type(class_name)}.insertMember(\"{field.spelling}\", 
            HOFFSET({class_name}, {field.spelling}), {_h5type_name});"""

        return _template

    def generate_std_string_type(self, class_name, field):
        # std::string, std::u8string,  c_str() can get the NUL-terminated c-style string pointer
        # a per-field write serializer() is needed, inject meta data as Attribute like type
        # H5::StrType(H5::PredType::C_S1, H5T_VARIABLE)) to write char* string_array[],
        # std::vector<std::string>

        el_type_name = "char"
        _h5type_name = f"{class_name}_{field.spelling}_h5type"
        el_h5type_name = f"TO_H5T({el_type_name})"
        vl_field_name = f"{field.spelling}_hvl"
        offset_str = f"HOFFSET({class_name}, {vl_field_name})"
        _template = f"""
        auto {_h5type_name} = H5::VarLenType({el_h5type_name});
        {self.get_h5type(class_name)}.insertMember(\"{field.spelling}\", 
            {offset_str}, {_h5type_name});"""

        return _template

    def generate_vlen_array_type(self, class_name, field):
        # todo: std::vector<T> using vlen_type, delay the insertMember until runtime
        # a per-field write serializer() is needed, inject meta data as Attribute like type

        el_type_name = get_template_arguments(get_code(field))[0]
        _h5type_name = f"{class_name}_{field.spelling}_h5type"
        el_h5type_name = f"TO_H5T({el_type_name})"
        vl_field_name = f"{field.spelling}_hvl"
        offset_str = f"HOFFSET({class_name}, {vl_field_name})"
        _template = f"""
        auto {_h5type_name} = H5::VarLenType({el_h5type_name});
        {self.get_h5type(class_name)}.insertMember(\"{field.spelling}\", 
            {offset_str}, {_h5type_name});"""

        return _template

    def generate_array_type(self, class_name, array_field):
        # C style fixed size 1D Array only ,  1D array with contiguous memory storage
        # add attribute into ArrayType

        dim = 1  # 1D array
        array_field_name = array_field.spelling
        if is_std_array(array_field):
            # not working for `get_template_argument_value`
            # array_size = array_field.get_template_argument_value(1)
            # el_type_name = array_field.get_template_argument_type(0).spelling
            el_type_name, array_size = get_template_arguments(get_code(array_field))
        else:
            array_size = array_field.type.element_count
            el_type_name = array_field.type.element_type.spelling

        dim_array_expr = f"{{{array_size}}}"
        dim_name = f"{class_name}_{array_field_name}_dims"
        el_h5type_name = f"TO_H5T({el_type_name})"
        array_h5type_name = f"{class_name}_{array_field_name}_h5type"

        array_template = f"""
        hsize_t {dim_name}[] = {dim_array_expr};
        auto {array_h5type_name} = H5::ArrayType({el_h5type_name}, {dim}, {dim_name});
        {self.get_h5type(class_name)}.insertMember(\"{array_field_name}\", 
            HOFFSET({class_name}, {array_field_name}), {array_h5type_name});"""

        return array_template

    def is_user_type(self, field_decl):
        # class or struct,   "TypeKind.RECORD"
        return field_decl.type.spelling in self.generated_types

    def get_h5type(self, class_name):
        pos = class_name.find("_hvl")
        if pos > 0:
            return class_name[:pos] + "_h5type"
        else:
            return class_name + "_h5type"

    def generate_to_h5type_trait(self, class_name):
        return f"""template <>
        struct to_h5type<{self.namespace_name}::{class_name}>
        {{
            static inline const H5::DataType *get(void)
            {{
                return &{self.namespace_name}::{class_name}_h5type;
            }}
        }};
        """

    # format(class_name, array_field_name, el_type_name, dim, dim_array_expr)
    def generate_field(self, class_name, field_decl, field_type=None):
        """ 
        """
        field_name = field_decl.spelling
        if not field_type:
            field_type = field_decl.type
        field_type_name = field_decl.type.spelling  # field_decl.type.kind  -> TypeKind
        is_template = field_decl.get_num_template_arguments()
        print(
            f"{field_name}, {is_template} {field_type.spelling}, ", get_code(field_decl),
        )

        if is_cstyle_array(field_decl) or is_std_array(field_decl):
            return self.generate_array_type(class_name, field_decl)
        elif is_std_vector(field_decl):
            # return f"// WARNING: skip vlen array `{field_name}` of type `{field_type_name}`"
            return self.generate_vlen_array_type(class_name, field_decl)
        elif is_std_string(field_decl):
            return self.generate_std_string_type(class_name, field_decl)
        elif is_cstr_string(field_decl):
            return self.generate_cstr_type(class_name, field_decl)

        elif field_type.kind == TypeKind.POINTER:  # type detect is working for pointer
            # return f"// WARNING: skip raw pointer `{field_name}` of type `{field_type_name}`"
            return self.generate_field(class_name, field_decl, field_type=field_type.pointee)
        elif is_smart_pointer(field_decl):
            return f"// WARNING: skip smart pointer `{field_name}` of type `{field_type_name}`"
            # target_type = get_template_arguments(get_code(field))[0]  # str value
            # return self.generate_field(class_name, field_decl, field_type=target_type)

        # elif field_decl.is_reference():
        #    field_decl.referenced
        #    return f"// WARNING: skip reference type `{field_type_name}`"
        elif is_builtin_type(field_decl):
            field_h5type_name = f"TO_H5T({field_type_name})"
            return f"""{self.get_h5type(class_name)}.insertMember(\"{field_name}\", 
                HOFFSET({class_name}, {field_name}), {field_h5type_name});"""
        elif field_decl.is_anonymous():
            return f"// WARNING: skip anonymous `{field_name}` of type `{field_type_name}`"
        elif field_decl.is_scoped_enum():  ## field_decl.is_enum() or
            return f"// WARNING: skip enum type `{field_type_name}`"
        elif self.is_user_type(field_decl):
            if field_type_name in self.generated_types:
                field_h5type_name = self.generated_types[field_type_name]
                return f"""{self.get_h5type(class_name)}.insertMember(\"{field_name}\", 
                    HOFFSET({class_name}, {field_name}), {field_h5type_name});"""
            else:
                return f"/// WARNING: `{field_type_name}` yet generated, check if inside the input header"
        else:
            return f"/// WARNING: member `{field_name}` of type `{field_type_name}` not supported"

    def generate_hvl_class(self, cls, vl_fields):
        # copy into a derived class with extra hvl_t field
        class_name = cls.spelling
        ext_class_name = class_name + "_hvl"
        vl = "\n".join([f"hvl_t {k}_hvl;" for k in vl_fields.keys()])
        ctor = []
        for k, vtype in vl_fields.items():
            if vtype == "std::vector":
                ctor.append(f"{k}_hvl.p = obj.{k}.data();")
                ctor.append(f"{k}_hvl.len = obj.{k}.size();")
            if vtype == "std::string":
                ctor.append(f"{k}_hvl.p = std::malloc(sizeof(char) * (obj.{k}.size()+1));")
                ctor.append(f"std::strcpy((char*)({k}_hvl.p), obj.{k}.data());  // fixme: free()")
                ctor.append(f"{k}_hvl.len = obj.{k}.size()  + 1;")

        des = []
        for k, vtype in vl_fields.items():
            field = get_field_by_name(cls, k)
            if vtype == "std::string":
                des.append(
                    f"""// std::string from char* and length
                {k} = "fixme"; //  std::string({k}_hvl.p, {k}_hvl.len);
                """
                )
            if vtype == "std::vector":
                el_type_name = get_template_arguments(get_code(field))[0]
                des.append(
                    f"""
                auto {k}_ptr = static_cast<{el_type_name}*>({k}_hvl.p);
                {k}.assign({k}_ptr, {k}_ptr + {k}_hvl.len);
                """
                )

        ctor_lines = "\n".join(ctor)
        des_lines = "\n".join(des)

        return f"""class {ext_class_name} : public {class_name}{{
            public:
            // make base class's private and protected field public
            // using {class_name}::field_name;

            /// extra hvl_t fields for all varlen fields of the base class
            {vl}

            {ext_class_name} (){{  }}  // default ctor

            {ext_class_name} ({class_name}& obj): {class_name}(obj)
            {{
                {ctor_lines}
            }}

            /// needed for deserialization 
            {class_name} get_base()
            {{
                {des_lines}
                {class_name} obj(*this);
                return obj;
            }}

        }};
        """

    def get_varlen_types(self, cls):
        #
        vl_fields = OrderedDict()
        for field in cls.get_children():
            if (
                field.kind == CursorKind.FIELD_DECL
                and field.access_specifier == cx.AccessSpecifier.PUBLIC
            ):
                if is_std_vector(field):
                    vl_fields[field.spelling] = "std::vector"
                if is_std_string(field):
                    vl_fields[field.spelling] = "std::string"

        return vl_fields

    def generate_class_code(self, cls):
        # apply to only data class, trivial? no pointer type

        vl_fields = self.get_varlen_types(cls)
        if len(vl_fields.keys()) > 0:
            class_name = cls.spelling + "_hvl"
        else:
            class_name = cls.spelling

        print("generating code for: `%s`, full type name: `%s`" % (cls.spelling, cls.type.spelling))

        if cls.kind == CursorKind.CLASS_TEMPLATE:
            print("template class is not supported yet")
            return

        protected_fields = OrderedDict()
        # non-Recurse for children of this class
        for field in cls.get_children():
            if field.kind == CursorKind.FIELD_DECL:
                self.init_codes.append(self.generate_field(class_name, field))

            if field.access_specifier == cx.AccessSpecifier.PROTECTED:
                protected_fields[field.spelling] = "protected"
            if field.access_specifier == cx.AccessSpecifier.PRIVATE:
                protected_fields[field.spelling] = "private"

        self.init_codes.append(f"// end of CompType member/field definition for {class_name}\n")
        # register the user type, so it can be field type of another user type
        self.generated_types[cls.type.spelling] = f"{class_name}_h5type"

        # is_trivially_copyable() is not available in clang, monkey_patch?
        # if not cls.type.is_pod():  # is_pod() is too strict requirement
        if vl_fields:
            if not self.is_header_only:
                self.generate_serializer_decl(cls)

            self.sio_codes.append(self.generate_serializer_impl(cls, vl_fields))
            self.sio_codes.append(self.generate_deserializer_impl(cls))

            # FIXME for not pod class, sizeof() does not reflect the storage size
            self.decl_codes.append(self.generate_hvl_class(cls, vl_fields))
            size_str = f"sizeof({class_name})"  # + {len(vl_fields.keys())}*sizeof(hvl_t)
            type_decl = f"H5::CompType {cls.spelling}_h5type({size_str});"
        else:
            type_decl = f"H5::CompType {class_name}_h5type(sizeof({class_name}));"
        self.decl_codes.append(type_decl)
        self.type_trait_codes.append(self.generate_to_h5type_trait(cls.spelling))
        #

    ####################################################################

    def generate_serializer_decl(self, cls):
        class_name = cls.spelling
        return f"""void {class_name}_serialize(const {class_name}& obj, 
            const H5::CompType& h5tobj, H5::H5Object& h5o);"""

    def generate_deserializer_decl(self, cls):
        class_name = cls.spelling
        return f"""{class_name} {class_name}_deserialize(H5::H5Object&, const H5::CompType& h5tobj); """

    def generate_serializer_impl(self, cls, vl_fields):
        # per-element write
        class_name = cls.spelling

        _s = f"""
        template <> struct to_h5serializer<{self.namespace_name}::{class_name}>
        {{
            static inline const Serializer<{self.namespace_name}::{class_name}> get(void)
            {{
                return {self.namespace_name}::{class_name}_serialize;
            }}
        }};
        """
        self.type_trait_codes.append(_s)

        lines = []
        lines.append(
            f"""void {class_name}_serialize({class_name}& obj, H5::DataSet & dataset, 
                   const H5::DataSpace * memspace, const H5::DataSpace * space) {{
                {class_name}_hvl tmp(obj);
                if(memspace)
                    dataset.write(&tmp, {class_name}_h5type, *memspace, *space);
                else
                {{
                    // todo check if it attributeval, attrib
                    //dataset.write({class_name}_h5type, &tmp);
                }}

            """
        )

        # for each VarlenType emember in ht5 CompType
        # base_num = f"base_num = h5tobj.get_number"
        # for i, k in enumerate(vl_fields.keys()):
        #     vl_type = vl_fields[k]
        #     if vl_type == "std::vector":
        #         line = f"""
        #         auto {k}_i = h5tobj.getMemberIndex("{k}");
        #         auto {k}_vl_t = getMemberVarLenType({k}_i);
        #         """

        lines.append(f"}} //  end of `{class_name}` serializer function\n")
        return "\n".join(lines)

    def generate_deserializer_impl(self, cls):
        # flatten but keep the shape as attribute?
        class_name = cls.spelling

        _d = f"""
        template <> struct to_h5deserializer<{self.namespace_name}::{class_name}>
        {{
            static inline const Deserializer<{self.namespace_name}::{class_name}> get(void)
            {{
                return {self.namespace_name}::{class_name}_deserialize;
            }}
        }};
        """
        self.type_trait_codes.append(_d)

        return f"""{class_name} {class_name}_deserialize(H5::DataSet & dataset, 
                   const H5::DataSpace * memspace, const H5::DataSpace * space) {{
            {class_name}_hvl tmp;
            dataset.write(&tmp, {class_name}_h5type, *memspace, *space);
            return tmp.get_base();
        }}"""


if __name__ == "__main__":

    input_file = "../demo/CodeGen_types.h"

    if len(sys.argv) >= 2:
        input_file = sys.argv[1]

    # tmp
    if input_file.find("EERA") >= 0:
        namespace = "EERAModel"
    else:
        namespace = "CodeGen"
    if not os.path.exists(input_file):
        raise Exception(
            f"{input_file} does not exist, check filename and current working directory"
        )

    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        output_file = input_file.replace(".h", "_hdf5.h")

    g = hdf5_generator(input_file, output_file, ns_name=namespace)
    # todo: detect namespace_name
    g.generate()
    g.write_code()
