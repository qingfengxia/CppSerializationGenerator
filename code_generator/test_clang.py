import sys
import os.path
import clang.cindex as cc

# install libclang-6, must be version 6 as the time of writing in 2020
cc.Config.set_library_file("/usr/lib/llvm-6.0/lib/libclang.so.1")
from clang.cindex import TypeKind, CursorKind, TranslationUnit, Cursor

source = """
class Foo {
};
template <typename T>
class Template {
};
Template<Foo> instance;
int bar;
"""


def get_tu(source, lang="c", all_warnings=False, flags=[]):
    """Obtain a translation unit from source and language.
    By default, the translation unit is created from source file "t.<ext>"
    where <ext> is the default file extension for the specified language. By
    default it is C, so "t.c" is the default file name.
    Supported languages are {c, cpp, objc}.
    all_warnings is a convenience argument to enable all compiler warnings.
    """
    args = list(flags)
    name = "t.c"
    if lang == "cpp":
        name = "t.cpp"
        args.append("-std=c++11")
    elif lang == "objc":
        name = "t.m"
    elif lang != "c":
        raise Exception("Unknown language: %s" % lang)

    if all_warnings:
        args += ["-Wall", "-Wextra"]

    return TranslationUnit.from_source(name, args, unsaved_files=[(name, source)])


def get_cursor(source, spelling):
    """Obtain a cursor from a source object.
    This provides a convenient search mechanism to find a cursor with specific
    spelling within a source. The first argument can be either a
    TranslationUnit or Cursor instance.
    If the cursor is not found, None is returned.
    """
    # Convenience for calling on a TU.
    root_cursor = source if isinstance(source, Cursor) else source.cursor

    for cursor in root_cursor.walk_preorder():
        if cursor.spelling == spelling:
            return cursor

    return None


def assertEqual(a, b):
    assert a == b


tu = get_tu(source, lang="cpp")

# Varible with a template argument.
cursor = get_cursor(tu, "instance")
cursor_type = cursor.type
assertEqual(cursor.kind, CursorKind.VAR_DECL)
assertEqual(cursor_type.spelling, "Template<Foo>")
# assertEqual(cursor_type.get_num_template_arguments(), 1)
# template_type = cursor_type.get_template_argument_type(0)
assertEqual(template_type.spelling, "Foo")

# Variable without a template argument.
cursor = get_cursor(tu, "bar")
assertEqual(cursor.get_num_template_arguments(), -1)
