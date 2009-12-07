#
# Options
#

# Or you may want to select an explicit Python version, e.g.
PYTHON = python2.5

#
# Interesting targets
#

.PHONY: all
all: bin/buildout
	bin/buildout

.PHONY: check test
check test: bin/test
	bin/test

.PHONY: coverage
coverage:
	bin/test -u --coverage=coverage
	bin/coverage parts/test/coverage

.PHONY: tags
tags:
	bin/ctags

.PHONY: dist
dist: check
	$(PYTHON) setup.py sdist

.PHONY: distcheck
distcheck: check dist
	version=`$(PYTHON) setup.py --version` && \
	rm -rf tmp && \
	mkdir tmp && \
	cd tmp && \
	tar xvzf ../dist/zodbbrowser-$$version.tar.gz && \
	cd zodbbrowser-$$version && \
	make dist && \
	cd .. && \
	mkdir one two && \
	cd one && \
	tar xvzf ../../dist/zodbbrowser-$$version.tar.gz && \
	cd ../two/ && \
	tar xvzf ../zodbbrowser-$$version/dist/zodbbrowser-$$version.tar.gz && \
	cd .. && \
	diff -ur one two -x SOURCES.txt && \
	cd .. && \
	rm -rf tmp && \
	echo "sdist seems to be ok"
# I'm ignoring SOURCES.txt since it appears that the second sdist gets a new
# source file, namely, setup.cfg.  Setuptools/distutils black magic, may it rot
# in hell forever.

release:
	@$(PYTHON) setup.py --version | grep -qv dev || { \
	    echo "Please remove the 'dev' suffix from the version number in src/zodbbrowser/__init__.py"; exit 1; }
	@$(PYTHON) setup.py --long-description | rst2html --exit-status=2 > /dev/null
	@ver_and_date="`$(PYTHON) setup.py --version` (`date +%Y-%m-%d`)" && \
	    grep -q "^$$ver_and_date$$" CHANGES.txt || { \
	        echo "CHANGES.txt has no entry for $$ver_and_date"; exit 1; }
	make distcheck
	test -z "`bzr status`" || { echo; echo "Your working tree is not clean" 1>&2; bzr status; exit 1; }
	# I'm chicken so I won't actually do these things yet
	@echo Please run $(PYTHON) setup.py sdist register upload
	@echo Please run bzr tag `$(PYTHON) setup.py --version`
	@echo Please increment the version number in src/zodbbrowser/__init__.py
	@echo Please add a new empty entry in CHANGES.txt

#
# Implementation
#

bin/buildout:
	$(PYTHON) bootstrap.py

bin/test: bin/buildout
	bin/buildout

