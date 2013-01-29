# Makefile for testing

.PHONY: test single-udiff multi-udiff

test: single-udiff multi-udiff

single-udiff:
	src/cdiff.py -t tests/single.udiff
	src/cdiff.py -t tests/single.udiff | diff -u tests/single.udiff -

multi-udiff:
	src/cdiff.py -t tests/multi.udiff
	src/cdiff.py -t tests/multi.udiff | diff -u tests/multi.udiff -

# vim:set noet ts=8 sw=8:
