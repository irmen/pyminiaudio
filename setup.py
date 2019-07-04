import os
import sys
import enum
import re
import textwrap
import unittest
from setuptools import setup

if sys.version_info < (3, 5):
    raise SystemExit("Miniaudio requires Python 3.5 or newer")

miniaudio_path = os.path.abspath(".")  # to make sure the compiler can find the required include files
PKG_VERSION = re.search(r'^__version__\s*=\s*"(.+)"', open("miniaudio.py", "rt").read(), re.MULTILINE).groups()[0]


def miniaudio_test_suite():
    testloader = unittest.TestLoader()
    testsuite = testloader.discover("tests", pattern="test*.py")
    return testsuite


if __name__ == "__main__":
    setup(
        name="miniaudio",
        version=PKG_VERSION,
        cffi_modules=["build_ffi_module.py:ffibuilder"],
        include_dirs=[miniaudio_path],
        zip_safe=False,
        include_package_data=False,
        py_modules=["miniaudio"],
        install_requires=["cffi>=1.3.0"],
        setup_requires=["cffi>=1.3.0"],
        tests_require=[],
        test_suite="setup.miniaudio_test_suite"
    )


def make_docs():
    import miniaudio
    import inspect
    documentable_classes = []
    documentable_functions = []
    width = 100
    for name, item in inspect.getmembers(miniaudio):
        if inspect.isclass(item) or inspect.isfunction(item):
            if item.__module__ == "miniaudio" and not item.__name__.startswith('_'):
                if inspect.isclass(item):
                    documentable_classes.append(item)
                elif inspect.isfunction(item):
                    documentable_functions.append(item)
    print("\n\n==================== 8<  GENERATED DOCS 8< =================\n\n")
    for f in documentable_functions:
        doc = inspect.getdoc(f) or "No documentation available"
        sig = inspect.signature(f)
        sig = "*function*  ``{name}  {sig}``".format(name=f.__name__, sig=sig)
        print(sig)
        print()
        for line in textwrap.wrap("> "+doc, width):
            print(line)
        print("\n")
    for c in documentable_classes:
        if issubclass(c, enum.Enum):
            print("*enum class*  ``{name}``".format(name=c.__name__))
            print(" names:  ``{}``\n".format("`` ``".join(e.name for e in list(c))))
            doc = inspect.getdoc(c) or "No documentation available"
            for line in textwrap.wrap("> "+doc, width):
                print(line)
            print("\n")
        else:
            doc = inspect.getdoc(c) or "No documentation available"
            sig = inspect.signature(c.__init__)
            print("*class*  ``{}``\n".format(c.__name__))
            sig = "``{name}  {sig}``\n".format(name=c.__name__, sig=sig)
            print(sig)
            print()
            for line in textwrap.wrap("> "+doc, width):
                print(line)
            print("\n")
