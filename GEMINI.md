# Fly-in Project Rules

## Language & Tooling
- Python 3.10+, fully Object-Oriented.
- All code must pass `flake8` (max line length 79) and `mypy`.
- Run checks via `.venv/bin/flake8` and `.venv/bin/mypy` (no bare `python` command).
- Use `uv` / the project `.venv` for all dependency management.

## Type Hints
- Mandatory type hints on all parameters, return types, and variables.
- Use `mypy --strict` compatible style.

## Docstrings
- Follow PEP 257, Google style.
- **Keep them short**: one-line summary + terse `Args/Returns/Raises` only where non-obvious.
- Do NOT restate what the code already says. No multi-line prose descriptions.
- Private/internal methods (`_foo`) do not need docstrings.

## Coding Style
- No external graph libraries (`networkx`, `graphlib`, etc.).
- Use context managers (`with open(...)`) for all file/resource access.
- Handle exceptions gracefully — no unhandled crashes.

## Project Structure
- Parser: `src/packages/parsing/`
- Graph: `src/graph/graph.py`
- Algorithm will live in `src/` (Space-Time Dijkstra with Priority Planning).
- Tests: `tests/` using `pytest`.

## Algorithm Context
- This is a mini-MAPF problem: route `nb_drones` from `start_hub` to `end_hub`.
- Algorithm: Space-Time Dijkstra with Priority Planning (PP).
- `BLOCKED` zones: kept in graph for visualisation, excluded from routing edges.
- `RESTRICTED` zones cost 2 turns and require edge reservation for 2 time steps.
- `PRIORITY` zones cost 1 but are preferred via tiebreaker (lower secondary key).
- Reservation table tracks node and edge occupancy per time step.
