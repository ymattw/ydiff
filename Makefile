# Makefile for testing

TESTPYPI = https://testpypi.python.org/pypi
PYPI = https://pypi.python.org/pypi

.PHONY: dogfood clean build dist-test dist \
	test test3 unit unit3 reg reg3 profile profile3

dogfood:
	./cdiff.py
	git diff | ./cdiff.py -s

test: unit reg

test3: unit3 reg3

unit:
	tests/test_cdiff.py

unit3:
	python3 tests/test_cdiff.py

reg:
	tests/regression.sh

reg3:
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
