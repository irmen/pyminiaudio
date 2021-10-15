.PHONY:  all win_dist dist upload

all:
	@echo "Targets:  clean, test, docs, dist, win_wheels, linux_wheel, check_upload, upload"

clean:
	rm -f dist/* *.so
	python setup.py clean --all

test:
	rm -f *.so
	python setup.py build
	python setup.py test
	python -m pytest -v tests
	# mypy --follow-imports skip miniaudio.py

docs:
	@python -c 'import setup; setup.make_md_docs("miniaudio")'

win_wheels: test
	cmd /C del /q dist\*
	py -3.7-64 setup.py clean --all
	py -3.7-64 setup.py bdist_wheel
	py -3.8-64 setup.py clean --all
	py -3.8-64 setup.py bdist_wheel
	py -3.9-64 setup.py clean --all
	py -3.9-64 setup.py bdist_wheel
	py -3.10-64 setup.py clean --all
	py -3.10-64 setup.py bdist_wheel

linux_wheel: test
	rm -f dist/* *.so
	python setup.py bdist_wheel
	@echo
	@echo
	@echo "REMEMBER: the Linux wheel may be very system/cpu dependent so should you really use this? Beware."
	@echo

dist: test
	rm -f dist/* *.so
	python setup.py clean
	python setup.py sdist

upload: check_upload
	twine upload dist/*

check_upload:
	twine check dist/*
