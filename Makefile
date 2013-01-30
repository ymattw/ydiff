# Makefile for testing

.PHONY: test single-udiff multi-udiff

test: single-udiff multi-udiff

single-udiff:
	src/cdiff.py tests/single.udiff
	src/cdiff.py tests/single.udiff | diff -u tests/single.udiff -

multi-udiff:
	src/cdiff.py tests/multi.udiff
	src/cdiff.py tests/multi.udiff | diff -u tests/multi.udiff -

# vim:set noet ts=8 sw=8:
