# flake8: noqa
# fmt: off

import pytest
import textwrap
import sys
import os

# Ensure src is in the python path for module imports
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from packages.parsing.parsing import ConfigParser, ParsingError
from packages.parsing.config_models import ZoneType, Colors


def create_temp_file(tmp_path, content: str):
    file_path = tmp_path / "test_map.txt"
    file_path.write_text(textwrap.dedent(content).strip())
    return str(file_path)


# --- Happy Path Tests ---


def test_valid_basic_map(tmp_path):
    """Verifies that a simple valid map is parsed correctly."""
    content = """
    nb_drones: 3
    start_hub: start_node 0 0 [color=green]
    end_hub: end_node 10 10 [color=red]
    connection: start_node-end_node
    """
    file_path = create_temp_file(tmp_path, content)
    parser = ConfigParser(file_path)
    config = parser.parse()

    assert config.nb_drones == 3
    assert config.start_hub.name == "start_node"
    assert config.end_hub.name == "end_node"
    assert len(config.hubs) == 0
    assert len(config.connections) == 1
    assert config.connections[0].connection == "start_node-end_node"


def test_valid_complex_map(tmp_path):
    """Verifies a complex map with various metadata, types, and negative coordinates."""
    content = """
    # This is a comment
    nb_drones: 10
    
    start_hub: s 0 0 [color=blue max_drones=5 zone=normal]
    hub: A -1 -2 [zone=priority color=gold max_drones=2]
    hub: B 5 5 [zone=blocked]
    end_hub: e 10 0 [zone=restricted max_drones=1 color=red]
    
    connection: s-A [max_link_capacity=2]
    connection: A-B
    connection: B-e [max_link_capacity=10]
    """
    file_path = create_temp_file(tmp_path, content)
    parser = ConfigParser(file_path)
    config = parser.parse()

    assert config.nb_drones == 10
    assert config.start_hub.metadata.color == Colors.BLUE
    assert config.start_hub.metadata.max_drones == 5
    assert config.start_hub.metadata.zone_type == ZoneType.NORMAL

    assert "A" in config.hubs
    assert config.hubs["A"].x == -1
    assert config.hubs["A"].y == -2
    assert config.hubs["A"].metadata.zone_type == ZoneType.PRIORITY
    assert config.hubs["A"].metadata.max_drones == 2

    assert config.hubs["B"].metadata.zone_type == ZoneType.BLOCKED

    assert config.connections[0].max_link_capacity == 2
    assert config.connections[1].max_link_capacity == 1


# --- nb_drones Constraints ---


@pytest.mark.parametrize(
    "content, expected_err_line",
    [
        (
            "start_hub: s 0 0\nend_hub: e 1 1",
            1,
        ),  # nb_drones missing or not first
        (
            "nb_drones: -5\nstart_hub: s 0 0\nend_hub: e 1 1",
            1,
        ),  # negative drones
        (
            "nb_drones: zero\nstart_hub: s 0 0\nend_hub: e 1 1",
            1,
        ),  # invalid drones value (not a positive integer)
    ],
)
def test_invalid_nb_drones(tmp_path, content, expected_err_line):
    """Tests various invalid drone number specifications."""
    file_path = create_temp_file(tmp_path, content)
    parser = ConfigParser(file_path)
    with pytest.raises(ParsingError) as exc_info:
        parser.parse()
    assert exc_info.value.line == expected_err_line


# --- Hub Constraints ---


@pytest.mark.parametrize(
    "content, expected_err_msg",
    [
        ("nb_drones: 1\nhub: A 0 0\nend_hub: e 1 1", "start_hub not defined"),
        ("nb_drones: 1\nstart_hub: s 0 0\nhub: A 1 1", "end_hub not defined"),
        (
            "nb_drones: 1\nstart_hub: s1 0 0\nstart_hub: s2 1 1\nend_hub: e 2 2",
            "Multiple start_hub defined",
        ),
        (
            "nb_drones: 1\nstart_hub: s 0 0\nend_hub: e1 1 1\nend_hub: e2 2 2",
            "Multiple end_hub defined",
        ),
        (
            "nb_drones: 1\nstart_hub: A 0 0\nend_hub: e 1 1\nhub: A 2 2",
            "Each zone must have a unique name",
        ),
        (
            "nb_drones: 1\nstart_hub: s 0 0\nend_hub: e 1 1\nhub: H 2 2\nhub: H 3 3",
            "Zone 'H' already defined",
        ),
    ],
)
def test_hub_uniqueness_and_presence(tmp_path, content, expected_err_msg):
    """Tests requirements for presence and uniqueness of start, end, and regular hubs."""
    file_path = create_temp_file(tmp_path, content)
    parser = ConfigParser(file_path)
    with pytest.raises(ParsingError) as exc_info:
        parser.parse()
    assert expected_err_msg in exc_info.value.message


@pytest.mark.parametrize(
    "content",
    [
        "nb_drones: 1\nstart_hub: invalid-name 0 0\nend_hub: e 1 1",
        "nb_drones: 1\nstart_hub: s 0 0\nend_hub: e 1 1\nhub: bad-name 2 2",
        "nb_drones: 1\nstart_hub: s 0 0\nend_hub: e 1 1\nconnection: s-invalid-name",  # regex for connection name match also forbids it
    ],
)
def test_invalid_names_dashes_spaces(tmp_path, content):
    """Verifies that zone names with dashes (forbidden by connection syntax) or spaces are rejected."""
    file_path = create_temp_file(tmp_path, content)
    parser = ConfigParser(file_path)
    with pytest.raises(ParsingError):
        parser.parse()


# --- Connection Constraints ---


@pytest.mark.parametrize(
    "content, expected_err_msg",
    [
        (
            "nb_drones: 1\nstart_hub: s 0 0\nend_hub: e 1 1\nconnection: s-A",
            "Connections must link only previously defined zones",
        ),
        (
            "nb_drones: 1\nstart_hub: s 0 0\nend_hub: e 1 1\nconnection: s-e\nconnection: s-e",
            "The same connection must not appear more than once",
        ),
        (
            "nb_drones: 1\nstart_hub: s 0 0\nend_hub: e 1 1\nconnection: s-e\nconnection: e-s",
            "The same connection must not appear more than once",
        ),
        (
            "nb_drones: 1\nstart_hub: s 0 0\nend_hub: e 1 1\nconnection: s",
            "Syntax error",
        ),
    ],
)
def test_connection_validation(tmp_path, content, expected_err_msg):
    """Tests link validity, duplication prevention, and format of connections."""
    file_path = create_temp_file(tmp_path, content)
    parser = ConfigParser(file_path)
    with pytest.raises(ParsingError) as exc_info:
        parser.parse()
    assert expected_err_msg in exc_info.value.message


# --- Metadata Constraints ---


@pytest.mark.parametrize(
    "content, expected_err_msg",
    [
        (
            "nb_drones: 1\nstart_hub: s 0 0 [zone=invalid_zone]\nend_hub: e 1 1",
            "Input should be",  # Pydantic enum validation failure
        ),
        (
            "nb_drones: 1\nstart_hub: s 0 0 [color=invalid_color]\nend_hub: e 1 1",
            "Input should be",
        ),
        (
            "nb_drones: 1\nstart_hub: s 0 0 [max_drones=0]\nend_hub: e 1 1",
            "Input should be greater than 0",
        ),
        (
            "nb_drones: 1\nstart_hub: s 0 0 [max_drones=-5]\nend_hub: e 1 1",
            "Input should be greater than 0",
        ),
        (
            "nb_drones: 1\nstart_hub: s 0 0 [max_drones=not_int]\nend_hub: e 1 1",
            "max_drones must be an integer",
        ),
        (
            "nb_drones: 1\nstart_hub: s 0 0\nend_hub: e 1 1\nconnection: s-e [max_link_capacity=0]",
            "Input should be greater than 0",
        ),
        (
            "nb_drones: 1\nstart_hub: s 0 0\nend_hub: e 1 1\nconnection: s-e [max_link_capacity=not_int]",
            "max_link_capacity must be an integer",
        ),
        (
            "nb_drones: 1\nstart_hub: s 0 0 [invalid_format_no_equals]\nend_hub: e 1 1",
            "Invalid metadata format",
        ),
    ],
)
def test_metadata_validation(tmp_path, content, expected_err_msg):
    """Tests metadata parsing and Pydantic model validation for zone types, colors, and capacities."""
    file_path = create_temp_file(tmp_path, content)
    parser = ConfigParser(file_path)
    with pytest.raises(ParsingError) as exc_info:
        parser.parse()
    assert expected_err_msg in exc_info.value.message


# --- General Edge Cases ---


def test_missing_file():
    """Verifies that an error is raised when trying to parse a non-existent file."""
    parser = ConfigParser("non_existent_file.txt")
    with pytest.raises(ParsingError) as exc_info:
        parser.parse()
    assert "File not found" in exc_info.value.message


@pytest.mark.parametrize(
    "content, expected_err_msg",
    [
        (
            "nb_drones: 1\nstart_hub: s 0 0\nend_hub: e 1 1\nsomething invalid",
            "Syntax error: 'something invalid'",
        ),
        (
            "nb_drones: 1\nstart_hub: s 0 0\nend_hub: e 1.5 1",
            "Syntax error: 'end_hub: e 1.5 1'",  # floats not matched by regex COORD
        ),
    ],
)
def test_general_syntax_errors(tmp_path, content, expected_err_msg):
    """Tests general syntax errors like malformed lines or unsupported value types (e.g., floats for coordinates)."""
    file_path = create_temp_file(tmp_path, content)
    parser = ConfigParser(file_path)
    with pytest.raises(ParsingError) as exc_info:
        parser.parse()
    assert expected_err_msg in exc_info.value.message
