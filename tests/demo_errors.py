# flake8: noqa
# fmt: off

import textwrap
import tempfile
import sys
import os

# Ensure src is in the python path for module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from packages.parsing.parsing import ConfigParser, ParsingError


class Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    CYAN = "\033[36m"
    BLUE = "\033[34m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"


def ctext(text, color):
    return f"{color}{text}{Color.RESET}"


def print_case_header(index, title):
    print(ctext("=" * 72, Color.CYAN))
    print(ctext(f" Test case #{index}: {title}", Color.BOLD + Color.BLUE))
    print(ctext("=" * 72, Color.CYAN))


def print_block_title(title):
    print(ctext(f"\n{title}", Color.BOLD + Color.YELLOW))


def print_error_message(message):
    if message == "(No error raised!)":
        print(ctext(message, Color.GREEN))
    else:
        print(ctext(message, Color.RED))

TEST_CASES = [
    ("nb_drones missing or not first", "start_hub: s 0 0\nend_hub: e 1 1"),
    ("Negative drones", "nb_drones: -5\nstart_hub: s 0 0\nend_hub: e 1 1"),
    ("Invalid drones (non-integer)", "nb_drones: zero\nstart_hub: s 0 0\nend_hub: e 1 1"),
    ("Missing start_hub", "nb_drones: 1\nhub: A 0 0\nend_hub: e 1 1"),
    ("Missing end_hub", "nb_drones: 1\nstart_hub: s 0 0\nhub: A 1 1"),
    ("Multiple start_hub", "nb_drones: 1\nstart_hub: s1 0 0\nstart_hub: s2 1 1\nend_hub: e 2 2"),
    ("Multiple end_hub", "nb_drones: 1\nstart_hub: s 0 0\nend_hub: e1 1 1\nend_hub: e2 2 2"),
    ("Duplicate zone name", "nb_drones: 1\nstart_hub: A 0 0\nend_hub: e 1 1\nhub: A 2 2"),
    ("Connection to unknown zone", "nb_drones: 1\nstart_hub: s 0 0\nend_hub: e 1 1\nconnection: s-A"),
    ("Duplicate connection (same direction)", "nb_drones: 1\nstart_hub: s 0 0\nend_hub: e 1 1\nconnection: s-e\nconnection: s-e"),
    ("Duplicate connection (reversed direction)", "nb_drones: 1\nstart_hub: s 0 0\nend_hub: e 1 1\nconnection: s-e\nconnection: e-s"),
    ("Malformed connection line (no dash)", "nb_drones: 1\nstart_hub: s 0 0\nend_hub: e 1 1\nconnection: s"),
    ("Invalid zone type", "nb_drones: 1\nstart_hub: s 0 0 [zone=unknown_type]\nend_hub: e 1 1"),
    ("Unsupported color", "nb_drones: 1\nstart_hub: s 0 0 [color=unsupported_color]\nend_hub: e 1 1"),
    ("Invalid max_drones (0)", "nb_drones: 1\nstart_hub: s 0 0 [max_drones=0]\nend_hub: e 1 1"),
    ("Invalid max_drones (non-integer)", "nb_drones: 1\nstart_hub: s 0 0 [max_drones=abc]\nend_hub: e 1 1"),
    ("Invalid max_link_capacity (0)", "nb_drones: 1\nstart_hub: s 0 0\nend_hub: e 1 1\nconnection: s-e [max_link_capacity=0]"),
    ("Invalid max_link_capacity (non-integer)", "nb_drones: 1\nstart_hub: s 0 0\nend_hub: e 1 1\nconnection: s-e [max_link_capacity=xyz]"),
    ("Malformed metadata format (no equals)", "nb_drones: 1\nstart_hub: s 0 0 [invalid_metadata]\nend_hub: e 1 1"),
    ("Invalid zone name (contains dash)", "nb_drones: 1\nstart_hub: name-with-dash 0 0\nend_hub: e 1 1"),
    ("Invalid zone name (contains space)", "nb_drones: 1\nstart_hub: name with space 0 0\nend_hub: e 1 1"),
    ("General syntax error", "nb_drones: 1\nstart_hub: s 0 0\nend_hub: e 1 1\nthis is not valid"),
    ("Invalid coordinate (floating point)", "nb_drones: 1\nstart_hub: s 0 0\nend_hub: e 1.5 1"),
]

def run_demo():
    for i, (name, content) in enumerate(TEST_CASES, start=1):
        content = textwrap.dedent(content).strip()
        print_case_header(i, name)
        print_block_title("Input file body:")
        print(content)
        
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            temp_path = f.name
            
        try:
            parser = ConfigParser(temp_path)
            parser.parse()
            print_block_title("Result:")
            print_error_message("(No error raised!)")
        except ParsingError as e:
            print_block_title("Result:")
            print_error_message(str(e))
        except Exception as e:
            print_block_title("Result:")
            print_error_message(f"Unexpected error: {e}")
        finally:
            os.remove(temp_path)
        
        # Add a newline between cases for readability in the demo script output
        print()

    # Special case for Missing file
    print_case_header(len(TEST_CASES) + 1, "Missing file")
    print_block_title("Input file body:")
    print("(No file content - file does not exist)")
    try:
        ConfigParser("non_existent.txt").parse()
    except ParsingError as e:
        print_block_title("Result:")
        print_error_message(str(e))
    print()

if __name__ == "__main__":
    run_demo()
