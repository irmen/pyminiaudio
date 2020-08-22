.PHONY:  all win_dist dist upload

all:
	@echo "Targets:  test, docs, dist, win_wheels, linux_wheel, check_upload, upload"

test:
	rm -f *.so
	python setup.py build test
	python -m pytest tests

docs:
	@python -c 'import setup; setup.make_md_docs("miniaudio")'

win_wheels: test
	cmd /C del /q dist\*
	py -3.7-32 setup.py clean --all
	py -3.7-32 setup.py bdist_wheel
	py -3.7-64 setup.py clean --all
	py -3.7-64 setup.py bdist_wheel
	py -3.8-32 setup.py clean --all
	py -3.8-32 setup.py bdist_wheel
	py -3.8-64 setup.py clean --all
	py -3.8-64 setup.py bdist_wheel

linux_wheel: dist
	python setup.py bdist_wheel

dist: test
	rm -f dist/* *.so
	python setup.py clean
	python setup.py sdist

upload: check_upload
	twine upload dist/*

check_upload:
	twine check dist/*
