# Makefile for testing

TESTPYPI = pypitest
PYPI = pypi

.PHONY: dogfood lint doc-check doc-preview clean build dist-test dist \
	test cov html reg profile

dogfood:
	./ydiff.py
	git diff | ./ydiff.py -s

lint:
	pep8 --ignore=E203 *.py tests/*.py

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
	tests/profile.sh tests/*/in.diff

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
	docker run -v $(shell pwd):$(shell pwd) -w $(shell pwd) --rm \
		ymattw/ydiff-dev make test

docker-image:
	docker build -t ymattw/ydiff-dev .

docker-push-image:
	docker push ymattw/ydiff-dev .

docker-shell:
	docker run -v $(shell pwd):$(shell pwd) -w $(shell pwd) -it --rm -P \
		ymattw/ydiff-dev /bin/bash

# vim:set noet ts=8 sw=8:
