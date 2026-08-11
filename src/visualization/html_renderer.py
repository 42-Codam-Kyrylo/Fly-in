# flake8: noqa: E501, W293, W391
"""Web-based visualiser generating a self-contained HTML file."""

import json
import os
import tempfile
import webbrowser
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
            ) or not self.graph.is_routable(to_z)
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
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fly-in Simulation Visualiser</title>
    <style>
        :root {
            --bg-main: #0c0e14;
            --bg-panel: #12161e;
            --text: #d2daeb;
            --text-dim: #6e7d96;
            --accent: #3c78dc;
            --accent-hover: #4e8ff0;
            --border: #303a52;
            --font-mono: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
            --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        }
        
        * { box-sizing: border-box; margin: 0; padding: 0; }
        
        body {
            background-color: var(--bg-main);
            color: var(--text);
            font-family: var(--font-sans);
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        #canvas-container {
            flex: 1;
            position: relative;
            width: 100%;
            height: calc(100vh - 80px);
        }

        canvas {
            display: block;
            width: 100%;
            height: 100%;
        }

        /* Bottom Panel */
        #controls {
            height: 80px;
            background-color: var(--bg-panel);
            border-top: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 30px;
            position: relative;
        }

        /* Timeline bar at the top of the controls */
        #timeline {
            position: absolute;
            top: -2px;
            left: 0;
            width: 100%;
            height: 4px;
            background-color: var(--border);
            cursor: pointer;
            z-index: 10;
            appearance: none;
            outline: none;
        }
        
        #timeline::-webkit-slider-thumb {
            appearance: none;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: var(--accent);
            cursor: pointer;
            margin-top: -4px;
            box-shadow: 0 0 10px var(--accent);
        }
        
        #timeline::-webkit-slider-runnable-track {
            height: 4px;
            background: linear-gradient(to right, var(--accent) var(--progress, 0%), transparent var(--progress, 0%));
        }

        .control-group {
            display: flex;
            align-items: center;
            gap: 15px;
        }

        button {
            background-color: var(--border);
            color: var(--text);
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-family: var(--font-sans);
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        button:hover {
            background-color: #404d6e;
        }
        
        button.primary {
            background-color: var(--accent);
            font-weight: 600;
            padding: 8px 24px;
        }
        
        button.primary:hover {
            background-color: var(--accent-hover);
        }

        .stat-box {
            font-family: var(--font-mono);
            font-size: 15px;
            display: flex;
            flex-direction: column;
            align-items: center;
            min-width: 120px;
        }
        
        .stat-label {
            font-size: 11px;
            color: var(--text-dim);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 4px;
        }
        
        .stat-value {
            font-weight: 600;
            font-size: 18px;
        }

        /* Legend */
        .legend {
            display: flex;
            gap: 20px;
            font-size: 13px;
            color: var(--text-dim);
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .legend-color {
            width: 12px;
            height: 12px;
            border-radius: 3px;
        }
    </style>
</head>
<body>

    <div id="canvas-container">
        <canvas id="viz"></canvas>
    </div>

    <div id="controls">
        <input type="range" id="timeline" min="0" max="1" step="0.01" value="0">
        
        <div class="control-group">
            <div class="legend">
                <div class="legend-item"><div class="legend-color" style="background:#1c346c; border:2px solid #4b73d2"></div>Normal</div>
                <div class="legend-item"><div class="legend-color" style="background:#622e0e; border:2px solid #d76e23"></div>Restricted</div>
                <div class="legend-item"><div class="legend-color" style="background:#125226; border:2px solid #32b95a"></div>Priority</div>
                <div class="legend-item"><div class="legend-color" style="background:#1e1e24; border:2px solid #383842"></div>Blocked</div>
            </div>
        </div>
        
        <div class="control-group">
            <button id="btn-reset">Reset</button>
            <button id="btn-step-back">Back</button>
            <button id="btn-play" class="primary">Play</button>
            <button id="btn-step-fwd">Step</button>
        </div>
        
        <div class="control-group">
            <div class="stat-box">
                <div class="stat-label">Speed</div>
                <div style="display:flex; align-items:center; gap:8px;">
                    <button id="btn-slower" style="padding:2px 8px">-</button>
                    <span id="speed-val" class="stat-value">2.0x</span>
                    <button id="btn-faster" style="padding:2px 8px">+</button>
                </div>
            </div>
            
            <div class="stat-box" style="margin-left: 15px;">
                <div class="stat-label">Turn</div>
                <div class="stat-value" id="turn-display">0 / 0</div>
            </div>
            
            <div class="stat-box" style="margin-left: 15px;">
                <div class="stat-label">Arrived</div>
                <div class="stat-value" id="arrived-display">0 / 0</div>
            </div>
        </div>
    </div>

    <script>
        // --- DATA INJECTION ---
        const simData = /*DATA_PLACEHOLDER*/{};
        
        // --- CONSTANTS & STYLES ---
        const COLORS = {
            bg: '#0c0e14',
            text: '#d2daeb',
            textDim: '#6e7d96',
            edgeNormal: '#303a52',
            edgeBlocked: '#202430',
            zoneFills: {
                NORMAL: '#1c346c',
                BLOCKED: '#1e1e24',
                RESTRICTED: '#622e0e',
                PRIORITY: '#125226'
            },
            zoneBorders: {
                NORMAL: '#4b73d2',
                BLOCKED: '#383842',
                RESTRICTED: '#d76e23',
                PRIORITY: '#32b95a'
            },
            // Named config colors
            cfg: {
                red: '#c83737', orange: '#d28228', green: '#37b44b', yellow: '#d2c332',
                blue: '#3c6ed2', gray: '#787d8c', black: '#23232a', purple: '#8c4bc3',
                gold: '#d2af26', maroon: '#821c37', darkred: '#961c1c', brown: '#8c5f37',
                cyan: '#37bed2', crimson: '#be1c37', lime: '#6ed237', magenta: '#d237c3',
                rainbow: '#64c3e6', violet: '#9b4bd7'
            },
            drones: [
                '#ff5555', '#559bff', '#55d755', '#ffc82d', '#d755ff', '#55ebd7', '#ff8c2d', '#c8c855',
                '#ff69c3', '#55c3af', '#c88255', '#82c8ff', '#ffafaf', '#afffaf', '#afafff', '#ffff78',
                '#ff78ff', '#78ffff', '#c85555', '#5555c8', '#55c855', '#c8c855', '#c855c8', '#55c8c8', '#ffa055'
            ]
        };

        function getFill(type, cfgColor) {
            if (cfgColor && COLORS.cfg[cfgColor]) return darken(COLORS.cfg[cfgColor], 0.45);
            return COLORS.zoneFills[type];
        }
        function getBorder(type, cfgColor) {
            if (cfgColor && COLORS.cfg[cfgColor]) return COLORS.cfg[cfgColor];
            return COLORS.zoneBorders[type];
        }
        function getDroneColor(id) {
            return COLORS.drones[(id - 1) % COLORS.drones.length];
        }
        function darken(hex, factor) {
            let r = parseInt(hex.slice(1,3), 16) * factor;
            let g = parseInt(hex.slice(3,5), 16) * factor;
            let b = parseInt(hex.slice(5,7), 16) * factor;
            return `rgb(${Math.floor(r)},${Math.floor(g)},${Math.floor(b)})`;
        }
        function hexToRgba(hex, alpha) {
            let r = parseInt(hex.slice(1,3), 16);
            let g = parseInt(hex.slice(3,5), 16);
            let b = parseInt(hex.slice(5,7), 16);
            return `rgba(${r},${g},${b},${alpha})`;
        }

        // --- SETUP LOGIC ---
        const canvas = document.getElementById('viz');
        const ctx = canvas.getContext('2d');
        const container = document.getElementById('canvas-container');
        
        // Transform logic
        let scale = 1;
        let offsetX = 0;
        let offsetY = 0;
        let nodePos = {}; // Screen coordinates
        
        function resize() {
            canvas.width = container.clientWidth * window.devicePixelRatio;
            canvas.height = container.clientHeight * window.devicePixelRatio;
            ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
            computeLayout();
        }

        function computeLayout() {
            const pad = 60;
            let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
            for (const key in simData.nodes) {
                const n = simData.nodes[key];
                if (n.x < minX) minX = n.x;
                if (n.x > maxX) maxX = n.x;
                if (n.y < minY) minY = n.y;
                if (n.y > maxY) maxY = n.y;
            }
            
            const spanX = Math.max(maxX - minX, 1);
            const spanY = Math.max(maxY - minY, 1);
            
            const cw = container.clientWidth;
            const ch = container.clientHeight;
            
            scale = Math.min((cw - 2*pad) / spanX, (ch - 2*pad) / spanY);
            offsetX = pad + (cw - 2*pad - spanX * scale) / 2;
            offsetY = pad + (ch - 2*pad - spanY * scale) / 2;
            
            nodePos = {};
            for (const key in simData.nodes) {
                const n = simData.nodes[key];
                nodePos[key] = {
                    x: offsetX + (n.x - minX) * scale,
                    y: offsetY + (maxY - n.y) * scale // flip Y
                };
            }
        }

        window.addEventListener('resize', resize);

        // --- ANIMATION STATE ---
        let time = 0;
        let playing = false;
        let speed = 2.0;
        let lastTimestamp = 0;

        // UI Elements
        const elTimeline = document.getElementById('timeline');
        const elTurn = document.getElementById('turn-display');
        const elArrived = document.getElementById('arrived-display');
        const elSpeed = document.getElementById('speed-val');
        const btnPlay = document.getElementById('btn-play');

        elTimeline.max = simData.maxTurn;
        
        function updateUI() {
            const turn = Math.floor(time);
            elTurn.innerText = `${turn} / ${simData.maxTurn}`;
            
            let arrivedCount = 0;
            for (const key in simData.paths) {
                const path = simData.paths[key];
                if (path[path.length - 1].t <= time) arrivedCount++;
            }
            elArrived.innerText = `${arrivedCount} / ${simData.nbDrones}`;
            
            elTimeline.value = time;
            const progressPct = (time / simData.maxTurn) * 100;
            elTimeline.style.setProperty('--progress', `${progressPct}%`);
            
            btnPlay.innerText = playing ? 'Pause' : 'Play';
            btnPlay.classList.toggle('primary', !playing);
        }

        // --- RENDER LOOP ---
        function render(timestamp) {
            if (!lastTimestamp) lastTimestamp = timestamp;
            const dt = (timestamp - lastTimestamp) / 1000;
            lastTimestamp = timestamp;

            if (playing) {
                time += dt * speed;
                if (time >= simData.maxTurn) {
                    time = simData.maxTurn;
                    playing = false;
                }
                updateUI();
            }

            draw();
            requestAnimationFrame(render);
        }

        function draw() {
            const cw = container.clientWidth;
            const ch = container.clientHeight;
            ctx.clearRect(0, 0, cw, ch);
            
            const nr = Math.max(14, Math.min(26, scale * 0.38));
            const dr = Math.max(6, Math.min(10, nr / 3 + 2));

            // Edges
            ctx.lineCap = 'round';
            for (const edge of simData.edges) {
                const p1 = nodePos[edge.from];
                const p2 = nodePos[edge.to];
                if (!p1 || !p2) continue;
                
                ctx.beginPath();
                ctx.moveTo(p1.x, p1.y);
                ctx.lineTo(p2.x, p2.y);
                ctx.lineWidth = edge.blocked ? 1 : Math.max(1, Math.min(4, edge.cap));
                ctx.strokeStyle = edge.blocked ? COLORS.edgeBlocked : COLORS.edgeNormal;
                ctx.stroke();
            }

            // Nodes
            ctx.textAlign = 'center';
            ctx.textBaseline = 'top';
            ctx.font = '10px var(--font-mono)';
            
            for (const key in simData.nodes) {
                const n = simData.nodes[key];
                const p = nodePos[key];
                
                const fill = getFill(n.type, n.color);
                const border = getBorder(n.type, n.color);
                
                if (n.is_hub) {
                    const grd = ctx.createRadialGradient(p.x, p.y, nr, p.x, p.y, nr + 20);
                    grd.addColorStop(0, hexToRgba(border, 0.4));
                    grd.addColorStop(1, 'rgba(0,0,0,0)');
                    ctx.fillStyle = grd;
                    ctx.beginPath();
                    ctx.arc(p.x, p.y, nr + 20, 0, Math.PI * 2);
                    ctx.fill();
                }

                ctx.beginPath();
                ctx.arc(p.x, p.y, nr, 0, Math.PI * 2);
                ctx.fillStyle = fill;
                ctx.fill();
                ctx.lineWidth = n.is_hub ? 4 : 2;
                ctx.strokeStyle = border;
                ctx.stroke();

                if (n.type === 'BLOCKED') {
                    const d = nr - 5;
                    ctx.beginPath();
                    ctx.moveTo(p.x - d, p.y - d);
                    ctx.lineTo(p.x + d, p.y + d);
                    ctx.moveTo(p.x + d, p.y - d);
                    ctx.lineTo(p.x - d, p.y + d);
                    ctx.lineWidth = 2;
                    ctx.stroke();
                }

                ctx.fillStyle = COLORS.textDim;
                ctx.fillText(key, p.x, p.y + nr + 4);
            }

            // Drones
            const turnInt = Math.floor(time);
            
            // Clustering logic
            const atNode = {};
            const activeDrones = [];
            
            for (const [didStr, path] of Object.entries(simData.paths)) {
                const did = parseInt(didStr);
                let pos = getDronePos(path, time);
                let onNode = getDroneNodeInt(path, turnInt);
                
                activeDrones.push({ did, pos, onNode });
                if (onNode) {
                    if (!atNode[onNode]) atNode[onNode] = [];
                    atNode[onNode].push(did);
                }
            }
            
            ctx.font = '10px var(--font-sans)';
            ctx.textBaseline = 'middle';
            
            for (const d of activeDrones) {
                let px = d.pos.x;
                let py = d.pos.y;
                
                if (d.onNode && atNode[d.onNode]) {
                    const cluster = atNode[d.onNode];
                    const idx = cluster.indexOf(d.did);
                    const total = cluster.length;
                    
                    if (total > 1) {
                        const cols = Math.min(4, total);
                        const rows = Math.ceil(total / cols);
                        const row = Math.floor(idx / cols);
                        const col = idx % cols;
                        const spacing = Math.min(dr * 2 + 2, (nr * 2) / Math.max(cols, rows));
                        const dx = (col - (cols - 1) / 2) * spacing;
                        const dy = (row - (rows - 1) / 2) * spacing;
                        px += dx;
                        py += dy;
                    }
                }
                
                const color = getDroneColor(d.did);
                
                // Glow
                const grd = ctx.createRadialGradient(px, py, dr, px, py, dr + 10);
                grd.addColorStop(0, hexToRgba(COLORS.drones[(d.did-1)%COLORS.drones.length], 0.5));
                grd.addColorStop(1, 'rgba(0,0,0,0)');
                ctx.fillStyle = grd;
                ctx.beginPath();
                ctx.arc(px, py, dr + 10, 0, Math.PI * 2);
                ctx.fill();
                
                // Drone circle
                ctx.beginPath();
                ctx.arc(px, py, dr, 0, Math.PI * 2);
                ctx.fillStyle = color;
                ctx.fill();
                ctx.lineWidth = 1;
                ctx.strokeStyle = '#fff';
                ctx.stroke();
                
                // Number
                ctx.fillStyle = '#fff';
                ctx.fillText(d.did.toString(), px, py);
            }
        }

        function getDroneNodeInt(path, t) {
            for (let i = 0; i < path.length; i++) {
                if (path[i].t === t) return path[i].node;
            }
            return null;
        }

        function getDronePos(path, t) {
            if (t <= path[0].t) return nodePos[path[0].node];
            if (t >= path[path.length - 1].t) return nodePos[path[path.length - 1].node];
            
            for (let i = 1; i < path.length; i++) {
                const pt = path[i].t;
                const ppt = path[i - 1].t;
                if (ppt <= t && t <= pt) {
                    const frac = (t - ppt) / Math.max(pt - ppt, 1);
                    const p1 = nodePos[path[i - 1].node];
                    const p2 = nodePos[path[i].node];
                    return {
                        x: p1.x + (p2.x - p1.x) * frac,
                        y: p1.y + (p2.y - p1.y) * frac
                    };
                }
            }
            return nodePos[path[path.length - 1].node];
        }

        // --- CONTROLS ---
        btnPlay.onclick = () => {
            if (time >= simData.maxTurn) time = 0;
            playing = !playing;
            updateUI();
        };
        document.getElementById('btn-reset').onclick = () => { playing = false; time = 0; updateUI(); };
        document.getElementById('btn-step-back').onclick = () => { playing = false; time = Math.max(0, Math.floor(time) - 1); updateUI(); };
        document.getElementById('btn-step-fwd').onclick = () => { playing = false; time = Math.min(simData.maxTurn, Math.floor(time) + 1); updateUI(); };
        
        document.getElementById('btn-slower').onclick = () => { speed = Math.max(0.25, speed / 1.5); elSpeed.innerText = speed.toFixed(1) + 'x'; };
        document.getElementById('btn-faster').onclick = () => { speed = Math.min(16.0, speed * 1.5); elSpeed.innerText = speed.toFixed(1) + 'x'; };

        elTimeline.oninput = (e) => {
            playing = false;
            time = parseFloat(e.target.value);
            updateUI();
        };

        // Keyboard support
        window.addEventListener('keydown', (e) => {
            if (e.code === 'Space') { e.preventDefault(); btnPlay.click(); }
            else if (e.code === 'ArrowRight') document.getElementById('btn-step-fwd').click();
            else if (e.code === 'ArrowLeft') document.getElementById('btn-step-back').click();
            else if (e.key === 'r' || e.key === 'R') document.getElementById('btn-reset').click();
        });

        // INIT
        resize();
        updateUI();
        requestAnimationFrame(render);
    </script>
</body>
</html>
"""

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

        print(f"\\nVisualisation generated at: {path}")
        print("Opening in default browser...")

        # Open in default browser
        webbrowser.open(f"file://{path}")
