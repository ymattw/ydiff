Ydiff
=====

.. image:: https://github.com/ymattw/ydiff/actions/workflows/test.yml/badge.svg
   :alt: Tests status
   :target: https://github.com/ymattw/ydiff/actions

Ydiff is a terminal-based tool to view *colored*, *incremental* diffs in
a version-controlled workspace or from stdin, in *side-by-side* (similar to
``diff -y``) or unified mode, and *auto-paged*. It only requires Python >= 3.3
*without external dependencies* and ``less`` as a pager.

The diffs in side-by-side mode appear below. See also the `screenshots`_ of the
unified mode.

.. _`screenshots`: https://github.com/ymattw/ydiff/tree/26857b8/img

*Theme "default" on a dark terminal background:*

.. image:: https://raw.githubusercontent.com/ymattw/ydiff/26857b8/img/darkbg-side-by-side-default.png
   :alt: side by side, theme 'default' on a dark background
   :align: center
   :height: 300 px

*Theme "default" on a light terminal background:*

.. image:: https://raw.githubusercontent.com/ymattw/ydiff/26857b8/img/lightbg-side-by-side-default.png
   :alt: side by side, theme 'default' on a light background
   :align: center
   :height: 300 px

*Theme "dark" on a dark terminal background:*

.. image:: https://raw.githubusercontent.com/ymattw/ydiff/26857b8/img/darkbg-side-by-side-dark.png
   :alt: side by side, theme 'dark' on a dark background
   :align: center
   :height: 300 px

*Theme "light" on a light terminal background:*

.. image:: https://raw.githubusercontent.com/ymattw/ydiff/26857b8/img/lightbg-side-by-side-light.png
   :alt: side by side, theme 'light' on a light background
   :align: center
   :height: 300 px

Installation
------------

Ydiff only depends on Python built-in libraries, so you can just download the
source and run without worrying about any installation. Git `tagged`_ revisions
will be packaged and uploaded to `PyPI`_ timely, however, packages hosted
elsewhere are not (please note they are not managed by the author `@ymattw`_).

.. _`tagged`: https://github.com/ymattw/ydiff/tags
.. _`PyPI`: http://pypi.python.org/pypi/ydiff
.. _`@ymattw`: https://github.com/ymattw

To run from source directly, just save `ydiff.py`_ as ``ydiff`` to whatever
directory which is in your ``$PATH``, for example, ``$HOME/bin``:

.. _`ydiff.py`: https://raw.github.com/ymattw/ydiff/master/ydiff.py

.. code-block:: bash

    curl -L https://raw.github.com/ymattw/ydiff/master/ydiff.py > ~/bin/ydiff
    chmod +x ~/bin/ydiff

To install from `PyPI`_:

.. code-block:: bash

    pip install --upgrade ydiff

To install with Homebrew (`Formula`_) on macOS:

.. _`Formula`: https://github.com/Homebrew/homebrew-core/blob/master/Formula/y/ydiff.rb

.. code-block:: bash

    brew install ydiff

To install on Fedora:

.. code-block:: bash

    dnf install ydiff

To install on FreeBSD:

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
      -c WHEN, --color=WHEN
                            colorize mode 'auto' (default), 'always', or 'never'
      -t N, --tab-width=N   convert tab chars to this many spaces (default: 8)
      --wrap                wrap long lines in side-by-side mode (default True;
                            DEPRECATED)
      --nowrap, --no-wrap   do not wrap long lines in side-by-side mode
      -p PAGER, --pager=PAGER
                            pager application to feed output to, default is 'less'
      -o OPT, --pager-options=OPT
                            options to supply to pager application
      --theme=THEME         option to pick a color theme (one of default, dark,
                            light)

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

    ydiff -p more                   # use "more" as a pager
    ydiff -p cat                    # when neither less nor more is avilable
    ydiff -o "-FRSX --shift 2"      # custmized option (pager defaults to less)

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

Notes
-----

1. Ydiff only supports diffs in `Unified Format`_. Diffs in other format may be
   converted to Unified Format via tool ``filterdiff`` (usually offered by
   package ``patchutils``.)

   .. _`Unified Format`: https://en.wikipedia.org/wiki/Diff#Unified_format

2. Environment variable ``YDIFF_OPTIONS`` may be used to specify default
   options that will be placed at the beginning of the argument list, for
   example:

   .. code-block:: bash

    export YDIFF_OPTIONS='-w100'
    ydiff foo  # equivalent to "ydiff -w100 foo"

3. If you feel more comfortable with a command such as ``git d`` to trigger the
   ydiff command, you may symlink the executable to one named ``git-d``, or
   configure an alias:

   .. code-block:: bash

    # Create a symlink git-d -> ydiff
    D=$(dirname $(which ydiff)); ln -s ydiff $D/git-d

    # Or configure an alias
    git config --global alias.d '!ydiff'

Known issues
------------

- Wide characters may cause alignment problem in side-by-side mode.
- Terminal might be in a mess on exception (type ``reset`` can fix it).

.. vim:set ft=rst et sw=4 sts=4 tw=79:
