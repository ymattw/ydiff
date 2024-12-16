# Makefile for testing

SHELL := bash

.PHONY: dogfood lint doc-check doc-preview clean build dist-test dist \
	test cov html reg profile

dogfood:
	./ydiff.py -u
	git diff | ./ydiff.py -s

lint:
	pycodestyle --ignore=W503,W504 *.py */*.py

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
	./setup.py build sdist bdist_wheel

# Expected to run outside docker with twine installed via pip
dist-test: docker-test-min-python3 docker-test clean build
	~/.local/bin/twine upload --repository=testpypi dist/ydiff-*.tar.gz dist/ydiff-*-any.whl
	rm -f ~/.pypirc

# Expected to run outside docker with twine installed via pip
dist: docker-test-min-python3 docker-test clean build
	~/.local/bin/twine upload dist/ydiff-*.tar.gz dist/ydiff-*.tar.gz dist/ydiff-*-any.whl
	rm -f ~/.pypirc

MIN_PY_VERSION ?= 3.3
docker-test-min-python3:
	docker run -v $(shell pwd):$(shell pwd) -w $(shell pwd) -t --rm \
		python:$(MIN_PY_VERSION)-alpine /bin/sh -ec \
		'apk add -U bash git less make; pip install --trusted-host pypi.python.org -r requirements-dev.txt; make test'

docker-shell-min-python3:
	docker run -v $(shell pwd):$(shell pwd) -w $(shell pwd) -it --rm \
		python:$(MIN_PY_VERSION)-alpine /bin/sh -ec \
		'apk add -U bash git less make; pip install --trusted-host pypi.python.org -r requirements-dev.txt; exec /bin/sh'

docker-test:
	docker run -v $(shell pwd):$(shell pwd) -w $(shell pwd) -t --rm \
		python:3-alpine /bin/sh -ec \
		'apk add bash git less make; pip install -r requirements-dev.txt; make test'

docker-shell:
	docker run -v $(shell pwd):$(shell pwd) -w $(shell pwd) -it --rm -P \
		python:3-alpine /bin/sh -xc \
		'apk add bash git less make; pip install -r requirements-dev.txt; exec /bin/sh'

# vim:set noet ts=8 sw=8:
