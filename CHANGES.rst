
Change log
==========

Version 1.0 (2016-12-31)

  - Use environment variable ``CDIFF_OPTIONS`` to hold default options

Version 0.9.8 (2016-01-16)

  - More robust parser to tolerate evil unified diff

Version 0.9.7 (2015-04-24)

  - Fix unexpected side-by-side output for diff of diff
  - Better color to work with solarized color scheme

Version 0.9.6 (2014-06-20)

  - Fix TypeError exception in auto width logic

Version 0.9.5 (2014-06-19)

  - Option ``--width 0`` now fits terminal size automatically
  - Enable smooth horizontal scrolling with less option ``--shift 1``

Version 0.9.4 (2014-06-04)

  - Respect the ``LESS`` environment variable
  - Support python 3.4
  - Fix curl options in document

Version 0.9.3 (2013-09-28)

  - Moved screenshots to 'gh-pages' branch
  - Handle all keyboard interrupts more completely
  - Explicitly set default encoding to utf-8
  - Fixed broken output diff when I/O with filterdiff in nonblocking mode

Version 0.9.2 (2013-06-21)

  - Enahanced option parser now pass unknown option to underneath revision
    control, user can use ``cdiff --cached``, ``cdiff -U5`` directly

Version 0.9.1 (2013-05-20)

  - Use ``--no-ext-diff`` to disable GIT_EXTERNAL_DIFF and diff.external which
    might break cdiff output

Version 0.9 (2013-03-23)

  - Supports reading context diff via ``filterdiff`` (patchutils)
  - Fixed a diff parser bug which misread git commit message as common line
  - Lots of code refactor

Version 0.8 (2013-03-13)

  - Parser is now robust enough to handle dangling headers and short patch
  - PEP8 (with minor own flavors) and other code lint
  - Change 'Development Status' to stable

Version 0.7.1 (2013-02-25)

  - Handle 'Binary files ... differ'
  - Document update for known issues

Version 0.7 (2013-02-23)

  - Support reading diff or log for given files/dirs in workspace
  - Support diff generated from ``diff -ru dir1 dir2``
  - Usage change: reading a patch and comparing two files need stdin redirect

Version 0.6 (2013-02-20)

  - A few performance tuning and code clean up
  - Add unit test cases with coverage 70%
  - Show merge history in svn log

Version 0.5.1 (2013-02-19)

  - Fixed incorrect yield on diff missing eof
  - Fixed a bug in diff format probe
  - Handle keyboard interrupt and large diffs in non-color mode
  - Code clean up

Version 0.5 (2013-02-18)

  - Support read output from ``svn diff --log`` and ``hg log -p``
  - Streamline reading large patch set
  - New ``--log (-l)`` option to read revision control diff log (thanks to
    `Steven Myint`_)

Version 0.4 (2013-02-16)

  - New option *-c WHEN* (*--color WHEN*) to support auto test
  - Auto regression test now on Travis

Version 0.3 (2013-02-07)

  - Support compare two files (wrapper of diff)

Version 0.2 (2013-02-06)

  - Move cdiff.py to top dir for better meta info management

Version 0.1 (2013-02-05)

  - New --version option
  - setup.py now read version from source code

Version 0.0.4 (2013-02-04)

  - Add CHANGES for history track and better versioning

Version 0.0.3 (2013-02-04)

  - Publish on PyPI, supports read patch from file, pipe and diff output from
    revision tools (thanks to `Steven Myint`_)

.. _Steven Myint: https://github.com/myint

.. vim:set ft=rst et sw=4 sts=4 tw=79:
