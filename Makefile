.PHONY: tests

PY=python3

check:
	$(PY) -m ruff check ./ichier

tests:
	$(PY) -m pytest -v ./tests

clean:
	make uninstall
	find ./ichier ./tests -type d -name __pycache__ -exec rm -rf {} +
	rm -rf build
	rm -rf dist
	rm -rf ichier.egg-info

install:
	$(PY) -m pip install .

uninstall:
	$(PY) -m pip uninstall ichier -y
	
build:
	make clean
	$(PY) setup.py sdist build

upload: dist
	$(PY) -m twine upload dist/*
