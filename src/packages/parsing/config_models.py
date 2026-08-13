from pydantic import BaseModel, Field, model_validator
from enum import StrEnum, auto
from packages.utils import NO_DASH_OR_SPACE_REGEX


class ZoneType(StrEnum):
    """Enumeration of possible zone types."""
    NORMAL = auto()
    BLOCKED = auto()
    RESTRICTED = auto()
    PRIORITY = auto()

    @property
    def cost(self) -> int | float:
        """Get the base cost associated with the zone type."""
        mapping: dict[ZoneType, int | float] = {
            ZoneType.NORMAL: 1,
            ZoneType.RESTRICTED: 2,
            ZoneType.PRIORITY: 1,
            ZoneType.BLOCKED: float("inf"),
        }
        return mapping.get(self, 1)


class Colors(StrEnum):
    """Enumeration of allowed colors for visualization."""
    RED = auto()
    ORANGE = auto()
    GREEN = auto()
    YELLOW = auto()
    BLUE = auto()
    GRAY = auto()
    BLACK = auto()
    PURPLE = auto()
    GOLD = auto()
    MAROON = auto()
    DARKRED = auto()
    BROWN = auto()
    CYAN = auto()
    CRIMSON = auto()
    LIME = auto()
    MAGENTA = auto()
    RAINBOW = auto()
    VIOLET = auto()


class Metadata(BaseModel):
    """Metadata attributes for a zone."""
    zone_type: ZoneType = ZoneType.NORMAL
    color: Colors | None = None
    max_drones: int = Field(gt=0, default=1)


class Zone(BaseModel):
    """Represents a location or hub in the drone network."""
    name: str = Field(pattern=NO_DASH_OR_SPACE_REGEX)
    x: int
    y: int
    metadata: Metadata


class Connection(BaseModel):
    """Represents a link between two zones."""
    connection: str
    max_link_capacity: int = Field(gt=0, default=1)


class Config(BaseModel):
    """Complete parsed configuration of the drone network."""
    nb_drones: int = Field(gt=0)
    start_hub: Zone
    end_hub: Zone
    hubs: dict[str, Zone]
    connections: list[Connection]

    @model_validator(mode="after")
    def validate_unique_zone_names(self) -> "Config":
        """Ensure all zones have distinct names."""
        zones = [self.start_hub, self.end_hub, *self.hubs.values()]
        names = [zone.name for zone in zones]
        if len(names) != len(set(names)):
            raise ValueError("Each zone must have a unique name")
        return self

    @model_validator(mode="after")
    def validate_connection_link(self) -> "Config":
        """Ensure connections only link defined zones."""
        defined_zone_names = {
            self.start_hub.name,
            self.end_hub.name,
            *(zone.name for zone in self.hubs.values()),
        }

        for connection in self.connections:
            endpoints = connection.connection.split("-")
            if len(endpoints) != 2 or not all(endpoints):
                raise ValueError(
                    "Invalid connection format. Expected '<zone1>-<zone2>'"
                )

            zone_a, zone_b = endpoints
            if (
                zone_a not in defined_zone_names
                or zone_b not in defined_zone_names
            ):
                raise ValueError(
                    "Connections must link only previously defined zones"
                )

        return self

    @model_validator(mode="after")
    def validate_connection_duplicates(self) -> "Config":
        """Ensure no duplicate connections exist."""
        normalized_connections: list[tuple[str, str]] = []
        for connection in self.connections:
            endpoints = connection.connection.split("-")
            if len(endpoints) != 2 or not all(endpoints):
                raise ValueError(
                    "Invalid connection format. Expected '<zone1>-<zone2>'"
                )

            zone_a, zone_b = endpoints
            zone_tuple = tuple(sorted((zone_a, zone_b)))
            if len(zone_tuple) == 2:
                normalized_connections.append((zone_tuple[0], zone_tuple[1]))

        if len(normalized_connections) != len(set(normalized_connections)):
            raise ValueError(
                "The same connection must not appear more than once"
            )
        return self
