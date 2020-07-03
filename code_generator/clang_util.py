import os.path
import clang.cindex as cx
from clang.cindex import TypeKind, CursorKind

# install libclang-6, must be version 6 as the time of writing in 2020
cx.Config.set_library_file("/usr/lib/llvm-6.0/lib/libclang.so.1")


# Cymbal makes it easy to add functionality missing from libclang Python bindings
# pybinder for pyocct has  clangext.py for monkey_patch extension the clang.module


def get_code(cursor):
    # todo: type and var_name has no space to separate
    ts = []
    for t in cursor.get_tokens():
        ts.append(t.spelling)
    return "".join(ts)


def get_template_arguments(code):
    # template parameters list extracted from field decl's source code
    start = code.find("<") + 1
    end = code.rfind(">")
    all_args = code[start:end].split(",")
    return [a.strip() for a in all_args]


def get_field_by_name(cls, field_name):
    for field in cls.get_children():
        if field.kind == CursorKind.FIELD_DECL and field.spelling == field_name:
            return field


# can be further appended, assuming it is template class,
registered_smart_pointers = ["shared_ptr", "unique_ptr", "scoped_ptr"]


def is_smart_pointer(field_decl):
    # can be registered to a list
    for p in registered_smart_pointers:
        if get_code(field_decl).find(p) >= 0:
            return True
    return False


def find_all(a_str, sub):
    # find all occurrences of a substring
    pos = []
    start = 0
    while True:
        start = a_str.find(sub, start)
        if start == -1:
            return pos
        pos.append(start)
        start += len(sub)  # use start += 1 to find overlapping matches
    return pos


## ############### field decl type detection ##################
def is_std_vector(field_decl):
    '''
    TypeKind.POINTER
        t.get_template_argument_type(0).spelling
        def get_template_argument_type(self, num):
            """Returns the CXType for the indicated template argument."""
            return conf.lib.clang_Cursor_getTemplateArgumentType(self, num)
    '''
    decl_code = get_code(field_decl)
    return decl_code.find("std::vector<") >= 0 and len(find_all(decl_code, "vector<")) == 1


def is_xtensor_matrix(field_decl):
    """ xt::xtensor<>
    """
    decl_code = get_code(field_decl)
    return decl_code.find("xtensor") >= 0


def is_eigen_matrix(field_decl):
    """ Eigen::Matrix<>
    """
    decl_code = get_code(field_decl)
    return decl_code.find("Eigen::Matrix") >= 0


def is_vlen_matrix(field_decl):
    """ std::vector<std::vector<int>>  can be rugged
    """
    decl_code = get_code(field_decl)
    return len(find_all(decl_code, "vector<")) == 2


def is_cstyle_matrix(field_decl):
    """ 2D array: int** A,  int A[][],  int* A[]
    using some place_holder as row_count, col_count, let user to manually set it
    """
    decl_code = get_code(field_decl)
    return (
        len(find_all(decl_code, "[")) == 2
        or len(find_all(decl_code, "*")) == 2
        or (len(find_all(decl_code, "*")) == 1 and len(find_all(decl_code, "[")) == 1)
    )


def is_matrix(field_decl):
    return (
        is_cstyle_matrix(field_decl)
        or is_eigen_matrix(field_decl)
        or is_vlen_matrix(field_decl)
        or is_xtensor_matrix(field_decl)
    )


def is_cstyle_array(field_decl):
    """
    TypeKind.CONSTANTARRAY `int A[3]` 
    TypeKind.INCOMPLETEARRAY  `int A[]` but compiler should know the size
    TypeKind.VARIABLEARRAY 
    TypeKind.DEPENDENTSIZEDARRAY `int s[x+foo()]` size expression is arbitrary
    """
    tkind = field_decl.type.kind
    return tkind == TypeKind.CONSTANTARRAY or tkind == TypeKind.INCOMPLETEARRAY
    # return ctype.spelling.find("[")>=0  # e.g. `int []`


def is_std_array(field_decl):
    return get_code(field_decl).find("std::array<") >= 0  # e.g. `std::array<int, 3>`


def is_cstr_string(field_decl):
    # char* cstyle_string, `char[]` is_cstyle_array
    code = get_code(field_decl)
    return code.find("*") >= 0 and code.find("char") >= 0


def is_template(decl):
    return hasattr(decl, "type") and decl.type.get_num_template_arguments() != -1


def is_std_string(field_decl):
    # std::string
    return get_code(field_decl).find("std::string") >= 0


def is_builtin_type(field_decl):
    # bug: all template are detected as builtin type Int, why?
    v = field_decl.type.kind.value
    return v >= TypeKind.BOOL.value and v <= TypeKind.LONGDOUBLE.value


######################################################
# helpers for visiting the AST recursively
def visit(node, func):
    func(node)
    for c in node.get_children():
        visit(c, func)


def print_ast(node):
    # show the AST tree

    def visit_depth(node, func, depth=0):
        # print(type(node))
        func(node, depth)
        for c in node.get_children():
            visit_depth(c, func, depth + 1)

    def ast_printer(node, depth):
        print(" " * depth, node.kind, node.spelling)

    visit_depth(node, ast_printer)
