NO_DASH_OR_SPACE_REGEX = r"^[^- ]+$"

# Building blocks
NAME = r"[^- ]+"
COORD = r"-?\d+"
METADATA_BLOCK = r"\[(?P<metadata>.*)\]"

# Line patterns
DRONES_LINE = rf"^nb_drones:\s+(?P<count>\d+)$"
ZONE_LINE = rf"^(?P<type>start_hub|end_hub|hub):\s+(?P<name>{NAME})\s+(?P<x>{COORD})\s+(?P<y>{COORD})(?:\s+{METADATA_BLOCK})?$"
CONNECTION_LINE = rf"^connection:\s+(?P<connection>{NAME}-{NAME})(?:\s+{METADATA_BLOCK})?$"
