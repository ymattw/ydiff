# Makefile for testing

TESTPYPI = http://testpypi.python.org/pypi

.PHONY: dogfood test clean build dist-test dist

dogfood:
	./cdiff.py -s
	git diff | ./cdiff.py
	git diff | ./cdiff.py -s

test:
	tests/regression.sh

clean:
	rm -f MANIFEST
	rm -rf build/ cdiff.egg-info/ dist/ __pycache__/

build:
	./setup.py build sdist

dist-test:
	./setup.py build sdist upload -r $(TESTPYPI)

dist:
	./setup.py build sdist upload

# vim:set noet ts=8 sw=8:
