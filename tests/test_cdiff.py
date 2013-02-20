#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Unit test for cdiff"""

import sys
if sys.hexversion < 0x02050000:
    raise SystemExit("*** Requires python >= 2.5.0")

import unittest

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
        self.assertEqual(
                stream.read_stream_header(1),
                [])

        items = ['hello', 'world', 'again']

        stream = cdiff.PatchStream(Sequential(items))
        self.assertEqual(stream.read_stream_header(2), items[:2])

        stream = cdiff.PatchStream(Sequential(items))
        self.assertEqual(stream.read_stream_header(4), items[:])

    def test_iter_after_read_stream_header(self):
        items = ['hello', 'world', 'again', 'and', 'again']
        stream = cdiff.PatchStream(Sequential(items))

        out = []
        _ = stream.read_stream_header(2)
        for item in stream:
            out.append(item)
        self.assertEqual(out, items)


class TestHunk(unittest.TestCase):

    def test_mdiff(self):
        pass

    def test_get_old_text(self):
        pass

    def test_get_new_text(self):
        pass


class TestDiff(unittest.TestCase):

    def test_markup_mix(self):
        pass

    def test_markup_traditional(self):
        pass

    def test_markup_side_by_side(self):
        pass


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
        items = ['spam\n', '--- README\n', '+++ README\n', '@@ -3,7 +3,6 @@\n']
        stream = cdiff.PatchStream(Sequential(items))
        parser = cdiff.DiffParser(stream)
        self.assertEqual(parser._type, 'udiff')

    def test_type_detect_neg(self):
        items = ['spam\n', '--- README\n', '+++ README\n', 'spam\n']
        stream = cdiff.PatchStream(Sequential(items))
        try:
            parser = cdiff.DiffParser(stream)
        except:
            e = sys.exc_info()[1]
            self.assertTrue(isinstance(e, RuntimeError))

    def test_parser(self):
        pass


if __name__ == '__main__':
    unittest.main()

# vim:set et sts=4 sw=4 tw=80:
