"""Pygame-based visualiser for the drone routing simulation."""

import math
import pygame  # type: ignore[import-untyped]

from graph.graph import Graph
from algorithm.simulator import SimulationResult
from packages.parsing.config_models import ZoneType
from visualization.colors import (
    BG, PANEL_BG, TEXT, TEXT_DIM,
    EDGE_NORMAL, EDGE_BLOCKED,
    PROGRESS_BG, PROGRESS_FG,
    ZONE_FILL, ZONE_BORDER,
    drone_color, node_fill, node_border,
)

W, H = 1280, 840
PANEL_H = 120
GRAPH_H = H - PANEL_H
FPS = 60

# Zone label text for the legend
_ZONE_LABELS: dict[ZoneType, str] = {
    ZoneType.NORMAL: "Normal",
    ZoneType.RESTRICTED: "Restricted (2t)",
    ZoneType.PRIORITY: "Priority",
    ZoneType.BLOCKED: "Blocked",
}


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


class Renderer:
    """Interactive pygame visualiser for the drone routing simulation."""

    def __init__(
        self, graph: Graph, result: SimulationResult
    ) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption(
            "Fly-in — Drone Routing Simulation"
        )
        self.clock = pygame.time.Clock()

        self.graph = graph
        self.result = result
        self.max_turn = result.total_turns
        self.nb = graph.nb_drones

        # Animation state
        self.turn: int = 0
        self.acc: float = 0.0      # fractional turn accumulator
        self.playing: bool = False
        self.speed: float = 2.0    # turns per second

        self._btns: dict[str, pygame.Rect] = {}
        self._compute_layout()
        self._init_fonts()

    # ----------------------------------------------------------------
    # Setup
    # ----------------------------------------------------------------

    def _init_fonts(self) -> None:
        self.f_xs = pygame.font.SysFont("monospace", 10)
        self.f_sm = pygame.font.SysFont("monospace", 12)
        self.f_md = pygame.font.SysFont("monospace", 15)
        self.f_lg = pygame.font.SysFont("monospace", 19, bold=True)

    def _compute_layout(self) -> None:
        nodes = self.graph.nodes
        xs = [n.zone.x for n in nodes.values()]
        ys = [n.zone.y for n in nodes.values()]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        span_x = max(float(max_x - min_x), 1.0)
        span_y = max(float(max_y - min_y), 1.0)

        pad = 80
        scale = min(
            (W - 2 * pad) / span_x,
            (GRAPH_H - 2 * pad) / span_y,
        )
        ox = pad + ((W - 2 * pad) - span_x * scale) / 2
        oy = pad + ((GRAPH_H - 2 * pad) - span_y * scale) / 2

        self.node_pos: dict[str, tuple[float, float]] = {}
        for name, node in nodes.items():
            sx = ox + (node.zone.x - min_x) * scale
            # Flip Y so positive is up
            sy = oy + (max_y - node.zone.y) * scale
            self.node_pos[name] = (sx, sy)

        self.nr = max(16, min(30, int(scale * 0.38)))
        self.dr = max(7, min(11, self.nr // 3 + 2))

    # ----------------------------------------------------------------
    # Main loop
    # ----------------------------------------------------------------

    def run(self) -> None:
        """Start the visualiser event loop."""
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if not self._on_key(event.key):
                        running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self._on_click(event.pos)

            if self.playing:
                self.acc += dt * self.speed
                steps = int(self.acc)
                if steps:
                    self.acc -= steps
                    self.turn = min(self.turn + steps, self.max_turn)
                    if self.turn >= self.max_turn:
                        self.playing = False
                        self.acc = 0.0

            self._draw(self.turn + (self.acc if self.playing else 0.0))
            pygame.display.flip()
        pygame.quit()

    # ----------------------------------------------------------------
    # Input
    # ----------------------------------------------------------------

    def _on_key(self, key: int) -> bool:
        if key in (pygame.K_ESCAPE, pygame.K_q):
            return False
        if key == pygame.K_SPACE:
            self._toggle_play()
        elif key == pygame.K_RIGHT:
            self._step(1)
        elif key == pygame.K_LEFT:
            self._step(-1)
        elif key in (pygame.K_r, pygame.K_HOME):
            self._reset()
        elif key == pygame.K_END:
            self._go(self.max_turn)
        elif key in (
            pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS
        ):
            self.speed = min(self.speed * 1.5, 16.0)
        elif key in (pygame.K_MINUS, pygame.K_KP_MINUS):
            self.speed = max(self.speed / 1.5, 0.25)
        return True

    def _on_click(self, pos: tuple[int, int]) -> None:
        for name, rect in self._btns.items():
            if rect.collidepoint(pos):
                self._on_btn(name)
                return

    def _on_btn(self, name: str) -> None:
        actions: dict[str, object] = {
            "play": self._toggle_play,
            "prev": lambda: self._step(-1),
            "next": lambda: self._step(1),
            "reset": self._reset,
            "end": lambda: self._go(self.max_turn),
            "slower": lambda: setattr(
                self, "speed", max(self.speed / 1.5, 0.25)
            ),
            "faster": lambda: setattr(
                self, "speed", min(self.speed * 1.5, 16.0)
            ),
        }
        fn = actions.get(name)
        if callable(fn):
            fn()

    def _toggle_play(self) -> None:
        if self.turn >= self.max_turn:
            self._reset()
        self.playing = not self.playing

    def _step(self, d: int) -> None:
        self.playing = False
        self.acc = 0.0
        self.turn = max(0, min(self.turn + d, self.max_turn))

    def _reset(self) -> None:
        self.playing = False
        self.turn = 0
        self.acc = 0.0

    def _go(self, t: int) -> None:
        self.playing = False
        self.turn = t
        self.acc = 0.0

    # ----------------------------------------------------------------
    # Drawing
    # ----------------------------------------------------------------

    def _draw(self, t: float) -> None:
        self.screen.fill(BG)
        self._btns.clear()
        self._draw_edges()
        self._draw_nodes()
        self._draw_drones(t)
        self._draw_panel(int(t))

    def _draw_edges(self) -> None:
        seen: set[tuple[str, str]] = set()
        for from_z, to_z, cap in self.graph.all_edges:
            key = (min(from_z, to_z), max(from_z, to_z))
            if key in seen:
                continue
            seen.add(key)
            p1 = self.node_pos[from_z]
            p2 = self.node_pos[to_z]
            blocked = (
                not self.graph.is_routable(from_z)
                or not self.graph.is_routable(to_z)
            )
            color = EDGE_BLOCKED if blocked else EDGE_NORMAL
            width = 1 if blocked else max(1, min(4, cap))
            pygame.draw.line(
                self.screen, color,
                (int(p1[0]), int(p1[1])),
                (int(p2[0]), int(p2[1])),
                width,
            )

    def _draw_nodes(self) -> None:
        for name, node in self.graph.nodes.items():
            cx, cy = (
                int(self.node_pos[name][0]),
                int(self.node_pos[name][1]),
            )
            zt = node.zone.metadata.zone_type
            cfg = self.graph.zone_color(name)
            fill = node_fill(zt, cfg)
            border = node_border(zt, cfg)
            is_hub = name in (
                self.graph.start_hub, self.graph.end_hub
            )

            if is_hub:
                self._draw_glow(cx, cy, self.nr + 6, border, 35)

            pygame.draw.circle(self.screen, fill, (cx, cy), self.nr)
            bw = 4 if is_hub else 2
            pygame.draw.circle(
                self.screen, border, (cx, cy), self.nr, bw
            )

            if zt == ZoneType.BLOCKED:
                d = self.nr - 6
                pygame.draw.line(
                    self.screen, border,
                    (cx - d, cy - d), (cx + d, cy + d), 2,
                )
                pygame.draw.line(
                    self.screen, border,
                    (cx + d, cy - d), (cx - d, cy + d), 2,
                )

            lbl = self.f_xs.render(name, True, TEXT_DIM)
            self.screen.blit(
                lbl,
                (cx - lbl.get_width() // 2, cy + self.nr + 3),
            )

    def _draw_drones(self, t: float) -> None:
        t_int = int(t)
        # Map node → drone list for cluster offsets
        at_node: dict[str, list[int]] = {}
        for did in range(1, self.nb + 1):
            node = self._node_at(did, t_int)
            if node is not None:
                at_node.setdefault(node, []).append(did)

        for did in range(1, self.nb + 1):
            px, py = self._drone_pos(did, t)
            node = self._node_at(did, t_int)
            if node and node in at_node:
                cluster = at_node[node]
                idx = cluster.index(did)
                total = len(cluster)
                dx, dy = self._cluster_offset(idx, total)
                px += dx
                py += dy

            cx, cy = int(px), int(py)
            color = drone_color(did)
            self._draw_glow(cx, cy, self.dr + 2, color, 55)
            pygame.draw.circle(self.screen, color, (cx, cy), self.dr)
            pygame.draw.circle(
                self.screen, (255, 255, 255), (cx, cy), self.dr, 1
            )
            lbl = self.f_xs.render(str(did), True, (255, 255, 255))
            self.screen.blit(lbl, lbl.get_rect(center=(cx, cy)))

    def _draw_panel(self, t: int) -> None:
        py = GRAPH_H
        pygame.draw.rect(self.screen, PANEL_BG, (0, py, W, PANEL_H))
        pygame.draw.line(
            self.screen, (40, 50, 70), (0, py), (W, py), 1
        )

        # Progress bar (thin strip at top of panel)
        prog = t / max(self.max_turn, 1)
        pygame.draw.rect(self.screen, PROGRESS_BG, (0, py, W, 4))
        pygame.draw.rect(
            self.screen, PROGRESS_FG, (0, py, int(W * prog), 4)
        )

        # --- Zone legend (left) ---
        lx, ly = 20, py + 18
        for zt, label in _ZONE_LABELS.items():
            sq = pygame.Rect(lx, ly, 14, 14)
            pygame.draw.rect(
                self.screen, ZONE_FILL[zt], sq, border_radius=3
            )
            pygame.draw.rect(
                self.screen, ZONE_BORDER[zt], sq, 2, border_radius=3
            )
            txt = self.f_sm.render(label, True, TEXT_DIM)
            self.screen.blit(txt, (lx + 18, ly - 1))
            ly += 22

        # --- Playback controls (center) ---
        cx = W // 2
        cy_btn = py + 40
        specs = [
            ("reset", "|<", cx - 150, 36),
            ("prev", " < ", cx - 100, 36),
            (
                "play",
                "  PAUSE  " if self.playing else "  PLAY  ",
                cx, 44,
            ),
            ("next", " > ", cx + 100, 36),
            ("end", ">|", cx + 150, 36),
        ]
        for name, btn_txt, bx, bw in specs:
            btn_txt_s: str = btn_txt
            rect = pygame.Rect(bx - bw // 2, cy_btn - 18, bw, 36)
            active = name == "play" and self.playing
            fc = (48, 90, 175) if active else (32, 42, 62)
            bc = (95, 148, 240) if active else (65, 85, 115)
            pygame.draw.rect(
                self.screen, fc, rect, border_radius=6
            )
            pygame.draw.rect(
                self.screen, bc, rect, 2, border_radius=6
            )
            btn_lbl = self.f_md.render(btn_txt_s, True, TEXT)
            self.screen.blit(
                btn_lbl, btn_lbl.get_rect(center=rect.center)
            )
            self._btns[name] = rect

        # Turn counter below buttons
        turn_txt = f"Turn  {t}  /  {self.max_turn}"
        lbl = self.f_lg.render(turn_txt, True, TEXT)
        self.screen.blit(
            lbl, lbl.get_rect(center=(cx, py + 88))
        )

        # --- Right: speed + stats + hints ---
        rx = W - 250
        ry = py + 14

        spd = self.f_sm.render(
            f"Speed: {self.speed:.2g}×", True, TEXT_DIM
        )
        self.screen.blit(spd, (rx, ry))

        for spd_rect, spd_name, spd_txt in [
            (pygame.Rect(rx + 138, ry - 2, 26, 22), "slower", "-"),
            (pygame.Rect(rx + 168, ry - 2, 26, 22), "faster", "+"),
        ]:
            pygame.draw.rect(
                self.screen, (32, 42, 62), spd_rect, border_radius=4
            )
            pygame.draw.rect(
                self.screen, (65, 85, 115), spd_rect, 2,
                border_radius=4,
            )
            spd_lbl = self.f_md.render(spd_txt, True, TEXT)
            self.screen.blit(
                spd_lbl, spd_lbl.get_rect(center=spd_rect.center)
            )
            self._btns[spd_name] = spd_rect

        arrived = sum(
            1 for did in range(1, self.nb + 1)
            if self.result.paths[did][-1][0] <= t
        )
        arr = self.f_sm.render(
            f"Arrived: {arrived} / {self.nb}", True, TEXT_DIM
        )
        self.screen.blit(arr, (rx, ry + 28))

        hints = (
            "Space: play/pause  ←/→: step  "
            "+/-: speed  r: reset  Esc: quit"
        )
        hint_lbl = self.f_xs.render(hints, True, TEXT_DIM)
        self.screen.blit(hint_lbl, (rx - 30, py + PANEL_H - 22))

    # ----------------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------------

    def _draw_glow(
        self,
        cx: int,
        cy: int,
        radius: int,
        color: tuple[int, int, int],
        alpha: int,
    ) -> None:
        sz = radius * 2
        surf = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)
        pygame.draw.circle(
            surf, (*color, alpha), (sz, sz), sz
        )
        self.screen.blit(surf, (cx - sz, cy - sz))

    def _node_at(self, drone_id: int, t: int) -> str | None:
        """Return zone name if drone is at a node at integer turn t."""
        for pt, node in self.result.paths[drone_id]:
            if pt == t:
                return node
        return None

    def _drone_pos_int(
        self, drone_id: int, t: int
    ) -> tuple[float, float]:
        """Return screen position of drone at integer turn t."""
        path = self.result.paths[drone_id]
        if t <= path[0][0]:
            return self.node_pos[path[0][1]]
        if t >= path[-1][0]:
            return self.node_pos[path[-1][1]]
        for i in range(1, len(path)):
            pt, node = path[i]
            ppt, pnode = path[i - 1]
            if ppt <= t <= pt:
                frac = (t - ppt) / max(pt - ppt, 1)
                sx, sy = self.node_pos[pnode]
                dx, dy = self.node_pos[node]
                return sx + (dx - sx) * frac, sy + (dy - sy) * frac
        return self.node_pos[path[-1][1]]

    def _drone_pos(
        self, drone_id: int, t: float
    ) -> tuple[float, float]:
        """Return interpolated screen position at continuous time t."""
        t0 = int(t)
        prog = t - t0
        x0, y0 = self._drone_pos_int(drone_id, t0)
        x1, y1 = self._drone_pos_int(drone_id, t0 + 1)
        return _lerp(x0, x1, prog), _lerp(y0, y1, prog)

    def _cluster_offset(
        self, idx: int, total: int
    ) -> tuple[float, float]:
        """Return (dx, dy) offset for drone idx within a same-node cluster."""
        if total == 1:
            return 0.0, 0.0
        cols = min(4, total)
        rows = math.ceil(total / cols)
        row = idx // cols
        col = idx % cols
        spacing = float(
            min(self.dr * 2 + 2, (self.nr * 2) // max(cols, rows))
        )
        dx = (col - (cols - 1) / 2) * spacing
        dy = (row - (rows - 1) / 2) * spacing
        return dx, dy
