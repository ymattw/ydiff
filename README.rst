Cdiff
=====

Term based tool to view **colored**, **incremental** diff in unified format or
**side by side** with **auto pager**.  Requires python (>= 2.5.0) and ``less``.

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
 
    sudo pip install cdiff

Install with setup.py
~~~~~~~~~~~~~~~~~~~~~

You can also run the setup.py from the source if you don't have ``pip``.

.. code:: sh

    git clone https://github.com/ymattw/cdiff.git
    cd cdiff
    sudo ./setup.py install

Download directly
~~~~~~~~~~~~~~~~~

Both ``pip`` and ``setup.py`` installs cdiff to system wide directory, if you
want a minimal tool without the boring external dependencies (like me), just
save `src/cdiff.py <https://raw.github.com/ymattw/cdiff/master/src/cdiff.py>`_
to whatever directory which is in your ``$PATH``, for example, ``$HOME/bin`` is
in my ``$PATH``, so I save the script there and name as ``cdiff``.

.. code:: sh

    curl -ksS https://raw.github.com/ymattw/cdiff/master/src/cdiff.py > ~/bin/cdiff
    chmod +x ~/bin/cdiff

Usage
-----

Cdiff reads diff from diff (patch) file if given, or stdin if redirected, or
diff produced by revision tool if in a git/svn/hg workspace.  Use option ``-s``
to enable side by side view, and option ``-w N`` to set a text width other than
default ``80``.  See examples below.

Show usage::

    cdiff -h

View a diff (patch) file:

.. code:: sh

    cdiff foo.patch             # view colored incremental udiff
    cdiff foo.patch -s          # view side by side
    cdiff foo.patch -s -w 90    # use text width 90 other than default 80

Read diff from local modification in a svn, git, or hg workspace:

.. code:: sh

    cd proj-workspace
    cdiff
    cdiff -s
    cdiff -s -w 90

Pipe in a diff:

.. code:: sh

    git log -p -2 | cdiff -s
    git show 15bfa56 | cdiff -s
    svn diff -r PREV | cdiff -s

Redirect output to another patch file is safe:

.. code:: sh

    svn diff | cdiff -s > my.patch

Known issue
-----------

- Only support unified diff for input format
- Side by side mode has alignment problem for wide chars

See also
--------

I have another tool `coderev <https://github.com/ymattw/coderev>`_ which
generates side-by-side diff pages for code review from two given files or
directories, I found it's not easy to extend to support git so invented
`cdiff`.  Idea of ansi color markup is also from project `colordiff
<https://github.com/daveewart/colordiff>`_.

