# Makefile for testing

.PHONY: dogfood test git svn

dogfood:
	git diff | src/cdiff.py
	git diff | src/cdiff.py -s
	git diff | src/cdiff.py -s -w 60
	git diff | src/cdiff.py -s -w 90

test: git svn

git svn:
	src/cdiff.py tests/$@.diff
	src/cdiff.py tests/$@.diff -s
	src/cdiff.py tests/$@.diff | diff -u tests/$@.diff -

# vim:set noet ts=8 sw=8:
