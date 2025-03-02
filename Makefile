.PHONY: check tests clean install uninstall build upload iv pack

PY=python3

check:
	$(PY) -m ruff check ./ichier

tests:
	$(PY) -m pytest

clean:
	make uninstall
	find ./ichier ./tests -type d -name __pycache__ -exec rm -rf {} +
	rm -rf build
	rm -rf dist
	rm -rf ichier.egg-info
	rm -rf packed

install:
	$(PY) -m pip install .

uninstall:
	$(PY) -m pip uninstall ichier -y
	
build:
	make clean
	$(PY) setup.py build bdist_wheel

upload: dist
	$(PY) -m twine upload dist/*

iv:
	iverilog -o test.vvp.tmp ./tmp/netlist/test.v
	rm -f test.vvp.tmp

pack:
	$(PY) -m nuitka ./tmp/ichier.py --standalone --onefile --output-dir=packed --remove-output
