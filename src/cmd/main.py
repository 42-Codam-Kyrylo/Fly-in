"""Entry point: parse config, run simulation, launch visualiser."""

import argparse
import sys
from packages.utils import print_err
from packages.parsing import ParsingError, ConfigParser
from graph.graph import Graph
from algorithm.simulator import Simulator
from visualization.html_renderer import HtmlRenderer
from visualization.terminal_renderer import TerminalRenderer


def main() -> None:
    """Parse a map file, route all drones, print output, show GUI."""
    parser = argparse.ArgumentParser(description="Fly-in drone routing.")
    parser.add_argument("config_file", help="Path to config file")
    parser.add_argument(
        "-t", "--terminal", action="store_true", help="Show terminal viz"
    )
    parser.add_argument(
        "-web", "--web", action="store_true", help="Show web viz"
    )

    args = parser.parse_args()

    # Default to terminal if neither is specified
    if not args.terminal and not args.web:
        args.terminal = True

    try:
        config = ConfigParser(args.config_file).parse()
        graph = Graph(config)
        result = Simulator(graph).run()

        print(result.render())
        print(f"\nTotal turns: {result.total_turns}")

        if args.terminal:
            TerminalRenderer(graph, result).run()

        if args.web:
            HtmlRenderer(graph, result).run()

    except ParsingError as e:
        print_err(str(e))
        sys.exit(1)
    except RuntimeError as e:
        print_err(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
