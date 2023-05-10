from setuptools import setup, Extension

try:
    from Cython.Build import cythonize
    ext_modules = cythonize("vsext.pyx")
except ModuleNotFoundError:
    ext_modules = [Extension(
        "vsext",
        sources=["vsext.cpp"],
        language="c++",
        extra_compile_args=["-std=c++20"],
        extra_link_args=["-std=c++20"]
    )]

setup(
    name="vsext",
    version="0.1.0",
    ext_modules=ext_modules
)

