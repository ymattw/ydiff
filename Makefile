# Makefile for testing

TESTS = git svn crlf strange
TESTPYPI = http://testpypi.python.org/pypi

.PHONY: dogfood test $(TESTS) clean dist-test dist

dogfood:
	./cdiff.py -s
	git diff | ./cdiff.py
	git diff | ./cdiff.py -s

test: $(TESTS)

$(TESTS):
	./cdiff.py tests/$@.diff
	./cdiff.py tests/$@.diff -s
	./cdiff.py tests/$@.diff | diff -u tests/$@.diff -
	python3 ./cdiff.py tests/$@.diff
	python3 ./cdiff.py tests/$@.diff -s
	python3 ./cdiff.py tests/$@.diff | diff -u tests/$@.diff -

clean:
	rm -f cdiff MANIFEST
	rm -rf build/ cdiff.egg-info/ dist/

dist-test:
	./setup.py build sdist upload -r $(TESTPYPI)

dist:
	./setup.py build sdist upload

# vim:set noet ts=8 sw=8:
