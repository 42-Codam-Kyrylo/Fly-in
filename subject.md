# Fly-in: Project Requirements

## I. Overview

Design an efficient drone routing system to navigate a fleet of drones from a `start_hub` to an `end_hub` while minimizing simulation turns and respecting strict constraints.

## II. Technical Constraints

- **Language:** Python 3.10 or later.
- **Paradigm:** Must be completely **Object-Oriented**.
- **Coding Standards:**
    - Adhere to `flake8` standards.
    - Mandatory type hints for all parameters, return types, and variables.
    - Must pass `mypy` (strict checking recommended).
    - Docstrings must follow PEP 257 (Google or NumPy style).
- **Resource Management:** Must use context managers (e.g., `with open(...)`) for resources like files to ensure automatic cleanup and prevent leaks.
- **Libraries:** NO libraries for graph logic are allowed (e.g., `networkx`, `graphlib`).
- **Error Handling:** Must handle exceptions gracefully; unhandled crashes during review lead to failure.
- **Testing & Environment (Recommended):** Use virtual environments (`venv` or `conda`) and write unit tests using `pytest` or `unittest` to cover edge cases.

## III. Common Instructions

- **Makefile:** Must include:
    - `install`: Install dependencies.
    - `run`: Execute the main script.
    - `debug`: Run in debug mode (pdb).
    - `clean`: Remove caches (`__pycache__`, `.mypy_cache`).
    - `lint`: Run `flake8` and specific `mypy` flags.
    - `lint-strict` (optional): Run `flake8` and `mypy --strict`.
- **Git:** Include a `.gitignore` to exclude Python artifacts.

## IV. Map & Parser Requirements

### Input Format

- First line: `nb_drones: <positive_integer>`
- Zone definitions:
    - `start_hub: <name> <x> <y> [metadata]`
    - `end_hub: <name> <x> <y> [metadata]`
    - `hub: <name> <x> <y> [metadata]`
- Connections: `connection: <zone1>-<zone2> [metadata]`
- **Comments:** Lines or parts of lines starting with `#` are comments and must be ignored.

### Metadata & Types

- **Zones:**
    - `zone=<type>` (default: `normal`)
        - `normal`: 1 turn movement cost.
        - `blocked`: Inaccessible.
        - `restricted`: 2 turns movement cost.
        - `priority`: 1 turn cost, but preferred in pathfinding.
    - `color=<value>`: Optional for visual output.
    - `max_drones=<N>`: Max occupancy (default: 1).
- **Connections:**
    - `max_link_capacity=<N>`: Max drones traversing simultaneously (default: 1).

### Parsing Rules

- Unique names and valid integer coordinates.
- Zone names cannot contain dashes or spaces.
- No duplicate connections (e.g., `a-b` and `b-a` are duplicates).
- Invalid types or negative capacities must raise a clear error with line and cause.
- **Exception for Start/End Hubs:** `max_drones` limits on `start_hub` and `end_hub` must be ignored (not a validation error) as they have infinite capacity.

## V. Simulation Mechanics

### Movement Rules

- **Turns:** Simulation proceeds in discrete turns.
- **Simultaneity:** Multiple drones can move at once if capacities allow.
- **Capacity:**
    - Drones moving _out_ free up space for drones moving _in_ during the same turn.
    - `start_hub` and `end_hub` have infinite capacity.
- **Restricted Zones:**
    - Cost 2 turns.
    - Turn 1: Drone enters the connection (occupies link capacity).
    - Turn 2: Drone arrives at the destination.
    - Drones **cannot** wait on the connection; they must arrive after turn 2.

### Output Format

- Each line represents one simulation turn.
- Movement format: `D<ID>-<zone>` or `D<ID>-<connection>` (for restricted zones).
- Only drones that move are listed.
- Simulation ends when all drones reach the `end_hub`.

## VI. Mandatory Features

- **Pathfinding:**
    - Distribute drones across multiple paths.
    - Strategic waiting and deadlock avoidance.
    - Account for path lengths and weighted costs.
- **Visual Representation:** Mandatory visual feedback via colored terminal output or a GUI.
- **Scoring:** Evaluated primarily on total simulation turns.

## VII. Performance Benchmarks

- **Easy Maps:** < 10 turns.
- **Medium Maps:** 10–30 turns.
- **Hard Maps:** < 60 turns.

## VIII. Bonus Part

- **Perfect Performance:** Match or beat the reference target turn count for all provided maps.
- **Challenger Map:** Solve "The Impossible Dream" (25 drones) and beat the reference record of 45 turns.

## IX. README Requirements

- First line: _This project has been created as part of the 42 curriculum by <login>._
- Sections: Description, Instructions (install/run), Resources (including AI usage details), Algorithm Strategy, and Visual Representation documentation.

## X. Peer-Review Preparation

- Be prepared to explain your algorithm's computational complexity (Big O), memory usage, and architectural choices.
- Be ready for live coding tasks: a brief modification of the project (e.g., minor behavior change, updating a function, adjusting a data structure) within a few minutes.
