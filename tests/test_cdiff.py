#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Unit test for cdiff"""

import sys
import unittest
import tempfile
import subprocess
import os

sys.path.insert(0, '')
import cdiff  # nopep8


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


class PatchStreamTest(unittest.TestCase):

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


class DecodeTest(unittest.TestCase):

    def test_normal(self):
        utext = 'hello'.encode('utf-8')
        self.assertEqual('hello', cdiff.decode(utext))

    def test_latin_1(self):
        text = '\x80\x02q\x01(U'
        if sys.version_info[0] == 2:
            decoded_text = text.decode('latin-1')
        else:
            decoded_text = text
        self.assertEqual(decoded_text, cdiff.decode(text))


class HunkTest(unittest.TestCase):

    def test_get_old_text(self):
        hunk = cdiff.Hunk([], '@@ -1,2 +1,2 @@', (1, 2), (1, 2))
        hunk.append(('-', 'foo\n'))
        hunk.append(('+', 'bar\n'))
        hunk.append((' ', 'common\n'))
        self.assertEqual(hunk._get_old_text(), ['foo\n', 'common\n'])

    def test_get_new_text(self):
        hunk = cdiff.Hunk([], '@@ -1,2 +1,2 @@', (1, 2), (1, 2))
        hunk.append(('-', 'foo\n'))
        hunk.append(('+', 'bar\n'))
        hunk.append((' ', 'common\n'))
        self.assertEqual(hunk._get_new_text(), ['bar\n', 'common\n'])


class DiffMarkupTest(unittest.TestCase):

    def _init_diff(self):
        """Return a minimal diff contains all required samples
            header
            --- old
            +++ new
            hunk header
            @@ -1,4 +1,4 @@
            -hhello
            +helloo
            +spammm
             world
            -garb
            -Again
            +again
        """

        hunk = cdiff.Hunk(['hunk header\n'], '@@ -1,4 +1,4 @@\n',
                          (1, 4), (1, 4))
        hunk.append(('-', 'hhello\n'))
        hunk.append(('+', 'helloo\n'))
        hunk.append(('+', 'spammm\n'))
        hunk.append((' ', 'world\n'))
        hunk.append(('-', 'garb\n'))
        hunk.append(('-', 'Again\n'))
        hunk.append(('+', 'again\n'))
        diff = cdiff.UnifiedDiff(
            ['header\n'], '--- old\n', '+++ new\n', [hunk])
        return diff

    def test_markup_mix(self):
        marker = cdiff.DiffMarker()
        line = 'foo \x00-del\x01 \x00+add\x01 \x00^chg\x01 bar'
        base_color = 'red'
        self.assertEqual(
            marker._markup_mix(line, base_color),
            '\x1b[31mfoo \x1b[7m\x1b[31mdel\x1b[0m\x1b[31m '
            '\x1b[7m\x1b[31madd\x1b[0m\x1b[31m '
            '\x1b[4m\x1b[31mchg\x1b[0m\x1b[31m bar\x1b[0m')

    def test_markup_traditional_hunk_header(self):
        hunk = cdiff.Hunk(['hunk header\n'], '@@ -0 +0 @@\n', (0, 0), (0, 0))
        diff = cdiff.UnifiedDiff([], '--- old\n', '+++ new\n', [hunk])
        marker = cdiff.DiffMarker()

        out = list(marker._markup_traditional(diff))
        self.assertEqual(len(out), 4)

        self.assertEqual(out[0], '\x1b[33m--- old\n\x1b[0m')
        self.assertEqual(out[1], '\x1b[33m+++ new\n\x1b[0m')
        self.assertEqual(out[2], '\x1b[1;36mhunk header\n\x1b[0m')
        self.assertEqual(out[3], '\x1b[1;34m@@ -0 +0 @@\n\x1b[0m')

    def test_markup_traditional_old_changed(self):
        hunk = cdiff.Hunk([], '@@ -1 +0,0 @@\n', (1, 0), (0, 0))
        hunk.append(('-', 'spam\n'))
        diff = cdiff.UnifiedDiff([], '--- old\n', '+++ new\n', [hunk])
        marker = cdiff.DiffMarker()

        out = list(marker._markup_traditional(diff))
        self.assertEqual(len(out), 4)

        self.assertEqual(out[0], '\x1b[33m--- old\n\x1b[0m')
        self.assertEqual(out[1], '\x1b[33m+++ new\n\x1b[0m')
        self.assertEqual(out[2], '\x1b[1;34m@@ -1 +0,0 @@\n\x1b[0m')
        self.assertEqual(out[3], '\x1b[1;31m-spam\n\x1b[0m')

    def test_markup_traditional_new_changed(self):
        hunk = cdiff.Hunk([], '@@ -0,0 +1 @@\n', (0, 0), (1, 0))
        hunk.append(('+', 'spam\n'))
        diff = cdiff.UnifiedDiff([], '--- old\n', '+++ new\n', [hunk])
        marker = cdiff.DiffMarker()

        out = list(marker._markup_traditional(diff))
        self.assertEqual(len(out), 4)

        self.assertEqual(out[0], '\x1b[33m--- old\n\x1b[0m')
        self.assertEqual(out[1], '\x1b[33m+++ new\n\x1b[0m')
        self.assertEqual(out[2], '\x1b[1;34m@@ -0,0 +1 @@\n\x1b[0m')
        self.assertEqual(out[3], '\x1b[32m+spam\n\x1b[0m')

    def test_markup_traditional_both_changed(self):
        hunk = cdiff.Hunk([], '@@ -1,2 +1,2 @@\n', (1, 2), (1, 2))
        hunk.append(('-', 'hella\n'))
        hunk.append(('+', 'hello\n'))
        hunk.append((' ', 'common\n'))
        diff = cdiff.UnifiedDiff([], '--- old\n', '+++ new\n', [hunk])
        marker = cdiff.DiffMarker()

        out = list(marker._markup_traditional(diff))
        self.assertEqual(len(out), 6)

        self.assertEqual(out[0], '\x1b[33m--- old\n\x1b[0m')
        self.assertEqual(out[1], '\x1b[33m+++ new\n\x1b[0m')
        self.assertEqual(out[2], '\x1b[1;34m@@ -1,2 +1,2 @@\n\x1b[0m')
        self.assertEqual(
            out[3],
            '\x1b[1;31m-\x1b[0m\x1b[31mhell'
            '\x1b[4m\x1b[31ma\x1b[0m\x1b[31m\n\x1b[0m')
        self.assertEqual(
            out[4],
            '\x1b[32m+\x1b[0m\x1b[32mhell'
            '\x1b[4m\x1b[32mo\x1b[0m\x1b[32m\n\x1b[0m')
        self.assertEqual(out[5], '\x1b[0m common\n\x1b[0m')

    def test_markup_side_by_side_padded(self):
        diff = self._init_diff()
        marker = cdiff.DiffMarker()

        out = list(marker._markup_side_by_side(diff, 7))
        self.assertEqual(len(out), 10)

        sys.stdout.write('\n')
        for markup in out:
            sys.stdout.write(markup)

        self.assertEqual(out[0], '\x1b[36mheader\n\x1b[0m')
        self.assertEqual(out[1], '\x1b[33m--- old\n\x1b[0m')
        self.assertEqual(out[2], '\x1b[33m+++ new\n\x1b[0m')
        self.assertEqual(out[3], '\x1b[1;36mhunk header\n\x1b[0m')
        self.assertEqual(out[4], '\x1b[1;34m@@ -1,4 +1,4 @@\n\x1b[0m')
        self.assertEqual(
            out[5],
            '\x1b[33m1\x1b[0m '
            '\x1b[31m\x1b[7m\x1b[31mh\x1b[0m\x1b[31mhello\x1b[0m  '
            '\x1b[0m\x1b[33m1\x1b[0m '
            '\x1b[32mhello\x1b[7m\x1b[32mo\x1b[0m\x1b[32m\x1b[0m\n')
        self.assertEqual(
            out[6],
            '\x1b[33m '
            '\x1b[0m         '
            '\x1b[0m\x1b[33m2\x1b[0m '
            '\x1b[32mspammm\x1b[0m\n')
        self.assertEqual(
            out[7],
            '\x1b[33m2\x1b[0m '
            '\x1b[0mworld\x1b[0m   '
            '\x1b[0m\x1b[33m3\x1b[0m '
            '\x1b[0mworld\x1b[0m\n')
        self.assertEqual(
            out[8],
            '\x1b[33m3\x1b[0m '
            '\x1b[1;31mgarb\x1b[0m '
            '\x1b[0m\x1b[33m '
            '\x1b[0m \n')
        self.assertEqual(
            out[9],
            '\x1b[33m4\x1b[0m '
            '\x1b[31m\x1b[4m\x1b[31mA\x1b[0m\x1b[31mgain\x1b[0m   '
            '\x1b[0m\x1b[33m4\x1b[0m '
            '\x1b[32m\x1b[4m\x1b[32ma\x1b[0m\x1b[32mgain\x1b[0m\n')

    # This test is not valid anymore
    def __test_markup_side_by_side_neg_width(self):
        diff = self._init_diff()
        marker = cdiff.DiffMarker()
        out = list(marker._markup_side_by_side(diff, -1))
        self.assertEqual(len(out), 10)

        self.assertEqual(out[0], '\x1b[36mheader\n\x1b[0m')
        self.assertEqual(out[1], '\x1b[33m--- old\n\x1b[0m')
        self.assertEqual(out[2], '\x1b[33m+++ new\n\x1b[0m')
        self.assertEqual(out[3], '\x1b[1;36mhunk header\n\x1b[0m')
        self.assertEqual(out[4], '\x1b[1;34m@@ -1,4 +1,4 @@\n\x1b[0m')
        self.assertEqual(
            out[5],
            '\x1b[33m1\x1b[0m '
            '\x1b[31m\x1b[7m\x1b[31mh\x1b[0m\x1b[31mhello\x1b[0m ' +
            (' ' * 74) +
            '\x1b[0m\x1b[33m1\x1b[0m '
            '\x1b[32mhello\x1b[7m\x1b[32mo\x1b[0m\x1b[32m\x1b[0m\n')
        self.assertEqual(
            out[6],
            '\x1b[33m '
            '\x1b[0m  ' + (' ' * 80) +
            '\x1b[0m\x1b[33m2\x1b[0m '
            '\x1b[32mspammm\x1b[0m\n')
        self.assertEqual(
            out[7],
            '\x1b[33m2\x1b[0m '
            '\x1b[0mworld\x1b[0m ' + (' ' * 75) +
            '\x1b[0m\x1b[33m3\x1b[0m '
            '\x1b[0mworld\x1b[0m\n')
        self.assertEqual(
            out[8],
            '\x1b[33m3\x1b[0m '
            '\x1b[1;31mgarb\x1b[0m '
            '\x1b[0m\x1b[33m '
            '\x1b[0m \n')
        self.assertEqual(
            out[9],
            '\x1b[33m4\x1b[0m '
            '\x1b[31m\x1b[4m\x1b[31mA\x1b[0m\x1b[31mgain\x1b[0m ' +
            (' ' * 75) +
            '\x1b[0m\x1b[33m4\x1b[0m '
            '\x1b[32m\x1b[4m\x1b[32ma\x1b[0m\x1b[32mgain\x1b[0m\n')

    def test_markup_side_by_side_off_by_one(self):
        diff = self._init_diff()
        marker = cdiff.DiffMarker()
        out = list(marker._markup_side_by_side(diff, 6))
        self.assertEqual(len(out), 10)

        sys.stdout.write('\n')
        for markup in out:
            sys.stdout.write(markup)

        self.assertEqual(out[0], '\x1b[36mheader\n\x1b[0m')
        self.assertEqual(out[1], '\x1b[33m--- old\n\x1b[0m')
        self.assertEqual(out[2], '\x1b[33m+++ new\n\x1b[0m')
        self.assertEqual(out[3], '\x1b[1;36mhunk header\n\x1b[0m')
        self.assertEqual(out[4], '\x1b[1;34m@@ -1,4 +1,4 @@\n\x1b[0m')
        self.assertEqual(
            out[5],
            '\x1b[33m1\x1b[0m '
            '\x1b[31m\x1b[7m\x1b[31mh\x1b[0m\x1b[31mhello\x1b[0m '
            '\x1b[0m\x1b[33m1\x1b[0m '
            '\x1b[32mhello\x1b[7m\x1b[32mo\x1b[0m\n')
        self.assertEqual(
            out[6],
            '\x1b[33m \x1b[0m        '
            '\x1b[0m\x1b[33m2\x1b[0m '
            '\x1b[32mspammm\x1b[0m\n')
        self.assertEqual(
            out[7],
            '\x1b[33m2\x1b[0m '
            '\x1b[0mworld\x1b[0m  '
            '\x1b[0m\x1b[33m3\x1b[0m '
            '\x1b[0mworld\x1b[0m\n')
        self.assertEqual(
            out[8],
            '\x1b[33m3\x1b[0m '
            '\x1b[1;31mgarb\x1b[0m '
            '\x1b[0m\x1b[33m '
            '\x1b[0m \n')
        self.assertEqual(
            out[9],
            '\x1b[33m4\x1b[0m '
            '\x1b[31m\x1b[4m\x1b[31mA\x1b[0m\x1b[31mgain\x1b[0m  '
            '\x1b[0m\x1b[33m4\x1b[0m '
            '\x1b[32m\x1b[4m\x1b[32ma\x1b[0m\x1b[32mgain\x1b[0m\n')

    def test_markup_side_by_side_wrapped(self):
        diff = self._init_diff()
        marker = cdiff.DiffMarker()
        out = list(marker._markup_side_by_side(diff, 5))
        self.assertEqual(len(out), 10)

        sys.stdout.write('\n')
        for markup in out:
            sys.stdout.write(markup)

        self.assertEqual(out[0], '\x1b[36mheader\n\x1b[0m')
        self.assertEqual(out[1], '\x1b[33m--- old\n\x1b[0m')
        self.assertEqual(out[2], '\x1b[33m+++ new\n\x1b[0m')
        self.assertEqual(out[3], '\x1b[1;36mhunk header\n\x1b[0m')
        self.assertEqual(out[4], '\x1b[1;34m@@ -1,4 +1,4 @@\n\x1b[0m')
        self.assertEqual(
            out[5],
            '\x1b[33m1\x1b[0m '
            '\x1b[31m\x1b[7m\x1b[31mh\x1b[0m\x1b[31mhel\x1b[0m\x1b[1;35m>\x1b[0m '  # nopep8
            '\x1b[0m\x1b[33m1\x1b[0m '
            '\x1b[32mhell\x1b[0m\x1b[1;35m>\x1b[0m\n')
        self.assertEqual(
            out[6],
            '\x1b[33m \x1b[0m       '
            '\x1b[0m\x1b[33m2\x1b[0m '
            ''
            '\x1b[32mspam\x1b[0m\x1b[1;35m>\x1b[0m\n')
        self.assertEqual(
            out[7],
            '\x1b[33m2\x1b[0m '
            '\x1b[0mworld\x1b[0m '
            '\x1b[0m\x1b[33m3\x1b[0m '
            '\x1b[0mworld\x1b[0m\n')
        self.assertEqual(
            out[8],
            '\x1b[33m3\x1b[0m '
            '\x1b[1;31mgarb\x1b[0m '
            '\x1b[0m\x1b[33m '
            '\x1b[0m \n')
        self.assertEqual(
            out[9],
            '\x1b[33m4\x1b[0m '
            '\x1b[31m\x1b[4m\x1b[31mA\x1b[0m\x1b[31mgain\x1b[0m '
            '\x1b[0m\x1b[33m4\x1b[0m '
            '\x1b[32m\x1b[4m\x1b[32ma\x1b[0m\x1b[32mgain\x1b[0m\n')


class UnifiedDiffTest(unittest.TestCase):

    diff = cdiff.UnifiedDiff(None, None, None, None)

    def test_is_hunk_meta_normal(self):
        self.assertTrue(self.diff.is_hunk_meta('@@ -1 +1 @@'))
        self.assertTrue(self.diff.is_hunk_meta('@@ -3,7 +3,6 @@'))
        self.assertTrue(self.diff.is_hunk_meta('@@ -3,7 +3,6 @@ class Foo'))
        self.assertTrue(self.diff.is_hunk_meta('@@ -3,7 +3,6 @@ class Foo\n'))
        self.assertTrue(
            self.diff.is_hunk_meta('@@ -3,7 +3,6 @@ class Foo\r\n'))

    def test_is_hunk_meta_svn_prop(self):
        self.assertTrue(self.diff.is_hunk_meta('## -0,0 +1 ##'))
        self.assertTrue(self.diff.is_hunk_meta('## -0,0 +1 ##\n'))
        self.assertTrue(self.diff.is_hunk_meta('## -0,0 +1 ##\r\n'))

    def test_is_hunk_meta_neg(self):
        self.assertFalse(self.diff.is_hunk_meta('@@ -1 + @@'))
        self.assertFalse(self.diff.is_hunk_meta('@@ -this is not a hunk meta'))
        self.assertFalse(self.diff.is_hunk_meta('## -this is not either'))

    def test_parse_hunk_meta_normal(self):
        self.assertEqual(self.diff.parse_hunk_meta('@@ -3,7 +3,6 @@'),
                         ((3, 7), (3, 6)))

    def test_parse_hunk_meta_missing(self):
        self.assertEqual(self.diff.parse_hunk_meta('@@ -3 +3,6 @@'),
                         ((3, 1), (3, 6)))
        self.assertEqual(self.diff.parse_hunk_meta('@@ -3,7 +3 @@'),
                         ((3, 7), (3, 1)))
        self.assertEqual(self.diff.parse_hunk_meta('@@ -3 +3 @@'),
                         ((3, 1), (3, 1)))

    def test_parse_hunk_meta_svn_prop(self):
        self.assertEqual(self.diff.parse_hunk_meta('## -0,0 +1 ##'),
                         ((0, 0), (1, 1)))

    def test_is_old(self):
        self.assertTrue(self.diff.is_old('-hello world'))
        self.assertTrue(self.diff.is_old('----'))            # yaml

    def test_is_old_neg(self):
        self.assertFalse(self.diff.is_old('--- considered as old path'))
        self.assertFalse(self.diff.is_old('-' * 72))         # svn log --diff

    def test_is_new(self):
        self.assertTrue(self.diff.is_new('+hello world'))
        self.assertTrue(self.diff.is_new('++++hello world'))

    def test_is_new_neg(self):
        self.assertFalse(self.diff.is_new('+++ considered as new path'))


class DiffParserTest(unittest.TestCase):

    def test_type_detect_unified(self):
        patch = """\
spam
--- a
+++ b
@@ -1,2 +1,2 @@
"""
        items = patch.splitlines(True)
        stream = cdiff.PatchStream(Sequential(items))
        parser = cdiff.DiffParser(stream)
        self.assertEqual(parser._type, 'unified')

    def test_type_detect_context(self):
        patch = """\
*** /path/to/original timestamp
--- /path/to/new timestamp
***************
*** 1,1 ****
--- 1,2 ----
+ This is an important
  This part of the
"""
        items = patch.splitlines(True)
        stream = cdiff.PatchStream(Sequential(items))
        parser = cdiff.DiffParser(stream)
        self.assertEqual(parser._type, 'context')

    def test_type_detect_neg(self):
        patch = """\
spam
--- a
spam
+++ b

"""
        items = patch.splitlines(True)
        stream = cdiff.PatchStream(Sequential(items))
        parser = cdiff.DiffParser(stream)
        self.assertEqual(parser._type, 'unified')

    def test_parse_invalid_hunk_meta(self):
        patch = """\
spam
--- a
+++ b
spam
@@ -a,a +0 @@
"""
        items = patch.splitlines(True)
        stream = cdiff.PatchStream(Sequential(items))
        parser = cdiff.DiffParser(stream)
        self.assertRaises(RuntimeError, list, parser.get_diff_generator())

    def test_parse_dangling_header(self):
        patch = """\
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

        out = list(parser.get_diff_generator())
        self.assertEqual(len(out), 2)
        self.assertEqual(len(out[1]._headers), 1)
        self.assertEqual(out[1]._headers[0], 'spam\n')
        self.assertEqual(out[1]._old_path, '')
        self.assertEqual(out[1]._new_path, '')
        self.assertEqual(len(out[1]._hunks), 0)

    def test_parse_missing_new_path(self):
        patch = """\
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
        self.assertRaises(AssertionError, list, parser.get_diff_generator())

    def test_parse_missing_hunk_meta(self):
        patch = """\
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

        out = list(parser.get_diff_generator())
        self.assertEqual(len(out), 2)
        self.assertEqual(len(out[1]._headers), 0)
        self.assertEqual(out[1]._old_path, '--- c\n')
        self.assertEqual(out[1]._new_path, '+++ d\n')
        self.assertEqual(len(out[1]._hunks), 0)

    def test_parse_missing_hunk_list(self):
        patch = """\
--- a
+++ b
@@ -1,2 +1,2 @@
-foo
+bar
 common
--- c
+++ d
@@ -1,2 +1,2 @@
"""
        items = patch.splitlines(True)
        stream = cdiff.PatchStream(Sequential(items))
        parser = cdiff.DiffParser(stream)
        self.assertRaises(AssertionError, list, parser.get_diff_generator())

    def test_parse_only_in_dir(self):
        patch = """\
--- a
+++ b
@@ -1,2 +1,2 @@
-foo
+bar
 common
Only in foo: foo
--- c
+++ d
@@ -1,2 +1,2 @@
-foo
+bar
 common
"""
        items = patch.splitlines(True)
        stream = cdiff.PatchStream(Sequential(items))
        parser = cdiff.DiffParser(stream)

        out = list(parser.get_diff_generator())
        self.assertEqual(len(out), 3)
        self.assertEqual(len(out[1]._hunks), 0)
        self.assertEqual(out[1]._headers, ['Only in foo: foo\n'])
        self.assertEqual(len(out[2]._hunks), 1)
        self.assertEqual(len(out[2]._hunks[0]._hunk_list), 3)

    def test_parse_only_in_dir_at_last(self):
        patch = """\
--- a
+++ b
@@ -1,2 +1,2 @@
-foo
+bar
 common
Only in foo: foo
"""
        items = patch.splitlines(True)
        stream = cdiff.PatchStream(Sequential(items))
        parser = cdiff.DiffParser(stream)

        out = list(parser.get_diff_generator())
        self.assertEqual(len(out), 2)
        self.assertEqual(len(out[1]._hunks), 0)
        self.assertEqual(out[1]._headers, ['Only in foo: foo\n'])

    def test_parse_binary_differ_diff_ru(self):
        patch = """\
--- a
+++ b
@@ -1,2 +1,2 @@
-foo
+bar
 common
Binary files a/1.pdf and b/1.pdf differ
--- c
+++ d
@@ -1,2 +1,2 @@
-foo
+bar
 common
"""
        items = patch.splitlines(True)
        stream = cdiff.PatchStream(Sequential(items))
        parser = cdiff.DiffParser(stream)

        out = list(parser.get_diff_generator())
        self.assertEqual(len(out), 3)
        self.assertEqual(len(out[1]._hunks), 0)
        self.assertEqual(out[1]._old_path, '')
        self.assertEqual(out[1]._new_path, '')
        self.assertEqual(len(out[1]._headers), 1)
        self.assertTrue(out[1]._headers[0].startswith('Binary files'))
        self.assertEqual(len(out[2]._hunks), 1)
        self.assertEqual(len(out[2]._hunks[0]._hunk_list), 3)

    def test_parse_binary_differ_git(self):
        patch = """\
diff --git a/foo b/foo
index 529d8a3..ad71911 100755
--- a/foo
+++ b/foo
@@ -1,2 +1,2 @@
-foo
+bar
 common
diff --git a/example.pdf b/example.pdf
index 1eacfd8..3696851 100644
Binary files a/example.pdf and b/example.pdf differ
diff --git a/bar b/bar
index 529e8a3..ad71921 100755
--- a/bar
+++ b/bar
@@ -1,2 +1,2 @@
-foo
+bar
 common
"""
        items = patch.splitlines(True)
        stream = cdiff.PatchStream(Sequential(items))
        parser = cdiff.DiffParser(stream)

        out = list(parser.get_diff_generator())
        self.assertEqual(len(out), 3)
        self.assertEqual(len(out[1]._hunks), 0)
        self.assertEqual(out[1]._old_path, '')
        self.assertEqual(out[1]._new_path, '')
        self.assertEqual(len(out[1]._headers), 3)
        self.assertTrue(out[1]._headers[2].startswith('Binary files'))
        self.assertEqual(len(out[2]._hunks), 1)
        self.assertEqual(len(out[2]._hunks[0]._hunk_list), 3)

    def test_parse_svn_prop(self):
        patch = """\
--- a
+++ b
Added: svn:executable
## -0,0 +1 ##
+*
\\ No newline at end of property
Added: svn:keywords
## -0,0 +1 ##
+Id
"""
        items = patch.splitlines(True)
        stream = cdiff.PatchStream(Sequential(items))
        parser = cdiff.DiffParser(stream)
        out = list(parser.get_diff_generator())
        self.assertEqual(len(out), 1)
        self.assertEqual(len(out[0]._hunks), 2)

        hunk = out[0]._hunks[1]
        self.assertEqual(hunk._hunk_headers, ['Added: svn:keywords\n'])
        self.assertEqual(hunk._hunk_list, [('+', 'Id\n')])


class MainTest(unittest.TestCase):

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

    def test_preset_options(self):
        os.environ['CDIFF_OPTIONS'] = '--help'
        self.assertRaises(SystemExit, cdiff.main)
        os.environ.pop('CDIFF_OPTIONS', None)

    def test_read_diff(self):
        sys.argv = sys.argv[:1]
        self._change_file('read_diff')

        os.chdir(self._ws)
        ret = cdiff.main()
        os.chdir(self._cwd)
        self.assertEqual(ret, 0)

    # Following 3 tests does not pass on Travis anymore due to tty problem

    def _test_read_log(self):
        sys.argv = [sys.argv[0], '--log']
        self._change_file('read_log')
        self._commit_file()

        os.chdir(self._ws)
        ret = cdiff.main()
        os.chdir(self._cwd)
        self.assertEqual(ret, 0)

    def _test_read_diff_neg(self):
        sys.argv = sys.argv[:1]
        os.chdir(self._non_ws)
        ret = cdiff.main()
        os.chdir(self._cwd)
        self.assertNotEqual(ret, 0)

    def _test_read_log_neg(self):
        sys.argv = [sys.argv[0], '--log']
        os.chdir(self._non_ws)
        ret = cdiff.main()
        os.chdir(self._cwd)
        self.assertNotEqual(ret, 0)


if __name__ == '__main__':
    unittest.main()

# vim:set et sts=4 sw=4 tw=80:
