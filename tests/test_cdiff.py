#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Unit test for cdiff"""

import sys
if sys.hexversion < 0x02050000:
    raise SystemExit("*** Requires python >= 2.5.0")

import unittest
import tempfile
import subprocess
import os

sys.path.insert(0, '')
import cdiff


class Sequential(object):
    """A non-seekable iterator, mock of file object"""

    def __init__(self, items):
        self._items = items
        self._index = 0

    def __iter__(self):
        while True:
            try:
                item = self._items[self._index]
            except IndexError:
                raise StopIteration
            yield item
            self._index += 1

    def readline(self):
        try:
            item = self._items[self._index]
        except IndexError:
            return ''
        self._index += 1
        return item


class TestPatchStream(unittest.TestCase):

    def test_is_empty(self):
        stream = cdiff.PatchStream(Sequential([]))
        self.assertTrue(stream.is_empty())

        stream = cdiff.PatchStream(Sequential(['hello', 'world']))
        self.assertFalse(stream.is_empty())

    def test_read_stream_header(self):
        stream = cdiff.PatchStream(Sequential([]))
        self.assertEqual(stream.read_stream_header(1), [])

        items = ['hello', 'world', 'again']

        stream = cdiff.PatchStream(Sequential(items))
        self.assertEqual(stream.read_stream_header(2), items[:2])

        stream = cdiff.PatchStream(Sequential(items))
        self.assertEqual(stream.read_stream_header(4), items[:])

    def test_iter_after_read_stream_header(self):
        items = ['hello', 'world', 'again', 'and', 'again']
        stream = cdiff.PatchStream(Sequential(items))

        _ = stream.read_stream_header(2)
        out = list(stream)
        self.assertEqual(out, items)


class TestHunk(unittest.TestCase):

    def test_get_old_text(self):
        hunk = cdiff.Hunk([], '@@ -1,2 +1,2 @@', (1,2), (1,2))
        hunk.append(('-', 'foo\n'))
        hunk.append(('+', 'bar\n'))
        hunk.append((' ', 'common\n'))
        self.assertEqual(hunk._get_old_text(), ['foo\n', 'common\n'])

    def test_get_new_text(self):
        hunk = cdiff.Hunk([], '@@ -1,2 +1,2 @@', (1,2), (1,2))
        hunk.append(('-', 'foo\n'))
        hunk.append(('+', 'bar\n'))
        hunk.append((' ', 'common\n'))
        self.assertEqual(hunk._get_new_text(), ['bar\n', 'common\n'])


class TestDiff(unittest.TestCase):

    def _init_diff(self):
        hunk = cdiff.Hunk(['hunk header\n'], '@@ -1,2 +1,2 @@\n', (1,2), (1,2))
        hunk.append(('-', 'hella\n'))
        hunk.append(('+', 'hello\n'))
        hunk.append((' ', 'world\n'))
        diff = cdiff.Diff(['header\n'], '--- old\n', '+++ new\n', [hunk])
        return diff

    def test_markup_mix(self):
        line = 'foo \x00-del\x01 \x00+add\x01 \x00^chg\x01 bar'
        base_color = 'red'
        diff = cdiff.Diff(None, None, None, None)
        self.assertEqual(diff._markup_mix(line, base_color),
                '\x1b[31mfoo \x1b[7m\x1b[31mdel\x1b[0m\x1b[31m '
                '\x1b[7m\x1b[31madd\x1b[0m\x1b[31m '
                '\x1b[4m\x1b[31mchg\x1b[0m\x1b[31m bar\x1b[0m')

    def test_markup_traditional(self):
        diff = self._init_diff()
        out = list(diff.markup_traditional())
        self.assertEqual(len(out), 8)

        sys.stdout.write('\n')
        for markup in out:
            sys.stdout.write(markup)

        self.assertEqual(out[0], '\x1b[36mheader\n\x1b[0m')
        self.assertEqual(out[1], '\x1b[33m--- old\n\x1b[0m')
        self.assertEqual(out[2], '\x1b[33m+++ new\n\x1b[0m')
        self.assertEqual(out[3], '\x1b[1;36mhunk header\n\x1b[0m')
        self.assertEqual(out[4], '\x1b[1;34m@@ -1,2 +1,2 @@\n\x1b[0m')
        self.assertEqual(out[5],
                '\x1b[1;31m-\x1b[0m\x1b[31mhell\x1b[4m'
                '\x1b[31ma\x1b[0m\x1b[31m\n\x1b[0m')
        self.assertEqual(out[6],
                '\x1b[1;32m+\x1b[0m\x1b[32mhell\x1b[4m'
                '\x1b[32mo\x1b[0m\x1b[32m\n\x1b[0m')
        self.assertEqual(out[7], '\x1b[0m world\n\x1b[0m')

    def test_markup_side_by_side_padded(self):
        diff = self._init_diff()
        out = list(diff.markup_side_by_side(6))
        self.assertEqual(len(out), 7)

        sys.stdout.write('\n')
        for markup in out:
            sys.stdout.write(markup)

        self.assertEqual(out[0], '\x1b[36mheader\n\x1b[0m')
        self.assertEqual(out[1], '\x1b[33m--- old\n\x1b[0m')
        self.assertEqual(out[2], '\x1b[33m+++ new\n\x1b[0m')
        self.assertEqual(out[3], '\x1b[1;36mhunk header\n\x1b[0m')
        self.assertEqual(out[4], '\x1b[1;34m@@ -1,2 +1,2 @@\n\x1b[0m')
        self.assertEqual(out[5],
                '\x1b[33m1\x1b[0m '
                '\x1b[31mhell\x1b[4m\x1b[31ma\x1b[0m\x1b[31m\x1b[0m  '
                '\x1b[0m\x1b[33m1\x1b[0m '
                '\x1b[32mhell\x1b[4m\x1b[32mo\x1b[0m\x1b[32m\x1b[0m\n')
        self.assertEqual(out[6],
                '\x1b[33m2\x1b[0m '
                '\x1b[0mworld\x1b[0m  '
                '\x1b[0m\x1b[33m2\x1b[0m '
                '\x1b[0mworld\x1b[0m\n')

    def test_markup_side_by_side_off_by_one(self):
        diff = self._init_diff()
        out = list(diff.markup_side_by_side(5))
        self.assertEqual(len(out), 7)

        sys.stdout.write('\n')
        for markup in out:
            sys.stdout.write(markup)

        self.assertEqual(out[0], '\x1b[36mheader\n\x1b[0m')
        self.assertEqual(out[1], '\x1b[33m--- old\n\x1b[0m')
        self.assertEqual(out[2], '\x1b[33m+++ new\n\x1b[0m')
        self.assertEqual(out[3], '\x1b[1;36mhunk header\n\x1b[0m')
        self.assertEqual(out[4], '\x1b[1;34m@@ -1,2 +1,2 @@\n\x1b[0m')
        self.assertEqual(out[5],
                '\x1b[33m1\x1b[0m '
                '\x1b[31mhell\x1b[4m\x1b[31ma\x1b[0m '
                '\x1b[0m\x1b[33m1\x1b[0m '
                '\x1b[32mhell\x1b[4m\x1b[32mo\x1b[0m\n')
        self.assertEqual(out[6],
                '\x1b[33m2\x1b[0m '
                '\x1b[0mworld\x1b[0m '
                '\x1b[0m\x1b[33m2\x1b[0m '
                '\x1b[0mworld\x1b[0m\n')

    def test_markup_side_by_side_wrapped(self):
        diff = self._init_diff()
        out = list(diff.markup_side_by_side(4))
        self.assertEqual(len(out), 7)

        sys.stdout.write('\n')
        for markup in out:
            sys.stdout.write(markup)

        self.assertEqual(out[0], '\x1b[36mheader\n\x1b[0m')
        self.assertEqual(out[1], '\x1b[33m--- old\n\x1b[0m')
        self.assertEqual(out[2], '\x1b[33m+++ new\n\x1b[0m')
        self.assertEqual(out[3], '\x1b[1;36mhunk header\n\x1b[0m')
        self.assertEqual(out[4], '\x1b[1;34m@@ -1,2 +1,2 @@\n\x1b[0m')
        self.assertEqual(out[5],
                '\x1b[33m1\x1b[0m '
                '\x1b[31mhel\x1b[0m\x1b[1;35m>\x1b[0m '
                '\x1b[0m\x1b[33m1\x1b[0m '
                '\x1b[32mhel\x1b[0m\x1b[1;35m>\x1b[0m\n')
        self.assertEqual(out[6],
                '\x1b[33m2\x1b[0m '
                '\x1b[0mwor\x1b[0m\x1b[1;35m>\x1b[0m '
                '\x1b[0m\x1b[33m2\x1b[0m '
                '\x1b[0mwor\x1b[0m\x1b[1;35m>\x1b[0m\n')


class TestUdiff(unittest.TestCase):

    diff = cdiff.Udiff(None, None, None, None)

    def test_is_hunk_meta_normal(self):
        self.assertTrue(self.diff.is_hunk_meta('@@ -1 +1 @@'))
        self.assertTrue(self.diff.is_hunk_meta('@@ -3,7 +3,6 @@'))
        self.assertTrue(self.diff.is_hunk_meta('@@ -3,7 +3,6 @@ class Foo'))
        self.assertTrue(self.diff.is_hunk_meta('@@ -3,7 +3,6 @@ class Foo\n'))
        self.assertTrue(self.diff.is_hunk_meta('@@ -3,7 +3,6 @@ class Foo\r\n'))

    def test_is_hunk_meta_svn_prop(self):
        self.assertTrue(self.diff.is_hunk_meta('## -0,0 +1 ##'))
        self.assertTrue(self.diff.is_hunk_meta('## -0,0 +1 ##\n'))
        self.assertTrue(self.diff.is_hunk_meta('## -0,0 +1 ##\r\n'))

    def test_is_hunk_meta_neg(self):
        self.assertFalse(self.diff.is_hunk_meta('@@ -1 + @@'))
        self.assertFalse(self.diff.is_hunk_meta('@@ -this is not a hunk meta'))
        self.assertFalse(self.diff.is_hunk_meta('## -this is not either'))

    def test_parse_hunk_meta_normal(self):
        self.assertEqual(
                self.diff.parse_hunk_meta('@@ -3,7 +3,6 @@'),
                ((3, 7), (3, 6)))

    def test_parse_hunk_meta_missing(self):
        self.assertEqual(
                self.diff.parse_hunk_meta('@@ -3 +3,6 @@'),
                ((3, 0), (3, 6)))
        self.assertEqual(
                self.diff.parse_hunk_meta('@@ -3,7 +3 @@'),
                ((3, 7), (3, 0)))
        self.assertEqual(
                self.diff.parse_hunk_meta('@@ -3 +3 @@'),
                ((3, 0), (3, 0)))

    def test_parse_hunk_meta_svn_prop(self):
        self.assertEqual(
                self.diff.parse_hunk_meta('## -0,0 +1 ##'),
                ((0, 0), (1, 0)))

    def test_is_old(self):
        self.assertTrue(self.diff.is_old('-hello world'))
        self.assertTrue(self.diff.is_old('----'))           # yaml

    def test_is_old_neg(self):
        self.assertFalse(self.diff.is_old('--- considered as old path'))
        self.assertFalse(self.diff.is_old('-------------')) # svn log --diff

    def test_is_new(self):
        self.assertTrue(self.diff.is_new('+hello world'))
        self.assertTrue(self.diff.is_new('++++hello world'))

    def test_is_new_neg(self):
        self.assertFalse(self.diff.is_new('+++ considered as new path'))


class TestDiffParser(unittest.TestCase):

    def test_type_detect(self):
        patch = r"""\
spam
--- a
+++ b
@@ -1,2 +1,2 @@
"""
        items = patch.splitlines(True)
        stream = cdiff.PatchStream(Sequential(items))
        parser = cdiff.DiffParser(stream)
        self.assertEqual(parser._type, 'udiff')

    def test_type_detect_neg(self):
        patch = r"""\
spam
--- a
+++ b
spam
"""
        items = patch.splitlines(True)
        stream = cdiff.PatchStream(Sequential(items))
        self.assertRaises(RuntimeError, cdiff.DiffParser, stream)

    def test_parse_dangling_header(self):
        patch = r"""\
--- a
+++ b
@@ -1,2 +1,2 @@
-foo
+bar
 common
spam
"""
        items = patch.splitlines(True)
        stream = cdiff.PatchStream(Sequential(items))
        parser = cdiff.DiffParser(stream)
        self.assertRaises(RuntimeError, list, parser._parse())

    def test_parse_missing_new_path(self):
        patch = r"""\
--- a
+++ b
@@ -1,2 +1,2 @@
-foo
+bar
 common
--- c
"""
        items = patch.splitlines(True)
        stream = cdiff.PatchStream(Sequential(items))
        parser = cdiff.DiffParser(stream)
        self.assertRaises(AssertionError, list, parser._parse())

    def test_parse_missing_hunk(self):
        patch = r"""\
--- a
+++ b
@@ -1,2 +1,2 @@
-foo
+bar
 common
--- c
+++ d
"""
        items = patch.splitlines(True)
        stream = cdiff.PatchStream(Sequential(items))
        parser = cdiff.DiffParser(stream)
        self.assertRaises(AssertionError, list, parser._parse())

    def test_parse_svn_prop(self):
        patch = r"""\
--- a
+++ b
Added: svn:executable
## -0,0 +1 ##
+*
\ No newline at end of property
Added: svn:keywords
## -0,0 +1 ##
+Id
"""
        items = patch.splitlines(True)
        stream = cdiff.PatchStream(Sequential(items))
        parser = cdiff.DiffParser(stream)
        out = list(parser._parse())
        self.assertEqual(len(out), 1)
        self.assertEqual(len(out[0]._hunks), 2)

        hunk = out[0]._hunks[1]
        self.assertEqual(hunk._hunk_headers, ['Added: svn:keywords\n'])
        self.assertEqual(hunk._hunk_list, [('+', 'Id\n')])


class TestMain(unittest.TestCase):

    def setUp(self):
        self._cwd = os.getcwd()
        self._ws = tempfile.mkdtemp(prefix='test_cdiff')
        self._non_ws = tempfile.mkdtemp(prefix='test_cdiff')
        cmd = ('cd %s; git init; git config user.name me; '
               'git config user.email me@example.org') % self._ws
        subprocess.call(cmd, shell=True, stdout=subprocess.PIPE)
        self._change_file('init')

    def tearDown(self):
        os.chdir(self._cwd)
        cmd = ['/bin/rm', '-rf', self._ws, self._non_ws]
        subprocess.call(cmd)

    def _change_file(self, text):
        cmd = ['/bin/sh', '-c',
               'cd %s; echo "%s" > foo' % (self._ws, text)]
        subprocess.call(cmd)

    def _commit_file(self):
        cmd = ['/bin/sh', '-c',
               'cd %s; git add foo; git commit foo -m update' % self._ws]
        subprocess.call(cmd, stdout=subprocess.PIPE)

    def test_too_many_args(self):
        sys.argv = [sys.argv[0], 'a', 'b', 'c']
        self.assertNotEqual(cdiff.main(), 0)

    def test_read_diff(self):
        sys.argv = sys.argv[:1]
        self._change_file('read_diff')

        os.chdir(self._ws)
        ret = cdiff.main()
        os.chdir(self._cwd)
        self.assertEqual(ret, 0)

    def test_read_diff_neg(self):
        sys.argv = sys.argv[:1]
        os.chdir(self._non_ws)
        ret = cdiff.main()
        os.chdir(self._cwd)
        self.assertNotEqual(ret, 0)

    def test_read_log(self):
        sys.argv = [sys.argv[0], '--log']
        self._change_file('read_log')
        self._commit_file()

        os.chdir(self._ws)
        ret = cdiff.main()
        os.chdir(self._cwd)
        self.assertEqual(ret, 0)

    def test_read_log_neg(self):
        sys.argv = [sys.argv[0], '--log']
        os.chdir(self._non_ws)
        ret = cdiff.main()
        os.chdir(self._cwd)
        self.assertNotEqual(ret, 0)


if __name__ == '__main__':
    unittest.main()

# vim:set et sts=4 sw=4 tw=80:
