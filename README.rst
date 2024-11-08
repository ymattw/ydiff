Ydiff
=====

.. image:: https://github.com/ymattw/ydiff/actions/workflows/test.yml/badge.svg
   :alt: Tests status
   :target: https://github.com/ymattw/ydiff/actions

Term based tool to view *colored*, *incremental* diff in a version controlled
workspace (supports Git, Mercurial, Perforce and Svn so far) or from stdin,
with *side by side* (similar to ``diff -y``) and *auto pager* support. Requires
python3 and ``less``.

.. image:: https://github.com/ymattw/ydiff/blob/master/img/side-by-side.png
   :alt: side by side
   :align: center
   :width: 900 px

.. image:: https://github.com/ymattw/ydiff/blob/master/img/unified.png
   :alt: unified
   :align: center

Ydiff only supports diff in `Unified Format`_. This is default in most version
control system except Perforce, which needs an environment variable
``P4DIFF="diff -u"`` to output unified diff.

.. _`Unified Format`: https://en.wikipedia.org/wiki/Diff#Unified_format

Installation
------------

Ydiff only depends on Python built-in libraries, so you can just download the
source and run without worrying about any installation.

Git tagged `releases`_ will be packaged and uploaded to PyPI timely, however,
packages hosted elsewhere are not (please note they are not managed by the
author `@ymattw`_).

.. _`@ymattw`: https://github.com/ymattw
.. _`releases`: https://github.com/ymattw/ydiff/releases

Download directly
~~~~~~~~~~~~~~~~~

Just save `ydiff.py`_ to whatever directory which is in your ``$PATH``, for
example, ``$HOME/bin`` is in my ``$PATH``, so I save the script there and name
as ``ydiff``.

.. _`ydiff.py`: https://raw.github.com/ymattw/ydiff/master/ydiff.py

.. code-block:: bash

    curl -L https://raw.github.com/ymattw/ydiff/master/ydiff.py > ~/bin/ydiff
    chmod +x ~/bin/ydiff

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
.. _`Formula`: https://github.com/Homebrew/homebrew-core/blob/master/Formula/y/ydiff.rb

.. code-block:: bash

    brew install ydiff


Install on Fedora
~~~~~~~~~~~~~~~~~

On Fedora, you can install ydiff with dnf.

.. code-block:: bash

    dnf install ydiff

Install on FreeBSD
~~~~~~~~~~~~~~~~~~

On FreeBSD, you can install ydiff with pkg.

.. code-block:: bash

    pkg install ydiff

Usage
-----

Type ``ydiff -h`` to show usage::

    $ ydiff -h
    Usage: ydiff [options] [file|dir ...]

    View colored, incremental diff in a workspace or from stdin, with side by side
    and auto pager support

    Options:
      --version             show program's version number and exit
      -h, --help            show this help message and exit
      -s, --side-by-side    enable side-by-side mode (default True; DEPRECATED)
      -u, --unified         show diff in unified mode (disables side-by-side mode)
      -w N, --width=N       set text width for side-by-side mode, 0 (default) for
                            auto detection and fallback to 80 when not possible
      -l, --log             show log with changes from revision control
      -c M, --color=M       colorize mode 'auto' (default), 'always', or 'never'
      -t N, --tab-width=N   convert tab chars to this many spaces (default: 8)
      --wrap                wrap long lines in side-by-side view (default True;
                            DEPRECATED)
      --nowrap, --no-wrap   do not wrap long lines in side-by-side view
      -p M, --pager=M       pager application to feed output to, default is 'less'
      -o M, --pager-options=M
                            options to supply to pager application

      Note:
        Option parser will stop on first unknown option and pass them down to
        underneath revision control. Environment variable YDIFF_OPTIONS may be
        used to specify default options that will be placed at the beginning
        of the argument list.

      Note:
        Option parser will stop on first unknown option and pass them down to
        underneath revision control. Environment variable YDIFF_OPTIONS may be
        used to specify default options that will be placed at the beginning
        of the argument list.

Read diff from local modification in a *Git/Mercurial/Perforce/Svn* workspace
(output from e.g. ``git diff``, ``svn diff``):

.. code-block:: bash

    cd proj-workspace
    ydiff                       # view colored side by side diff, auto set text
                                # width based on terminal size
    ydiff -u                    # view colored incremental diff in unified mode
    ydiff -w 90                 # use text width 90, wrap long lines
    ydiff --no-wrap             # auto set text width but do not wrap long lines
    ydiff file1 dir2            # view modification of given files/dirs only
    ydiff -w90 -- -U10          # pass '-U10' to underneath revision diff tool
    ydiff -w90 -U10             # '--' is optional as it's unknown to ydiff
    ydiff --cached              # show git staged diff (git diff --cached)
    ydiff -r1234                # show svn diff to revision 1234

Read log with changes in a *Git/Mercurial/Svn* workspace (output from e.g.
``git log -p``, ``svn log --diff``), note *--diff* option is new in svn 1.7.0:

.. code-block:: bash

    cd proj-workspace
    ydiff -l                    # read log along with changes, side by side
    ydiff -lu                   # equivalent to ydiff -l -u, unified mode
    ydiff -l -w90 --no-wrap     # set text width 90 and disable wrapping
    ydiff -l file1 dir2         # see log with changes of given files/dirs only

Utilize a specific pager application:

.. code-block:: bash

    ydiff                           # default pager - less
    LESS_OPTS='-FRSX --shift 1'
    ydiff -p less -o "${LESS_OPTS}" # emulate default pager
    ydiff -p /opt/bin/less          # custom pager to override 'less' in $PATH
    ydiff -p cat                    # non-paging ANSI processor for colorizing

Pipe in a diff:

.. code-block:: bash

    git log -p -2 | ydiff       # view git log with changes of last 2 commits
    git show 15bfa | ydiff      # view a given git commit, side by side
    svn diff -r1234 | ydiff     # view svn diff comparing to given revision
    diff -u file1 file2 | ydiff # view diff between two files (note the '-u')
    diff -ur dir1 dir2 | ydiff  # view diff between two dirs

    # View diff in a GitHub pull request, side by side
    curl https://github.com/ymattw/ydiff/pull/11.diff | ydiff

    # View a patch file in colored unified format.
    ydiff -u < foo.patch

Redirect output to another patch file is safe even without ``-u``:

.. code-block:: bash

    svn diff -r PREV | ydiff > my.patch

Environment variable
--------------------

Environment variable ``YDIFF_OPTIONS`` may be used to specify default options
that will be placed at the beginning of the argument list, for example:

.. code-block:: bash

    export YDIFF_OPTIONS='-w100'
    ydiff foo                   # equivalent to "ydiff -w100 foo"

Note the default pager ``less`` takes options from the environment variable
``LESS``.

Notes
-----

If you feel more comfortable with a command such as ``git ydiff`` to trigger
the ydiff command, you may symlink the executable to one named ``git-ydiff``
as follows:

.. code-block:: bash

    ydiff_dir=$(dirname $(which ydiff))
    ln -s "${ydiff_dir}/ydiff" "${ydiff_dir}/git-ydiff"

Known issues
------------

Ydiff has following known issues:

- Side by side mode has alignment problem for wide chars
- Terminal might be in a mess on exception (type ``reset`` can fix it)

Pull requests are very welcome, please make sure your changes can pass unit
tests and regression tests by run ``make docker-test``.

.. vim:set ft=rst et sw=4 sts=4 tw=79:
