.PHONY: test check
PYTHON ?= python3

test:
	$(PYTHON) -m unittest discover -s tests -v

check: test
	git diff --check
	spectra validate --all --strict
