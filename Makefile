# Makefile for testing

TESTS = git svn crlf strange
TESTPYPI = http://testpypi.python.org/pypi

.PHONY: dogfood test $(TESTS) clean dist

dogfood:
	src/cdiff.py -s
	git diff | src/cdiff.py
	git diff | src/cdiff.py -s

test: $(TESTS)

$(TESTS):
	src/cdiff.py tests/$@.diff
	src/cdiff.py tests/$@.diff -s
	src/cdiff.py tests/$@.diff | diff -u tests/$@.diff -
	python3 src/cdiff.py tests/$@.diff
	python3 src/cdiff.py tests/$@.diff -s
	python3 src/cdiff.py tests/$@.diff | diff -u tests/$@.diff -

clean:
	rm -rf MANIFEST build/ cdiff.egg-info/ dist/

dist-test:
	./setup.py build sdist upload -r $(TESTPYPI)

install-test:
	pip install -r $(TESTPYPI)

dist:
	./setup.py build sdist upload

# vim:set noet ts=8 sw=8:
