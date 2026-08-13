import re
from typing import Any
from pydantic import ValidationError

from packages.parsing.config_models import (
    Config,
    Zone,
    Connection,
    Metadata,
)
from packages.utils.regexp import DRONES_LINE, ZONE_LINE, CONNECTION_LINE


class ParsingError(Exception):
    """Exception raised for errors during configuration parsing."""
    def __init__(self, message: str, line: int):
        self.message = message
        self.line = line
        super().__init__(self.message)

    def __str__(self) -> str:
        return f"{self.message}, line: {self.line}"


class ConfigParser:
    """Parser for reading and validating network configuration files."""
    def __init__(self, config_path: str) -> None:
        """Initialize the parser with a file path."""
        self.config_path = config_path
        self._reset_state()

    def _reset_state(self) -> None:
        self._nb_drones: int | None = None
        self._start_hub: Zone | None = None
        self._end_hub: Zone | None = None
        self._hubs: dict[str, Zone] = {}
        self._connections: list[Connection] = []

    def parse(self) -> Config:
        """Parse the configuration file and return a Config object."""
        self._reset_state()
        line_idx = 0
        try:
            with open(self.config_path, "r") as f:
                for line_idx, raw_line in enumerate(f, start=1):
                    self._parse_line(raw_line, line_idx)
        except FileNotFoundError:
            raise ParsingError(f"File not found: {self.config_path}", 0)

        return self._finalize_config(line_idx)

    def _parse_line(self, raw_line: str, line_idx: int) -> None:
        line = raw_line.split("#")[0].strip()
        if not line:
            return

        if self._nb_drones is None:
            self._nb_drones = self._parse_drones_count(line, line_idx)
            return

        if self._try_handle_zone(line, line_idx):
            return

        if self._try_handle_connection(line, line_idx):
            return

        raise ParsingError(f"Syntax error: '{line}'", line_idx)

    def _parse_drones_count(self, line: str, line_idx: int) -> int:
        match = re.match(DRONES_LINE, line)
        if not match:
            raise ParsingError(
                "The first line must define the number of "
                "drones using nb_drones: <positive_integer>.",
                line_idx,
            )
        return int(match.group("count"))

    def _try_handle_zone(self, line: str, line_idx: int) -> bool:
        zone_match = re.match(ZONE_LINE, line)
        if not zone_match:
            return False

        z_type, zone_obj = self._process_zone(zone_match, line_idx)
        self._register_zone(z_type, zone_obj, line_idx)
        return True

    def _process_zone(
        self, zone_match: re.Match, line_idx: int
    ) -> tuple[str, Zone]:
        z_type = zone_match.group("type")
        z_name = zone_match.group("name")
        z_x = int(zone_match.group("x"))
        z_y = int(zone_match.group("y"))
        z_meta_str = zone_match.group("metadata")

        meta_data = self._parse_metadata(z_meta_str, line_idx)
        try:
            metadata_obj = Metadata(**meta_data)
            zone_obj = Zone(
                name=z_name,
                x=z_x,
                y=z_y,
                metadata=metadata_obj,
            )
            return z_type, zone_obj
        except ValidationError as e:
            raise ParsingError(e.errors()[0]["msg"], line_idx)

    def _register_zone(
        self, z_type: str, zone_obj: Zone, line_idx: int
    ) -> None:
        if z_type == "start_hub":
            if self._start_hub:
                raise ParsingError("Multiple start_hub defined", line_idx)
            self._start_hub = zone_obj
        elif z_type == "end_hub":
            if self._end_hub:
                raise ParsingError("Multiple end_hub defined", line_idx)
            self._end_hub = zone_obj
        else:
            if zone_obj.name in self._hubs:
                raise ParsingError(
                    f"Zone '{zone_obj.name}' already defined", line_idx
                )
            self._hubs[zone_obj.name] = zone_obj

    def _try_handle_connection(self, line: str, line_idx: int) -> bool:
        conn_match = re.match(CONNECTION_LINE, line)
        if not conn_match:
            return False

        conn_obj = self._process_connection(conn_match, line_idx)
        self._connections.append(conn_obj)
        return True

    def _process_connection(
        self, conn_match: re.Match, line_idx: int
    ) -> Connection:
        c_connection = conn_match.group("connection")
        c_meta_str = conn_match.group("metadata")

        meta_data = self._parse_metadata(c_meta_str, line_idx)
        try:
            conn_args = {"connection": c_connection}
            if "max_link_capacity" in meta_data:
                conn_args["max_link_capacity"] = meta_data["max_link_capacity"]

            return Connection(**conn_args)
        except ValidationError as e:
            raise ParsingError(e.errors()[0]["msg"], line_idx)

    def _parse_metadata(
        self, metadata_str: str | None, line_idx: int
    ) -> dict[str, Any]:
        if not metadata_str:
            return {}

        metadata_dict: dict[str, Any] = {}
        for part in metadata_str.split():
            key, value = self._split_metadata_part(part, line_idx)
            self._process_metadata_item(key, value, metadata_dict, line_idx)
        return metadata_dict

    def _split_metadata_part(
        self, part: str, line_idx: int
    ) -> tuple[str, str]:
        if "=" not in part:
            raise ParsingError(f"Invalid metadata format: '{part}'", line_idx)
        parts = part.split("=", 1)
        return parts[0], parts[1]

    def _process_metadata_item(
        self,
        key: str,
        value: str,
        metadata_dict: dict[str, Any],
        line_idx: int,
    ) -> None:
        if key == "zone":
            metadata_dict["zone_type"] = value
        elif key == "color":
            metadata_dict["color"] = value
        elif key in ("max_drones", "max_link_capacity"):
            metadata_dict[key] = self._parse_int_metadata(key, value, line_idx)
        else:
            metadata_dict[key] = value

    def _parse_int_metadata(self, key: str, value: str, line_idx: int) -> int:
        try:
            return int(value)
        except ValueError:
            raise ParsingError(
                f"{key} must be an integer, got '{value}'", line_idx
            )

    def _finalize_config(self, line_idx: int) -> Config:
        if self._nb_drones is None:
            raise ParsingError("nb_drones not defined", 0)
        if not self._start_hub:
            raise ParsingError("start_hub not defined", 0)
        if not self._end_hub:
            raise ParsingError("end_hub not defined", 0)

        try:
            return Config(
                nb_drones=self._nb_drones,
                start_hub=self._start_hub,
                end_hub=self._end_hub,
                hubs=self._hubs,
                connections=self._connections,
            )
        except (ValidationError, ValueError) as e:
            msg = (
                e.errors()[0]["msg"]
                if isinstance(e, ValidationError)
                else str(e)
            )
            raise ParsingError(msg, line_idx)
