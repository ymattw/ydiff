# Makefile for testing

TESTS = git svn crlf

.PHONY: dogfood test $(TESTS)

dogfood:
	git diff | src/cdiff.py
	git diff | src/cdiff.py -s
	git diff | src/cdiff.py -s -w 60
	git diff | src/cdiff.py -s -w 90

test: $(TESTS)

$(TESTS):
	src/cdiff.py tests/$@.diff
	src/cdiff.py tests/$@.diff -s
	src/cdiff.py tests/$@.diff | diff -u tests/$@.diff -

# vim:set noet ts=8 sw=8:
