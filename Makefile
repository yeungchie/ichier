.PHONY: check tests clean install uninstall build upload iv pverilog pspice

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
	$(PY) setup.py build sdist bdist_wheel

upload: dist
	$(PY) -m twine upload dist/*

iv:
	iverilog -o test.vvp.tmp ./tmp/netlist/test.v
	rm -f test.vvp.tmp

pverilog:
	python -m ichier parse verilog ./tmp/netlist/top.v

pspice:
	python -m ichier parse spice ./tmp/netlist/top.cdl
