#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import with_statement
import sys
from setuptools import setup
from ydiff import PKG_INFO

with open('README.rst') as doc:
    long_description = doc.read()
with open('CHANGES.rst') as changes:
    long_description += changes.read()

setup(
    name='ydiff',
    version=PKG_INFO['version'],
    author=PKG_INFO['author'],
    license=PKG_INFO['license'],
    description=PKG_INFO['description'],
    long_description=long_description,
    keywords=PKG_INFO['keywords'],
    url=PKG_INFO['url'],
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Topic :: Utilities',
        'License :: OSI Approved :: BSD License',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
    python_requires='>=3',
    py_modules=['ydiff'],
    scripts=['ydiff'],
)

# vim:set et sts=4 sw=4 tw=79:
