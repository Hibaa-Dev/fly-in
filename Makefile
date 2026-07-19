PYTHON = python3

PIP = $(PYTHON) -m pip

NAME = fly-in.py

install:
	$(PIP) install -r requirements.txt

run:
	$(PYTHON) $(NAME) mapefile.txt

debug:
	$(PYTHON) -m pgb

clean:
	find . -name "__pycache__" -exec rm -rf {} +
	find . -name ".mypy_cache" -exec rm -rf {} +

lint:
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	flake8 .
	mypy . --strict
