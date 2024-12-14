.PHONY:  all win_dist dist upload
PYTHON?=python3

all:
	@echo "Targets:  clean, test, docs, dist, win_wheels, linux_wheel, check_upload, upload"

clean:
	rm -f dist/* *.so *.pyd a.out
	${PYTHON} setup.py clean --all

test:
	rm -f *.so *.pyd
	${PYTHON} setup.py clean
	${PYTHON} setup.py build
	${PYTHON} setup.py test
	${PYTHON} -m pytest -v tests
	# mypy --follow-imports skip miniaudio.py

docs:
	@${PYTHON} -c 'import setup; setup.make_md_docs("miniaudio")'

win_wheels: test
	cmd /C del /q dist\*
	py -3.9-64 setup.py clean --all
	py -3.9-64 setup.py bdist_wheel
	py -3.10-64 setup.py clean --all
	py -3.10-64 setup.py bdist_wheel
	py -3.11-64 setup.py clean --all
	py -3.11-64 setup.py bdist_wheel
	py -3.12-64 setup.py clean --all
	py -3.12-64 setup.py bdist_wheel
	py -3.13-64 setup.py clean --all
	py -3.13-64 setup.py bdist_wheel

linux_wheel: test
	rm -f dist/* *.so
	${PYTHON} setup.py bdist_wheel
	@echo
	@echo
	@echo "REMEMBER: the Linux wheel may be very system/cpu dependent so should you really use this? Beware."
	@echo

dist: test
	rm -f dist/* *.so
	${PYTHON} setup.py clean
	${PYTHON} setup.py sdist

upload: check_upload
	twine upload dist/*

check_upload:
	twine check dist/*
