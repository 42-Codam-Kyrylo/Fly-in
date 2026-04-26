NO_DASH_OR_SPACE_REGEX = r"^[^- ]+$"

# Building blocks
NAME = r"[^- ]+"
COORD = r"-?\d+"
METADATA_BLOCK = r"\[(?P<metadata>.*)\]"

# Line patterns
DRONES_LINE = r"^nb_drones:\s+(?P<count>\d+)$"

ZONE_LINE = (
    rf"^(?P<type>start_hub|end_hub|hub):\s+"
    rf"(?P<name>{NAME})\s+"
    rf"(?P<x>{COORD})\s+"
    rf"(?P<y>{COORD})"
    rf"(?:\s+{METADATA_BLOCK})?$"
)

CONNECTION_LINE = (
    rf"^connection:\s+(?P<connection>{NAME}-{NAME})(?:\s+{METADATA_BLOCK})?$"
)
