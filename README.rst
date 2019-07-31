Ydiff
=====

.. image:: https://travis-ci.org/ymattw/ydiff.png?branch=master
   :target: https://travis-ci.org/ymattw/ydiff
   :alt: Build status

Term based tool to view *colored*, *incremental* diff in a version controlled
workspace (supports Git, Mercurial, Perforce and Svn so far) or from stdin,
with *side by side* (similar to ``diff -y``) and *auto pager* support. Requires
python (>= 2.5.0) and ``less``.

.. image:: https://raw.github.com/ymattw/ydiff/gh-pages/img/default.png
   :alt: default
   :align: center

.. image:: https://raw.github.com/ymattw/ydiff/gh-pages/img/side-by-side.png
   :alt: side by side
   :align: center
   :width: 900 px

Installation
------------

Install with pip
~~~~~~~~~~~~~~~~

Ydiff is already listed on `PyPI`_, you can install with ``pip`` if you have
the tool.

.. _PyPI: http://pypi.python.org/pypi/ydiff

.. code-block:: bash

    pip install --upgrade ydiff

Install with setup.py
~~~~~~~~~~~~~~~~~~~~~

You can also run the setup.py from the source if you don't have ``pip``.

.. code-block:: bash

    git clone https://github.com/ymattw/ydiff.git
    cd ydiff
    ./setup.py install

Install with Homebrew
~~~~~~~~~~~~~~~~~~~~~

You can also install with Homebrew on Mac. (Thanks to `@josa42`_,
`@bfontaine`_, `@hivehand`_ and `@nijikon`_ for contributing to the Homebrew
`Formula`_).

.. _`@josa42`: https://github.com/josa42
.. _`@bfontaine`: https://github.com/bfontaine
.. _`@hivehand`: https://github.com/hivehand
.. _`@nijikon`: https://github.com/nijikon
.. _`Formula`: https://github.com/Homebrew/homebrew-core/blob/master/Formula/ydiff.rb

.. code-block:: bash

    brew install ydiff

Download directly
~~~~~~~~~~~~~~~~~

Just save `ydiff.py`_ to whatever directory which is in your ``$PATH``, for
example, ``$HOME/bin`` is in my ``$PATH``, so I save the script there and name
as ``ydiff``.

.. _`ydiff.py`: https://raw.github.com/ymattw/ydiff/master/ydiff.py

.. code-block:: bash

    curl -ksSL https://raw.github.com/ymattw/ydiff/master/ydiff.py > ~/bin/ydiff
    chmod +x ~/bin/ydiff

Usage
-----

Type ``ydiff -h`` to show usage::

    $ ydiff -h
    Usage: ydiff [options] [file|dir ...]

    View colored, incremental diff in a workspace or from stdin, with side by side
    and auto pager support

    Options:
      --version            show program's version number and exit
      -h, --help           show this help message and exit
      -s, --side-by-side   enable side-by-side mode
      -w N, --width=N      set text width for side-by-side mode, 0 for auto
                           detection, default is 80
      -l, --log            show log with changes from revision control
      -c M, --color=M      colorize mode 'auto' (default), 'always', or 'never'
      -t N, --tab-width=N  convert tab characters to this many spaces (default: 8)
      --wrap               wrap long lines in side-by-side view

      Note:
        Option parser will stop on first unknown option and pass them down to
        underneath revision control. Environment variable YDIFF_OPTIONS may be
        used to specify default options that will be placed at the beginning
        of the argument list.

Read diff from local modification in a *Git/Mercurial/Svn* workspace (output
from e.g. ``git diff``, ``svn diff``):

.. code-block:: bash

    cd proj-workspace
    ydiff                         # view colored incremental diff
    ydiff -s                      # view side by side, use default text width 80
    ydiff -s -w 90                # use text width 90 other than default 80
    ydiff -s -w 0                 # auto set text width based on terminal size
    ydiff -s -w 0 --wrap          # same as before, but also wrap long lines
    ydiff -s file1 dir2           # view modification of given files/dirs only
    ydiff -s -w90 --wrap -- -U10  # pass '-U10' to underneath revision diff tool
    ydiff -s -w90 --wrap -U10     # '--' is optional as it's unknown to ydiff
    ydiff -s --cached             # show git staged diff (git diff --cached)
    ydiff -s -r1234               # show svn diff to revision 1234

Read log with changes in a *Git/Mercurial/Svn* workspace (output from e.g.
``git log -p``, ``svn log --diff``), note *--diff* option is new in svn 1.7.0:

.. code-block:: bash

    cd proj-workspace
    ydiff -l                    # read log along with changes
    ydiff -ls                   # equivalent to ydiff -l -s, view side by side
    ydiff -ls -w90 --wrap       # set text width 90 and enable wrapping as well
    ydiff -ls file1 dir2        # see log with changes of given files/dirs only

Defaults
~~~~~~~~~~~~~~~~
Environment variable ``YDIFF_OPTIONS`` may be used to specify default options
that will be placed at the beginning of the argument list, for example:

.. code-block:: bash

    export YDIFF_OPTIONS='-s -w0 --wrap'
    ydiff foo                   # equivalent to "ydiff -s -w0 --wrap foo"

If you feel more comfortable with a command such as ``git ydiff`` to trigger
the ydiff command, you may symlink the executable to one named ``git-ydiff``
as follows:

.. code-block:: bash

    ydiff_dir=$(dirname $(which ydiff))
    ln -s "${ydiff_dir}/ydiff" "${ydiff_dir}/git-ydiff"

Pipe in a diff:

.. code-block:: bash

    git log -p -2 | ydiff       # view git log with changes of last 2 commits
    git show 15bfa | ydiff -s   # view a given git commit, side by side
    svn diff -r1234 | ydiff -s  # view svn diff comparing to given revision
    diff -u file1 file2 | ydiff # view diff between two files (note the '-u')
    diff -ur dir1 dir2 | ydiff  # view diff between two dirs

    # View diff in a GitHub pull request, side by side
    curl https://github.com/ymattw/ydiff/pull/11.diff | ydiff -s

    # View a patch file in unified or context format, the latter depends on
    # command `filterdiff` from package `patchutils` which is available in
    # major Linux distros and MacPorts.
    #
    ydiff -s < foo.patch

Redirect output to another patch file is safe:

.. code-block:: bash

    svn diff -r PREV | ydiff -s > my.patch

Notes
-----

Ydiff has following known issues:

- Does not recognize `normal` diff, and depends on ``filterdiff`` (patchutils)
  to read `context` diff
- Side by side mode has alignment problem for wide chars
- Terminal might be in a mess on exception (type ``reset`` can fix it)

Pull requests are very welcome, please make sure your changes can pass unit
tests and regression tests by run ``make test`` (required tool *coverage* can
be installed with ``pip install coverage``).  Also watch out `travis build`_
after push, make sure it passes as well.

.. _`travis build`: https://travis-ci.org/ymattw/ydiff/pull_requests

See also
--------

I have another tool `coderev`_ which generates side-by-side diff pages for code
review from two given files or directories, I found it's not easy to extend to
support git so invented `ydiff`.  Idea of ansi color markup is also from
project `colordiff`_.

.. _coderev: https://github.com/ymattw/coderev
.. _colordiff: https://github.com/daveewart/colordiff

.. vim:set ft=rst et sw=4 sts=4 tw=79:
