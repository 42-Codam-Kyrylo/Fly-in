PYTHON ?= python3
UV ?= uv
MAIN ?= src/cmd/main.py
CONFIG ?= maps/custom.txt
# CONFIG ?= maps/intra/medium/02_circular_loop.txt
# CONFIG ?= maps/intra/challenger/01_the_impossible_dream.txt

.PHONY: install run run-web debug clean lint lint-strict test

install:
	$(UV) sync

run:
	PYTHONPATH=src $(UV) run $(PYTHON) ${MAIN} ${CONFIG}

run-web:
	PYTHONPATH=src $(UV) run $(PYTHON) ${MAIN} ${CONFIG} -web

debug:
	PYTHONPATH=src $(UV) run $(PYTHON) -m pdb ${MAIN} ${CONFIG}

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

lint:
	$(UV) run flake8 .
	$(UV) run mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	$(UV) run flake8 .
	$(UV) run mypy . --strict

test:
	PYTHONPATH=src $(UV) run pytest tests/ -v