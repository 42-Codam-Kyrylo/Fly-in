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
- **Libraries:** NO libraries for graph logic are allowed (e.g., `networkx`, `graphlib`).
- **Error Handling:** Must handle exceptions gracefully; unhandled crashes during review lead to failure.

## III. Common Instructions
- **Makefile:** Must include:
    - `install`: Install dependencies.
    - `run`: Execute the main script.
    - `debug`: Run in debug mode (pdb).
    - `clean`: Remove caches (`__pycache__`, `.mypy_cache`).
    - `lint`: Run `flake8` and specific `mypy` flags.
- **Git:** Include a `.gitignore` to exclude Python artifacts.

## IV. Map & Parser Requirements
### Input Format
- First line: `nb_drones: <positive_integer>`
- Zone definitions:
    - `start_hub: <name> <x> <y> [metadata]`
    - `end_hub: <name> <x> <y> [metadata]`
    - `hub: <name> <x> <y> [metadata]`
- Connections: `connection: <zone1>-<zone2> [metadata]`

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

## V. Simulation Mechanics
### Movement Rules
- **Turns:** Simulation proceeds in discrete turns.
- **Simultaneity:** Multiple drones can move at once if capacities allow.
- **Capacity:**
    - Drones moving *out* free up space for drones moving *in* during the same turn.
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
- **Easy Maps:** ≤ 8 turns.
- **Medium Maps:** 12–20 turns.
- **Hard Maps:** ≤ 60 turns (Ultimate challenge target: 35).
- **Challenger Map:** Reference record is 45 turns (optional).

## VIII. README Requirements
- First line: *This project has been created as part of the 42 curriculum by <login>.*
- Sections: Description, Instructions (install/run), Resources (including AI usage details), Algorithm Strategy, and Visual Representation documentation.
