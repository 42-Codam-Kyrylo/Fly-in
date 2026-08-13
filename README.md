*This project has been created as part of the 42 curriculum by kvolynsk.*

# Fly-in — Multi-Agent Drone Routing System

## Description

**Fly-in** is a Multi-Agent Pathfinding (MAPF) project that simulates the routing
of a fleet of drones across a weighted, zone-typed graph. The goal is to move
`nb_drones` drones from a `start_hub` to an `end_hub` in the **minimum number of
simulation turns**, while respecting capacity constraints, zone types, and avoiding
collisions or deadlocks.

### Zone Types

| Type         | Movement Cost | Notes                                                  |
|--------------|:-------------:|--------------------------------------------------------|
| `normal`     | 1 turn        | Standard traversal                                     |
| `priority`   | 1 turn        | Preferred by pathfinder via secondary tiebreaker       |
| `restricted` | 2 turns       | Drone enters edge on turn 1, arrives at node on turn 2 |
| `blocked`    | —             | Kept in graph for visualisation; excluded from routing |

### Key Constraints

- Drone movement is **simultaneous** — drones moving out free capacity for drones
  moving in during the same turn.
- `start_hub` and `end_hub` have **infinite capacity**.
- Connections have a configurable `max_link_capacity` (default: 1).
- Node zones have a configurable `max_drones` occupancy limit (default: 1).

---

## Algorithm: Space-Time Dijkstra + Priority Planning

The routing strategy is a two-level approach.

### 1. Priority Planning (PP)

Drones are planned **sequentially** in priority order (D1 first). Each drone plans
its route around all previously committed paths. This converts the MAPF problem into
a series of single-agent searches.

**Implementation:** [`src/algorithm/simulator.py`](src/algorithm/simulator.py)

### 2. Space-Time Dijkstra

Each individual drone is routed using a modified Dijkstra's algorithm operating in
**space-time**: graph states are `(time_step, node_name)` pairs rather than just
nodes. This naturally handles waiting and congestion.

**Key design decisions:**

- **Heap entry**: `(time, penalty, node, previous_state)` — time is the primary
  key; `penalty` is the secondary key (non-priority hops accumulated) so that
  `priority` zones are preferred when two paths have equal time cost.
- **Wait-in-place**: At each state, a drone may wait one turn at its current node
  (if capacity allows), generating a new state `(t+1, same_node)`.
- **Edge reservation**: For restricted zones (2-turn transit), the edge is reserved
  for both transit turns to prevent collisions mid-edge.
- **Hard time cap**: `max_time = (|nodes| + nb_drones) x 4` prevents unbounded
  search while being generous enough for complex maps.

**Implementation:** [`src/algorithm/pathfinder.py`](src/algorithm/pathfinder.py)

### 3. Reservation Table

A `ReservationTable` stores per-turn occupancy for both **nodes** and **edges**.
After each drone's path is found, all its node/edge reservations are committed, and
the next drone routes around them.

**Implementation:** [`src/algorithm/reservation.py`](src/algorithm/reservation.py)

### Complexity

| Aspect          | Bound                                                                        |
|-----------------|------------------------------------------------------------------------------|
| Space per drone | O(T x |V|) where T = max_time, |V| = number of nodes                       |
| Time per drone  | O(T x |V| x log(T x |V|)) — Dijkstra on the space-time graph               |
| Total (PP)      | O(nb_drones x T x |V| x log(T x |V|))                                      |

---

## Visual Representation

Two visualisation modes are provided, both launched automatically after the
simulation completes.

### Terminal Renderer (default)

Activated when the `-web` flag is **not** passed. Renders each turn as a compact
ASCII snapshot of the graph, showing:

- Which drones are present at each node, with **ANSI colour** inherited from the
  map's `color=<value>` metadata (18 named colours supported).
- Only nodes with drones, or the start/end hubs, are printed — reducing noise.
- Zone type (`NORMAL`, `RESTRICTED`, `PRIORITY`, `BLOCKED`) is shown next to each
  node name.

This renderer is ideal for quick runs and CI pipelines.

**Implementation:** [`src/visualization/terminal_renderer.py`](src/visualization/terminal_renderer.py)

### HTML / Web Renderer (`-web` flag)

Activated by passing `-web` on the command line (`make run-web`). Generates a
**self-contained HTML file** (inline CSS + JS, no external dependencies) and opens
it in the default browser. Features include:

- **Interactive graph canvas** — nodes are drawn at their declared `(x, y)`
  coordinates, edges shown with capacity labels.
- **Animated playback** — a step-through control lets the user advance or rewind
  turns to observe drone positions at each time step.
- **Zone-type colour coding** — blocked zones, restricted zones, hubs, and normal
  nodes are visually distinct.
- **Drone position tracking** — each drone is represented with its ID, smoothly
  repositioned on the canvas as turns advance.

The HTML file is written to a system temp directory and opened via `webbrowser`,
requiring no server.

**Implementation:** [`src/visualization/html_renderer.py`](src/visualization/html_renderer.py)

---

## Instructions

### Prerequisites

- Python 3.10+
- [`uv`](https://github.com/astral-sh/uv) package manager

### Installation

```bash
make install
```

This runs `uv sync` to install all dependencies into the project `.venv`.

### Running

```bash
# Terminal visualisation (default map: maps/custom.txt)
make run

# Web visualisation (opens browser)
make run-web

# Custom map
PYTHONPATH=src uv run python3 src/cmd/main.py maps/intra/medium/02_circular_loop.txt
PYTHONPATH=src uv run python3 src/cmd/main.py maps/intra/challenger/01_the_impossible_dream.txt -web
```

### Makefile Targets

| Target             | Description                                          |
|--------------------|------------------------------------------------------|
| `make install`     | Install dependencies via `uv sync`                   |
| `make run`         | Run with terminal visualisation                      |
| `make run-web`     | Run with HTML/browser visualisation                  |
| `make debug`       | Run under `pdb` debugger                             |
| `make lint`        | Run `flake8` + `mypy` (warn mode)                    |
| `make lint-strict` | Run `flake8` + `mypy --strict`                       |
| `make test`        | Run `pytest` test suite                              |
| `make clean`       | Remove `__pycache__`, `.mypy_cache`, `.pytest_cache` |

### Map File Format

```
nb_drones: <N>
start_hub: <name> <x> <y> [zone=<type>] [color=<value>] [max_drones=<N>]
end_hub:   <name> <x> <y> [zone=<type>] [color=<value>]
hub:       <name> <x> <y> [zone=<type>] [color=<value>] [max_drones=<N>]
connection: <zone1>-<zone2> [max_link_capacity=<N>]
# Lines starting with # are comments
```

---

## Project Structure

```
fly-in-1/
├── src/
│   ├── algorithm/
│   │   ├── pathfinder.py         # Space-Time Dijkstra (single drone)
│   │   ├── reservation.py        # Node & edge reservation table
│   │   └── simulator.py          # Priority Planning (all drones)
│   ├── graph/
│   │   └── graph.py              # Graph data structure (no external libs)
│   ├── packages/
│   │   ├── parsing/              # Map file parser
│   │   └── utils/                # Shared utilities
│   ├── visualization/
│   │   ├── terminal_renderer.py  # ANSI coloured terminal output
│   │   ├── html_renderer.py      # Self-contained HTML visualiser
│   │   ├── template.html
│   │   ├── style.css
│   │   └── script.js
│   └── cmd/
│       └── main.py               # Entry point
├── maps/                         # Provided and custom map files
├── tests/                        # pytest test suite
├── Makefile
├── pyproject.toml
└── mypy.ini
```

---

## Resources

### Algorithm & Data Structures

- [Understanding Adjacency List in DSA](https://zartaj5683.medium.com/understanding-adjacency-list-in-data-structure-and-algorithms-00ecb5d2d415)
- [Breadth-First Search — GeeksForGeeks](https://www.geeksforgeeks.org/dsa/breadth-first-search-or-bfs-for-a-graph/)
- [BFS — prajun_t on Medium](https://medium.com/@prajun_t/breadth-first-search-bfs-db7ffb384da7)
- [Dijkstra's Shortest Path — GeeksForGeeks](https://www.geeksforgeeks.org/dsa/dijkstras-shortest-path-algorithm-greedy-algo-7/)
- [Dijkstra's Algorithm — W3Schools](https://www.w3schools.com/dsa/dsa_algo_graphs_dijkstra.php)
- [Multi-Agent Pathfinding — Wikipedia](https://en.wikipedia.org/wiki/Multi-agent_pathfinding)

### AI Usage

AI assistance (Google Gemini / Antigravity) was used during this project for the
following tasks:

- **Edge-case reasoning** — clarifying the semantics of restricted-zone transit
  (edge reservations spanning two time steps) and capacity release rules.
- **Code review & refactoring** — suggesting improvements to type annotations,
  docstring style, and `flake8`/`mypy` compliance.
- **README writing** — structuring and drafting this document.

All algorithm logic, architectural choices, and implementation were authored and
validated by the project student.
