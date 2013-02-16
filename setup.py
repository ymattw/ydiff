#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import with_statement
from distutils.core import setup
import os
from cdiff import META_INFO as _meta

import sys
if sys.hexversion < 0x02050000:
    raise SystemExit("*** Requires python >= 2.5.0")

with open('README.rst') as doc:
    long_description = doc.read()
with open('CHANGES') as changes:
    long_description += changes.read()

setup(
    name = 'cdiff',
    version = _meta['version'],
    author = _meta['author'],
    author_email = _meta['email'],
    license = _meta['license'],
    description = _meta['description'],
    long_description = long_description,
    keywords = _meta['keywords'],
    url = _meta['url'],
    classifiers = [
        'Development Status :: 4 - Beta',
        'Topic :: Utilities',
        'License :: OSI Approved :: BSD License',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Programming Language :: Python',
    ],
    py_modules = ['cdiff'],
    scripts = ['cdiff'],
)

# vim:set et sts=4 sw=4 tw=80:
