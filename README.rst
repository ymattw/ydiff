Cdiff
=====

.. image:: https://travis-ci.org/ymattw/cdiff.png?branch=master
   :target: https://travis-ci.org/ymattw/cdiff
   :alt: Build status

Term based tool to view *colored*, *incremental* diff in a *Git/Mercurial/Svn*
workspace or from stdin, with *side by side* and *auto pager* support. Requires
python (>= 2.5.0) and ``less``.

.. image:: http://ymattw.github.com/cdiff/img/default.png
   :alt: default
   :align: center

.. image:: http://ymattw.github.com/cdiff/img/side-by-side.png
   :alt: side by side
   :align: center
   :width: 900 px

Installation
------------

Install with pip
~~~~~~~~~~~~~~~~

Cdiff is already listed on `PyPI <http://pypi.python.org/pypi/cdiff>`_, you can
install with ``pip`` if you have the tool.

.. code:: sh

    pip install --upgrade cdiff

Install with setup.py
~~~~~~~~~~~~~~~~~~~~~

You can also run the setup.py from the source if you don't have ``pip``.

.. code:: sh

    git clone https://github.com/ymattw/cdiff.git
    cd cdiff
    ./setup.py install

Download directly
~~~~~~~~~~~~~~~~~

Just save `cdiff.py <https://raw.github.com/ymattw/cdiff/master/cdiff.py>`_ to
whatever directory which is in your ``$PATH``, for example, ``$HOME/bin`` is in
my ``$PATH``, so I save the script there and name as ``cdiff``.

.. code:: sh

    curl https://raw.github.com/ymattw/cdiff/master/cdiff.py > ~/bin/cdiff
    chmod +x ~/bin/cdiff

Usage
-----

Type ``cdiff -h`` to show usage::

    $ cdiff -h
    Usage: cdiff [options] [file|dir ...]

    View colored, incremental diff in a workspace or from stdin, with side by side
    and auto pager support

    Options:
      --version           show program's version number and exit
      -h, --help          show this help message and exit
      -s, --side-by-side  enable side-by-side mode
      -w N, --width=N     set text width for side-by-side mode, default is 80
      -l, --log           show log with changes from revision control
      -c M, --color=M     colorize mode 'auto' (default), 'always', or 'never'

Read diff from local modification in a *Git/Mercurial/Svn* workspace (output
from e.g. ``git diff``, ``svn diff``):

.. code:: sh

    cd proj-workspace
    cdiff                       # view colored incremental diff
    cdiff -s                    # view side by side
    cdiff -s -w 90              # use text width 90 other than default 80
    cdiff -s file1 dir2         # view modification of given files/dirs only
    cdiff -s -w90 -- -U10       # pass '-U10' to underneath revision diff tool

Read log with changes in a *Git/Mercurial/Svn* workspace (output from e.g.
``git log -p``, ``svn log --diff``), note *--diff* option is new in svn 1.7.0:

.. code:: sh

    cd proj-workspace
    cdiff -l                    # read log along with changes
    cdiff -ls                   # equivalent to cdiff -l -s, view side by side
    cdiff -ls -w90              # set text width 90 as well
    cdiff -ls file1 dir2        # see log with changes of given files/dirs only

Pipe in a diff:

.. code:: sh

    git log -p -2 | cdiff       # view git log with changes of last 2 commits
    git show 15bfa | cdiff -s   # view a given git commit, side by side
    svn diff -r1234 | cdiff -s  # view svn diff comparing to given revision
    diff -u file1 file2 | cdiff # view diff between two files (note the '-u')
    diff -ur dir1 dir2 | cdiff  # view diff between two dirs

    # View diff in a GitHub pull request, side by side
    curl https://github.com/ymattw/cdiff/pull/11.diff | cdiff -s

    # View a patch file in unified or context format, the latter depends on
    # command `filterdiff` from package `patchutils` which is available in
    # major Linux distros and MacPorts.
    #
    cdiff -s < foo.patch

Redirect output to another patch file is safe:

.. code:: sh

    svn diff -r PREV | cdiff -s > my.patch

Notes
-----

Cdiff has following known issues:

- Does not recognize `normal` diff, and depends on ``filterdiff`` (patchutils)
  to read `context` diff
- Side by side mode has alignment problem for wide chars
- Terminal might be in a mess on exception (type ``reset`` can fix it)

Pull requests are very welcome, please make sure your changes can pass unit
tests and regression tests by run ``make test`` (required tool *coverage* can
be installed with ``pip install coverage``).  Also watch out `travis build
<https://travis-ci.org/ymattw/cdiff/pull_requests>`_ after push, make sure it
passes as well.

See also
--------

I have another tool `coderev <https://github.com/ymattw/coderev>`_ which
generates side-by-side diff pages for code review from two given files or
directories, I found it's not easy to extend to support git so invented
`cdiff`.  Idea of ansi color markup is also from project `colordiff
<https://github.com/daveewart/colordiff>`_.

