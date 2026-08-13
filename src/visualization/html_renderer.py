"""Web-based visualiser generating a self-contained HTML file."""

import json
import os
import tempfile
import webbrowser
from pathlib import Path
from typing import Any, Dict, List

from graph.graph import Graph
from algorithm.simulator import SimulationResult


class HtmlRenderer:
    """Generates a self-contained HTML visualiser and opens it in a browser."""

    def __init__(self, graph: Graph, result: SimulationResult) -> None:
        self.graph = graph
        self.result = result

    def _build_data(self) -> Dict[str, Any]:
        """Convert graph and result to a JSON-serializable dict."""
        nodes: Dict[str, Any] = {}
        for name, node in self.graph.nodes.items():
            nodes[name] = {
                "x": node.zone.x,
                "y": node.zone.y,
                "type": node.zone.metadata.zone_type.name,
                "color": self.graph.zone_color(name),
                "is_hub": name in (self.graph.start_hub, self.graph.end_hub),
                "is_start": name == self.graph.start_hub,
                "is_end": name == self.graph.end_hub,
            }

        edges: List[Dict[str, Any]] = []
        seen = set()
        for from_z, to_z, cap in self.graph.all_edges:
            key = (min(from_z, to_z), max(from_z, to_z))
            if key in seen:
                continue
            seen.add(key)
            blocked = not self.graph.is_routable(
                from_z
            ) or not self.graph.is_routable(  # noqa: E501
                to_z
            )
            edges.append(
                {"from": from_z, "to": to_z, "blocked": blocked, "cap": cap}
            )

        # Format paths for JS: drone_id -> array of {t: time, node: node_name}
        paths: Dict[int, List[Dict[str, Any]]] = {}
        for did, path in self.result.paths.items():
            paths[did] = [{"t": pt, "node": pnode} for pt, pnode in path]

        return {
            "nodes": nodes,
            "edges": edges,
            "paths": paths,
            "maxTurn": self.result.total_turns,
            "nbDrones": self.graph.nb_drones,
        }

    def _get_html_template(self) -> str:
        base_dir = Path(__file__).parent
        template = (base_dir / "template.html").read_text(encoding="utf-8")
        style = (base_dir / "style.css").read_text(encoding="utf-8")
        script = (base_dir / "script.js").read_text(encoding="utf-8")

        template = template.replace("/*STYLE_PLACEHOLDER*/", style)
        template = template.replace("/*SCRIPT_PLACEHOLDER*/", script)
        return template

    def run(self) -> None:
        """Generate the HTML file and open it."""
        data = self._build_data()
        json_data = json.dumps(data)

        html = self._get_html_template()
        # Inject the JSON string into the placeholder
        html = html.replace("/*DATA_PLACEHOLDER*/{}", json_data)

        # Write to a temporary file
        fd, path = tempfile.mkstemp(suffix=".html", prefix="fly_in_")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(html)

        # print(f"\\nVisualisation generated at: {path}")
        # print("Opening in default browser...")

        # Open in default browser
        webbrowser.open(f"file://{path}")
