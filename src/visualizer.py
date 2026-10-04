"""Living Architecture Visualizer for Cartographer.
Compiles interactive Mermaid DAGs and standalone Atelier-styled SVG/HTML blueprints.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from .ast_scanner import ModuleNode
from .graph_engine import ArchitectureMetrics, CodebaseDependencyGraph


class LivingArchitectureVisualizer:
    """Renders codebase DAGs into Mermaid syntax and standalone interactive HTML blueprints."""

    def __init__(self, graph: CodebaseDependencyGraph, metrics: ArchitectureMetrics):
        self.graph = graph
        self.metrics = metrics

    def generate_mermaid(self) -> str:
        """Generate clean, categorized Mermaid.js flowchart."""
        lines = ["flowchart TD"]
        lines.append("    %% Architecture Dependency Graph by Cartographer")
        lines.append("    classDef stable fill:#1e293b,stroke:#38bdf8,stroke-width:2px,color:#f8fafc;")
        lines.append("    classDef volatile fill:#3b1e2b,stroke:#f43f5e,stroke-width:2px,color:#f8fafc;")
        lines.append("    classDef core fill:#0f172a,stroke:#a855f7,stroke-width:2px,color:#f8fafc;")

        # Node id sanitizer
        def sanitize_id(path_str: str) -> str:
            return path_str.replace("/", "_").replace("\\", "_").replace(".", "_").replace("-", "_")

        # Create nodes
        for path_str, node in self.graph.modules.items():
            node_id = sanitize_id(path_str)
            instability = self.metrics.instability_index.get(path_str, 0.0)
            loc = node.lines_of_code
            num_funcs = len(node.functions)
            num_classes = len(node.classes)

            label = f'"{Path(path_str).stem}<br/><small>LOC: {loc} | I: {instability}</small>"'
            lines.append(f"    {node_id}[{label}]")

            if instability > 0.7:
                lines.append(f"    class {node_id} volatile;")
            elif instability < 0.3 and loc > 50:
                lines.append(f"    class {node_id} core;")
            else:
                lines.append(f"    class {node_id} stable;")

        # Create edges
        for src, targets in self.graph.edges.items():
            src_id = sanitize_id(src)
            for tgt in targets:
                tgt_id = sanitize_id(tgt)
                lines.append(f"    {src_id} --> {tgt_id}")

        return "\n".join(lines)

    def generate_html_blueprint(self, title: str = "Cartographer Living Architecture") -> str:
        """Generate self-contained HTML living architecture viewer with Da Vinci blueprint aesthetic."""
        mermaid_code = self.generate_mermaid()

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        :root {{
            --bg-color: #090d16;
            --surface-color: #111827;
            --border-color: #1e293b;
            --accent-blue: #38bdf8;
            --accent-rose: #f43f5e;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
            --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background-color: var(--bg-color);
            color: var(--text-main);
            font-family: var(--font-sans);
            display: flex;
            flex-direction: column;
            min-height: 100vh;
        }}
        header {{
            background: rgba(17, 24, 39, 0.85);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border-color);
            padding: 1rem 2rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .brand {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}
        .brand h1 {{
            font-size: 1.15rem;
            font-weight: 600;
            letter-spacing: -0.02em;
        }}
        .badge {{
            font-family: var(--font-mono);
            font-size: 0.7rem;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            background: rgba(56, 189, 248, 0.15);
            color: var(--accent-blue);
            border: 1px solid rgba(56, 189, 248, 0.3);
        }}
        .metrics-bar {{
            display: flex;
            gap: 1.5rem;
        }}
        .metric-pill {{
            font-size: 0.8rem;
            color: var(--text-muted);
        }}
        .metric-pill strong {{
            color: var(--text-main);
            font-family: var(--font-mono);
        }}
        main {{
            flex: 1;
            padding: 2rem;
            overflow: auto;
            display: flex;
            justify-content: center;
            align-items: flex-start;
        }}
        .mermaid-container {{
            background: var(--surface-color);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 2rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            max-width: 100%;
        }}
    </style>
</head>
<body>
    <header>
        <div class="brand">
            <h1>🗺️ Cartographer</h1>
            <span class="badge">LIVING ARCHITECTURE</span>
        </div>
        <div class="metrics-bar">
            <span class="metric-pill">Modules: <strong>{self.metrics.total_modules}</strong></span>
            <span class="metric-pill">LOC: <strong>{self.metrics.total_lines_of_code}</strong></span>
            <span class="metric-pill">Classes: <strong>{self.metrics.total_classes}</strong></span>
            <span class="metric-pill">Functions: <strong>{self.metrics.total_functions}</strong></span>
            <span class="metric-pill">Cycles: <strong>{len(self.metrics.circular_dependencies)}</strong></span>
        </div>
    </header>
    <main>
        <div class="mermaid-container">
            <pre class="mermaid">
{mermaid_code}
            </pre>
        </div>
    </main>
    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'dark',
            securityLevel: 'loose',
            flowchart: {{
                curve: 'basis',
                nodeSpacing: 50,
                rankSpacing: 50
            }}
        }});
    </script>
</body>
</html>
"""
        return html
