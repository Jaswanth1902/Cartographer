"""Inkloom AI Exporter for Cartographer.
Exports structured architecture schemas and living documentation compatible with Inkloom AI.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .ast_scanner import ModuleNode
from .graph_engine import ArchitectureMetrics, CodebaseDependencyGraph


class InkloomExporter:
    """Serializes codebase cartography into Inkloom AI specification format and Markdown docs."""

    def __init__(self, graph: CodebaseDependencyGraph, metrics: ArchitectureMetrics, project_name: str = "Project"):
        self.graph = graph
        self.metrics = metrics
        self.project_name = project_name

    def build_inkloom_spec(self) -> Dict[str, Any]:
        """Compile a structured JSON payload adhering to Inkloom AI's documentation ingestion schema."""
        modules_payload = []

        for path_str, node in self.graph.modules.items():
            outgoing = sorted(list(self.graph.edges.get(path_str, set())))
            incoming = sorted(list(self.graph.reverse_edges.get(path_str, set())))

            classes_data = [
                {
                    "name": cls.name,
                    "bases": cls.bases,
                    "docstring": cls.docstring or "",
                    "methods": [
                        {
                            "name": m.name,
                            "args": m.args,
                            "return_type": m.return_type,
                            "docstring": m.docstring or "",
                        }
                        for m in cls.methods
                    ],
                }
                for cls in node.classes
            ]

            functions_data = [
                {
                    "name": fn.name,
                    "args": fn.args,
                    "return_type": fn.return_type,
                    "docstring": fn.docstring or "",
                    "calls": fn.calls,
                }
                for fn in node.functions
            ]

            modules_payload.append(
                {
                    "file_path": path_str,
                    "module_name": node.module_name,
                    "docstring": node.docstring or "",
                    "lines_of_code": node.lines_of_code,
                    "dependencies": outgoing,
                    "dependents": incoming,
                    "instability": self.metrics.instability_index.get(path_str, 0.0),
                    "classes": classes_data,
                    "functions": functions_data,
                }
            )

        # Collect OpenAPI / HTTP endpoints for Inkloom integration
        endpoints_payload = []
        for path_str, node in self.graph.modules.items():
            for fn in node.functions:
                if getattr(fn, "http_endpoint", None):
                    endpoints_payload.append({
                        "file_path": path_str,
                        "handler": fn.name,
                        "method": fn.http_endpoint["method"],
                        "path": fn.http_endpoint["path"],
                        "decorator": fn.http_endpoint["decorator"],
                        "docstring": fn.docstring or ""
                    })
            for cls in node.classes:
                for m in cls.methods:
                    if getattr(m, "http_endpoint", None):
                        endpoints_payload.append({
                            "file_path": path_str,
                            "handler": f"{cls.name}.{m.name}",
                            "method": m.http_endpoint["method"],
                            "path": m.http_endpoint["path"],
                            "decorator": m.http_endpoint["decorator"],
                            "docstring": m.docstring or ""
                        })

        spec = {
            "schema_version": "inkloom.v1",
            "project_name": self.project_name,
            "metrics": {
                "total_modules": self.metrics.total_modules,
                "total_classes": self.metrics.total_classes,
                "total_functions": self.metrics.total_functions,
                "total_endpoints": len(endpoints_payload),
                "total_lines_of_code": self.metrics.total_lines_of_code,
                "circular_dependencies_count": len(self.metrics.circular_dependencies),
                "circular_cycles": self.metrics.circular_dependencies,
                "god_modules": self.metrics.god_modules,
                "orphan_modules": self.metrics.orphan_modules,
            },
            "api_endpoints": endpoints_payload,
            "modules": modules_payload,
        }
        return spec


    def export_to_json(self, output_path: str | Path) -> Path:
        """Write the Inkloom spec to a JSON file."""
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        spec = self.build_inkloom_spec()
        target.write_text(json.dumps(spec, indent=2), encoding="utf-8")
        return target

    def generate_markdown_docs(self) -> str:
        """Generate high-density Markdown documentation of the system architecture."""
        lines = [
            f"# 🧭 {self.project_name}: System Architecture & Component Catalog",
            "",
            "> **Generated by Cartographer** | *WCC Launchpad 3.0 x Inkloom AI Architecture Agent*",
            "",
            "## 1. Executive Metrics",
            f"- **Total Modules**: `{self.metrics.total_modules}`",
            f"- **Total Lines of Code**: `{self.metrics.total_lines_of_code}`",
            f"- **Classes Defined**: `{self.metrics.total_classes}`",
            f"- **Functions / Methods**: `{self.metrics.total_functions}`",
            f"- **Circular Import Rot**: `{'None detected (CLEAN)' if not self.metrics.circular_dependencies else f'{len(self.metrics.circular_dependencies)} cycles detected'}`",
            "",
            "## 2. Module Catalog & Dependency Surface",
            "| Module | LOC | Classes | Functions | Dependencies (Out) | Dependents (In) | Instability |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ]

        for path_str, node in sorted(self.graph.modules.items()):
            ce = len(self.graph.edges.get(path_str, set()))
            ca = len(self.graph.reverse_edges.get(path_str, set()))
            instability = self.metrics.instability_index.get(path_str, 0.0)
            lines.append(
                f"| `{path_str}` | {node.lines_of_code} | {len(node.classes)} | {len(node.functions)} | {ce} | {ca} | `{instability}` |"
            )

        if self.metrics.circular_dependencies:
            lines.extend([
                "",
                "## ⚠️ Circular Dependencies Detected",
            ])
            for i, cycle in enumerate(self.metrics.circular_dependencies, 1):
                cycle_str = " ➔ ".join([f"`{c}`" for c in cycle])
                lines.append(f"{i}. {cycle_str}")

        lines.extend([
            "",
            "## 3. Detailed Component Signatures",
        ])

        for path_str, node in sorted(self.graph.modules.items()):
            lines.append(f"### 📄 `{path_str}`")
            if node.docstring:
                lines.append(f"> {node.docstring.strip()}")
                lines.append("")

            if node.classes:
                lines.append("**Classes**:")
                for cls in node.classes:
                    bases_str = f"({', '.join(cls.bases)})" if cls.bases else ""
                    lines.append(f"- `class {cls.name}{bases_str}`: {cls.docstring or 'No docstring'}")
                    for m in cls.methods:
                        args_str = ", ".join(m.args)
                        ret_str = f" -> {m.return_type}" if m.return_type else ""
                        lines.append(f"  - `{m.name}({args_str}){ret_str}`")

            if node.functions:
                lines.append("**Functions**:")
                for fn in node.functions:
                    args_str = ", ".join(fn.args)
                    ret_str = f" -> {fn.return_type}" if fn.return_type else ""
                    lines.append(f"- `def {fn.name}({args_str}){ret_str}`: {fn.docstring or 'No docstring'}")

            lines.append("")

        return "\n".join(lines)
