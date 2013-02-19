# Makefile for testing

TESTPYPI = https://testpypi.python.org/pypi
PYPI = https://pypi.python.org/pypi
LONG_PATCH_CMD = for i in {1..100}; do cat tests/svn/in.diff; done
PROFILE_ARGS = -m cProfile -s time cdiff.py -c always -s -w 60

.PHONY: dogfood test test3 profile profile3 clean build dist-test dist

dogfood:
	./cdiff.py
	git diff | ./cdiff.py -s

test:
	tests/regression.sh

test3:
	PYTHON=python3 tests/regression.sh

profile:
	tests/profile.sh profile.tmp

profile3:
	tests/profile.sh profile3.tmp

clean:
	rm -f MANIFEST profile*.tmp*
	rm -rf build/ cdiff.egg-info/ dist/ __pycache__/

build:
	./setup.py build sdist

dist-test:
	./setup.py build sdist register upload -r $(TESTPYPI)

dist:
	./setup.py build sdist register upload -r $(PYPI)

# vim:set noet ts=8 sw=8:
