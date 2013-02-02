#! /usr/bin/env python
#install script for cdiff by Shimon Tolts
import os
from setuptools import setup, find_packages

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "cdiff",
    version = "0.0.1",
    author = "Matthew Wang",
    description = ("View incremental, colored diff in unified format or in side"
    				"							by side mode with auto pager"),
    keywords = "diff",
    url = "https://github.com/ymattw/cdiff",
    scripts = ['src/cdiff.py'],
    long_description=read('README.md'),
    install_requires = ['python>= 2.5.0'],
)