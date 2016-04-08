# Makefile for testing

TESTPYPI = pypitest
PYPI = pypi

.PHONY: dogfood lint doc-check doc-preview clean build dist-test dist \
	test test3 cov cov3 html reg reg3 profile profile3

dogfood:
	./cdiff.py
	git diff | ./cdiff.py -s

lint:
	pep8 --ignore=E203 *.py tests/*.py

doc-check:
	./setup.py --long-description | rst2html.py --strict > /dev/null

doc-preview:
	./setup.py --long-description | rst2html.py --strict > output.html
	python -m webbrowser -n "file://$(shell pwd)/output.html"
	sleep 1
	rm -f output.html

test: lint doc-check cov reg

test3: lint doc-check cov3 reg3

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
	rm -rf build/ cdiff.egg-info/ dist/ __pycache__/ htmlcov/

build:
	./setup.py build sdist

dist-test:
	./setup.py build sdist register upload -r $(TESTPYPI)
	rm -f ~/.pypirc

dist:
	./setup.py build sdist register upload -r $(PYPI)
	rm -f ~/.pypirc

# vim:set noet ts=8 sw=8:
