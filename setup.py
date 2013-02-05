#!/usr/bin/env python

from __future__ import with_statement
from distutils.core import setup
import os

# Create symlink so that to use 'scripts' w/o '.py'
link_name = 'cdiff'
if os.path.exists(link_name):
    os.unlink(link_name)
os.symlink('src/cdiff.py', link_name)

# This awfulness is all in aid of grabbing the version number out
# of the source code, rather than having to repeat it here.  Basically,
# we parse out firt line starts with "__version__" and execute it
#
with open('cdiff') as script:
    for line in script:
        if line.startswith('__version__ = '):
            exec(line)
            break

with open('README.rst') as doc:
    long_description = doc.read()
with open('CHANGES') as changes:
    long_description += changes.read()

setup(
    name = 'cdiff',
    version = __version__,
    author = 'Matthew Wang',
    author_email = 'mattwyl(@)gmail(.)com',
    license = 'BSD-3',
    description = ('View colored, incremental diff in workspace, or given '
                   'file from stdin, with side by side and auto pager support'),
    long_description = long_description,
    keywords = 'colored incremental side-by-side diff',
    url = 'https://github.com/ymattw/cdiff',
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
    package_dir = {'': 'src'},
    packages = [''],
    py_modules = ['cdiff'],
    scripts = [link_name],
)
