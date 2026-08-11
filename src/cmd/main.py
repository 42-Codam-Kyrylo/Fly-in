"""Entry point: parse config, run simulation, launch visualiser."""

import sys
from packages.utils import print_err
from packages.parsing import ParsingError, ConfigParser
from graph.graph import Graph
from algorithm.simulator import Simulator
from visualization.renderer import Renderer


def main() -> None:
    """Parse a map file, route all drones, print output, show GUI."""
    if len(sys.argv) < 2:
        print_err("Usage: script.py <config_file>")
        sys.exit(1)

    try:
        config = ConfigParser(sys.argv[1]).parse()
        graph = Graph(config)
        result = Simulator(graph).run()

        print(result.render())
        print(f"\nTotal turns: {result.total_turns}")

        Renderer(graph, result).run()

    except ParsingError as e:
        print_err(str(e))
        sys.exit(1)
    except RuntimeError as e:
        print_err(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
