#!/usr/bin/env python

from __future__ import with_statement
from distutils.core import setup

with open('README.rst') as doc:
    long_description = doc.read()

setup(
    name = 'cdiff',
    version = '0.0.1',
    author = 'Matthew Wang',
    author_email = 'mattwyl@gmail.com',
    license = 'BSD-3',
    description = ('View colored, incremental diff in unified format or side '
                   'by side with auto pager'),
    long_description = long_description,
    keywords = 'colored incremental side-by-side diff',
    url = 'https://github.com/ymattw/cdiff',
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Topic :: Utilities',
        'License :: OSI Approved :: BSD License',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Programming Language :: Python',
    ],
    package_dir = {'': 'src'},
    packages = [''],
    py_modules = ['cdiff'],
    scripts = ['src/cdiff'],
)
