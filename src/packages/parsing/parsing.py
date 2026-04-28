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
    def __init__(self, message: str, line: int):
        self.message = message
        self.line = line
        super().__init__(self.message)

    def __str__(self) -> str:
        return f"{self.message}, line: {self.line}"


class ConfigParser:
    def __init__(self, config_path: str) -> None:
        self.config_path = config_path

    def parse(self) -> Config:
        nb_drones = None
        start_hub = None
        end_hub = None
        hubs = {}
        connections = []

        try:
            with open(self.config_path, "r") as f:
                for line_idx, raw_line in enumerate(f, start=1):
                    line = raw_line.split("#")[0].strip()
                    if not line:
                        continue

                    if nb_drones is None:
                        match = re.match(DRONES_LINE, line)
                        if not match:
                            raise ParsingError(
                                "The first line must define the number of "
                                "drones using nb_drones: <positive_integer>.",
                                line_idx,
                            )
                        nb_drones = int(match.group("count"))
                        continue

                    zone_match = re.match(ZONE_LINE, line)
                    if zone_match:
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
                        except ValidationError as e:
                            msg = e.errors()[0]["msg"]
                            raise ParsingError(msg, line_idx)

                        if z_type == "start_hub":
                            if start_hub:
                                raise ParsingError(
                                    "Multiple start_hub defined", line_idx
                                )
                            start_hub = zone_obj
                        elif z_type == "end_hub":
                            if end_hub:
                                raise ParsingError(
                                    "Multiple end_hub defined", line_idx
                                )
                            end_hub = zone_obj
                        else:
                            if z_name in hubs:
                                raise ParsingError(
                                    f"Zone '{z_name}' already defined",
                                    line_idx,
                                )
                            hubs[z_name] = zone_obj
                        continue

                    conn_match = re.match(CONNECTION_LINE, line)
                    if conn_match:
                        c_connection = conn_match.group("connection")
                        c_meta_str = conn_match.group("metadata")

                        meta_data = self._parse_metadata(c_meta_str, line_idx)
                        try:
                            conn_args = {"connection": c_connection}
                            if "max_link_capacity" in meta_data:
                                conn_args["max_link_capacity"] = meta_data[
                                    "max_link_capacity"
                                ]

                            conn_obj = Connection(**conn_args)
                        except ValidationError as e:
                            msg = e.errors()[0]["msg"]
                            raise ParsingError(msg, line_idx)

                        connections.append(conn_obj)
                        continue

                    # No match
                    raise ParsingError(f"Syntax error: '{line}'", line_idx)

        except FileNotFoundError:
            raise ParsingError(f"File not found: {self.config_path}", 0)

        # Post-parse validation
        if nb_drones is None:
            raise ParsingError("nb_drones not defined", 0)
        if not start_hub:
            raise ParsingError("start_hub not defined", 0)
        if not end_hub:
            raise ParsingError("end_hub not defined", 0)

        try:
            config = Config(
                nb_drones=nb_drones,
                start_hub=start_hub,
                end_hub=end_hub,
                hubs=hubs,
                connections=connections,
            )
            return config
        except (ValidationError, ValueError) as e:
            if isinstance(e, ValidationError):
                msg = e.errors()[0]["msg"]
            else:
                msg = str(e)
            raise ParsingError(msg, line_idx if "line_idx" in locals() else 0)

    def _parse_metadata(
        self, metadata_str: str | None, line_idx: int
    ) -> dict[str, Any]:
        if not metadata_str:
            return {}

        metadata_dict = {}
        for part in metadata_str.split():
            if "=" not in part:
                raise ParsingError(
                    f"Invalid metadata format: '{part}'", line_idx
                )
            key, value = part.split("=", 1)

            if key == "zone":
                metadata_dict["zone_type"] = value
            elif key == "color":
                metadata_dict["color"] = value
            elif key == "max_drones":
                try:
                    metadata_dict["max_drones"] = int(value)
                except ValueError:
                    raise ParsingError(
                        f"max_drones must be an integer, got '{value}'",
                        line_idx,
                    )
            elif key == "max_link_capacity":
                try:
                    metadata_dict["max_link_capacity"] = int(value)
                except ValueError:
                    raise ParsingError(
                        f"max_link_capacity must be an integer, got '{value}'",
                        line_idx,
                    )
            else:
                metadata_dict[key] = value
        return metadata_dict
