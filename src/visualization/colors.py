"""Color constants and helpers for the visualiser."""

from packages.parsing.config_models import ZoneType

type RGBColor = tuple[int, int, int]

# -- UI palette --
BG: RGBColor = (12, 14, 20)
PANEL_BG: RGBColor = (18, 22, 32)
TEXT: RGBColor = (210, 218, 235)
TEXT_DIM: RGBColor = (110, 125, 150)
EDGE_NORMAL: RGBColor = (48, 58, 82)
EDGE_BLOCKED: RGBColor = (32, 36, 48)
PROGRESS_BG: RGBColor = (28, 34, 50)
PROGRESS_FG: RGBColor = (60, 120, 220)

# -- Zone fill (dark node background) --
ZONE_FILL: dict[ZoneType, RGBColor] = {
    ZoneType.NORMAL: (28, 52, 108),
    ZoneType.BLOCKED: (30, 30, 36),
    ZoneType.RESTRICTED: (98, 46, 14),
    ZoneType.PRIORITY: (18, 82, 38),
}

# -- Zone border (bright accent) --
ZONE_BORDER: dict[ZoneType, RGBColor] = {
    ZoneType.NORMAL: (75, 115, 210),
    ZoneType.BLOCKED: (56, 56, 66),
    ZoneType.RESTRICTED: (215, 110, 35),
    ZoneType.PRIORITY: (50, 185, 90),
}

# -- Config color name → RGB --
_CFG: dict[str, RGBColor] = {
    "red": (200, 55, 55),
    "orange": (210, 130, 40),
    "green": (55, 180, 75),
    "yellow": (210, 195, 50),
    "blue": (60, 110, 210),
    "gray": (120, 125, 140),
    "black": (35, 35, 42),
    "purple": (140, 75, 195),
    "gold": (210, 175, 38),
    "maroon": (130, 28, 55),
    "darkred": (150, 28, 28),
    "brown": (140, 95, 55),
    "cyan": (55, 190, 210),
    "crimson": (190, 28, 55),
    "lime": (110, 210, 55),
    "magenta": (210, 55, 195),
    "rainbow": (100, 195, 230),
    "violet": (155, 75, 215),
}

# -- 25 distinct drone colors --
DRONE_PALETTE: list[RGBColor] = [
    (255, 85, 85),   (85, 155, 255), (85, 215, 85),  (255, 200, 45),
    (215, 85, 255),  (85, 235, 215), (255, 140, 45),  (200, 200, 85),
    (255, 105, 195), (85, 195, 175), (200, 130, 85),  (130, 200, 255),
    (255, 175, 175), (175, 255, 175), (175, 175, 255), (255, 255, 120),
    (255, 120, 255), (120, 255, 255), (200, 85, 85),   (85, 85, 200),
    (85, 200, 85),   (200, 200, 85),  (200, 85, 200),  (85, 200, 200),
    (255, 160, 85),
]


def drone_color(drone_id: int) -> RGBColor:
    """Return the display color for drone *drone_id* (1-indexed)."""
    return DRONE_PALETTE[(drone_id - 1) % len(DRONE_PALETTE)]


def node_fill(zone_type: ZoneType, cfg_color: str | None) -> RGBColor:
    """Return node fill color (darkened config color or zone default)."""
    if cfg_color and cfg_color in _CFG:
        r, g, b = _CFG[cfg_color]
        return (int(r * 0.45), int(g * 0.45), int(b * 0.45))
    return ZONE_FILL[zone_type]


def node_border(zone_type: ZoneType, cfg_color: str | None) -> RGBColor:
    """Return node border color (config color or zone accent)."""
    if cfg_color and cfg_color in _CFG:
        return _CFG[cfg_color]
    return ZONE_BORDER[zone_type]
