# Makefile for testing

TESTPYPI = https://testpypi.python.org/pypi
PYPI = https://pypi.python.org/pypi

.PHONY: dogfood clean build dist-test dist \
	test test3 cov cov3 html reg reg3 profile profile3

dogfood:
	./cdiff.py
	git diff | ./cdiff.py -s

test: cov reg

test3: cov3 reg3

cov:
	coverage run tests/test_cdiff.py
	coverage report --show-missing

cov3:
	python3 `which coverage` run tests/test_cdiff.py
	python3 `which coverage` report --show-missing

html:
	coverage html
	python -m webbrowser -n "file://$(shell pwd)/htmlcov/index.html"

reg:
	tests/regression.sh

reg3:
	PYTHON=python3 tests/regression.sh

profile:
	tests/profile.sh profile.tmp

profile3:
	tests/profile.sh profile3.tmp

clean:
	rm -f MANIFEST profile*.tmp* .coverage
	rm -rf build/ cdiff.egg-info/ dist/ __pycache__/

build:
	./setup.py build sdist

dist-test:
	./setup.py build sdist register upload -r $(TESTPYPI)

dist:
	./setup.py build sdist register upload -r $(PYPI)

# vim:set noet ts=8 sw=8:
