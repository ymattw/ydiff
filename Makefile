# Makefile for testing

TESTPYPI = pypitest
PYPI = pypi

.PHONY: dogfood lint doc-check doc-preview clean build dist-test dist \
	test test3 cov cov3 html reg reg3 profile profile3

dogfood:
	./ydiff.py
	git diff | ./ydiff.py -s

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

test2: lint doc-check cov2 reg2

test3: lint doc-check cov3 reg3

cov:
	coverage run tests/test_ydiff.py
	coverage report --show-missing

cov2:
	python2 `which coverage` run tests/test_ydiff.py
	python2 `which coverage` report --show-missing

cov3:
	python3 `which coverage` run tests/test_ydiff.py
	python3 `which coverage` report --show-missing

html:
	coverage html
	python -m webbrowser -n "file://$(shell pwd)/htmlcov/index.html"

reg:
	tests/regression.sh

reg2:
	PYTHON=python2 tests/regression.sh

reg3:
	PYTHON=python3 tests/regression.sh

profile:
	PYTHON=python3 tests/profile.sh tests/*/in.diff

profile-difflib:
	PYTHON=python3 tests/profile.sh tests/large-hunk/tao.diff

clean:
	rm -f MANIFEST profile*.tmp* .coverage
	rm -rf build/ ydiff.egg-info/ dist/ __pycache__/ htmlcov/

build:
	./setup.py build sdist

dist-test: clean build
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*
	rm -f ~/.pypirc

dist: clean build
	twine upload dist/*
	rm -f ~/.pypirc

docker-test:
	docker run -v $(shell pwd):$(shell pwd) -w $(shell pwd) --rm \
		ymattw/ydiff-dev make test2 test3

docker-image:
	docker build -t ymattw/ydiff-dev .

docker-shell:
	docker run -v $(shell pwd):$(shell pwd) -w $(shell pwd) -it --rm -P \
		ymattw/ydiff-dev /bin/bash

# vim:set noet ts=8 sw=8:
