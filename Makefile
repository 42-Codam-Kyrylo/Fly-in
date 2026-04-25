PYTHON ?= python3
UV ?= uv
MAIN ?= src/cmd/main.py

.PHONY: install run debug clean lint lint-strict

install:
	$(UV) sync

run:
	$(UV) run $(PYTHON) ${MAIN}

debug:
	$(UV) run $(PYTHON) -m pdb main.py

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