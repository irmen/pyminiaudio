.PHONY: all build test clean docs dist win_wheels linux_wheel upload check_upload
PYTHON?=python3

all:
	@echo "Targets:  build, test, clean, docs, dist, win_wheels, linux_wheel, check_upload, upload"

check_venv:
	@if [ -z "$$VIRTUAL_ENV" ]; then \
		echo "Error: No virtual environment is active."; \
		echo "Please create and activate one first:"; \
		echo "  python3 -m venv venv"; \
		echo "  source venv/bin/activate"; \
		echo "Then run: make $@"; \
		exit 1; \
	fi

build: check_venv
	${PYTHON} -m pip install setuptools cffi
	${PYTHON} -m pip install --editable .

test:
	${PYTHON} -m pytest -v tests

clean:
	rm -rf build/ dist/* *.so *.pyd a.out

docs: check_venv
	${PYTHON} -m pip install setuptools cffi
	@${PYTHON} -c 'import setup; setup.make_md_docs("miniaudio")'

dist:
	rm -rf build/ dist/*
	${PYTHON} -m pip install build
	${PYTHON} -m build --sdist

win_wheels: build
	rm -rf build/ dist/*
	${PYTHON} -m pip install build
	for py in 3.10 3.11 3.12 3.13 3.14; do \
		py -$$py -m build; \
	done

linux_wheel: build
	rm -rf build/ dist/*
	${PYTHON} -m pip install build
	${PYTHON} -m build

upload: check_upload
	twine upload dist/*

check_upload:
	twine check dist/*
