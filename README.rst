Cdiff
=====

View **colored**, **incremental** diff in unified format or **side by side**
with **auto pager**.  Requires python (>= 2.5.0) and ``less``.

.. image: http://ymattw.github.com/cdiff/img/default.png
   :alt: default

.. image: http://ymattw.github.com/cdiff/img/side-by-side.png
   :alt: side by side

Installation
------------

Cdiff is not in PyPI yet, so far you could download the script directly or use
the ``setup.py`` to install.
 
**Download directly**

Save `src/cdiff.py <https://raw.github.com/ymattw/cdiff/master/src/cdiff.py>` to
whatever directory which is in your ``$PATH``, for example, ``$HOME/bin`` is in
my ``$PATH``, so I save the script there and name as ``cdiff``.

    curl -ksS https://raw.github.com/ymattw/cdiff/master/src/cdiff.py > ~/bin/cdiff
    chmod +x ~/bin/cdiff

**Install with the setup.py**

You can run the setup.py from the source to install ``cdiff`` to system wide
directory.

    git clone https://github.com/ymattw/cdiff.git
    cd cdiff
    sudo ./setup.py install

This usually installs it as ``/usr/local/bin/cdiff``.

Usage
-----

Cdiff reads diff from diff (patch) file if given, or stdin if redirected, or
diff produced by revision tool if in a git/svn/hg workspace.  Use option ``-s``
to enable side by side view, and option ``-w N`` to set a text width other than
default ``80``.  See examples below.

Show usage:

    cdiff -h

View a diff (patch) file:

    cdiff foo.patch             # view colored incremental udiff
    cdiff foo.patch -s          # view side by side
    cdiff foo.patch -s -w 90    # use text width 90 other than default 80

Read diff from local modification in a svn, git, or hg workspace:

    cd proj-workspace
    cdiff
    cdiff -s
    cdiff -s -w 90

Pipe in a diff:

    svn diff -r PREV | cdiff -s
    git log -p -2 | cdiff -s
    git show <commit> | cdiff -s

Redirect output to another patch file is safe:

    svn diff | cdiff -s > my.patch

Known issue
-----------

- Only support unified format for input diff
- Side by side mode has alignment problem for wide chars
