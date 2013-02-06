#!/usr/bin/env python

from __future__ import with_statement
from distutils.core import setup
import os
from cdiff import META_INFO as _meta

# Create symlink so that to use 'scripts' w/o '.py'
link_name = 'cdiff'
if os.path.exists(link_name):
    os.unlink(link_name)
os.symlink('cdiff.py', link_name)

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
    packages = [],
    py_modules = ['cdiff'],
    scripts = [link_name],
)
