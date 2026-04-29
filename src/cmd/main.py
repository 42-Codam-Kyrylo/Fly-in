import sys
from packages.utils import print_err
from packages.parsing import ParsingError, ConfigParser


def main() -> None:
    if len(sys.argv) < 2:
        print_err(
            "Missing config.txt. Pass as python script.py config.txt",
        )
        exit(1)

    config_path = sys.argv[1]
    try:
        parser = ConfigParser(config_path)
        config = parser.parse()
        from graph.graph import Graph

        graph = Graph(config)
        print(f"Successfully initialized graph with {len(graph.nodes)} nodes.")
        for node_name, node in graph.nodes.items():
            print(
                (
                    f"Node {node_name} "
                    f"(capacity={node.capacity}, cost={node.cost})"
                )
            )
            for edge in node.neighbors:
                print(
                    (
                        f"  -> {edge.to_zone} "
                        f"(link_capacity={edge.max_link_capacity})"
                    )
                )
    except ParsingError as e:
        print(str(e))
    except Exception as e:
        print(str(e))
    # print(f"config path {config_path}")


if __name__ == "__main__":
    main()
