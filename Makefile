# Makefile for testing

TESTPYPI := pypitest
PYPI := pypi
SHELL := bash

.PHONY: dogfood lint doc-check doc-preview clean build dist-test dist \
	test cov html reg profile

dogfood:
	./ydiff.py -u
	git diff | ./ydiff.py -s

lint:
	pycodestyle --ignore=E203,W503,W504 *.py */*.py

doc-check:
	./setup.py --long-description | rst2html.py --strict > /dev/null

doc-preview:
	./setup.py --long-description | rst2html.py --strict > output.html
	python3 -m webbrowser -n "file://$(shell pwd)/output.html"
	sleep 1
	rm -f output.html

test: lint doc-check cov reg

cov:
	coverage run tests/test_ydiff.py
	coverage report --show-missing

html:
	coverage html
	python3 -m webbrowser -n "file://$(shell pwd)/htmlcov/index.html"

reg:
	tests/regression.sh

profile:
	tests/profile.sh $(shell for x in {0..99}; do echo tests/*/in.diff; done)

profile-difflib:
	tests/profile.sh tests/large-hunk/tao.diff

clean:
	rm -f MANIFEST profile*.tmp* .coverage
	rm -rf build/ ydiff.egg-info/ dist/ __pycache__/ htmlcov/

build:
	./setup.py build sdist

dist-test: clean build
	twine upload --repository=testpypi dist/*
	rm -f ~/.pypirc

dist: clean build
	twine upload dist/*
	rm -f ~/.pypirc

docker-test:
	docker run -v $(shell pwd):$(shell pwd) -w $(shell pwd) -t --rm \
		python:3-alpine /bin/sh -ec \
		'apk add bash git less make; pip install -r requirements-dev.txt; make test'

docker-shell:
	docker run -v $(shell pwd):$(shell pwd) -w $(shell pwd) -it --rm -P \
		python:3-alpine /bin/sh -xc \
		'apk add bash git less make; pip install -r requirements-dev.txt; exec /bin/sh'

# vim:set noet ts=8 sw=8:
