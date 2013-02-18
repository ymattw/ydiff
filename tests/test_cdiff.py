#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Unit test for cdiff"""

import sys
if sys.hexversion < 0x02050000:
    raise SystemExit("*** Requires python >= 2.5.0")

sys.path.insert(0, '..')

import unittest
import cdiff

class TestCdiff(unittest.TestCase):

    def test_foo(self):
        self.assertTrue(1)

if __name__ == '__main__':
    unittest.main()

# vim:set et sts=4 sw=4 tw=80:
