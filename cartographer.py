#!/usr/bin/env python3
"""Cartographer: Zero-Drift Living Architecture & AST Graph CLI.

Can be run directly as:
    python cartographer.py --map . --format mermaid
    python cartographer.py --audit --depth 3
Or with subcommands:
    python cartographer.py scan .
    python cartographer.py lint .
    python cartographer.py docgen . --diff
    python cartographer.py visualize . -o docs/blueprint.html
    python cartographer.py export . -j .inkloom/spec.json -m docs/ARCHITECTURE.md
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add repo root to sys.path
repo_root = Path(__file__).resolve().parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.cli import (
    cmd_docgen,
    cmd_export,
    cmd_lint,
    cmd_scan,
    cmd_visualize,
    run_pipeline,
)
from src.visualizer import LivingArchitectureVisualizer


def handle_direct_flags(args) -> int:
    """Handle top-level flags like --map and --audit."""
    target_path = Path(args.map or args.path or ".").resolve()

    if args.map:
        scanner, graph, metrics, elapsed_ms = run_pipeline(target_path)
        fmt = (args.format or "mermaid").lower()

        if fmt == "mermaid":
            viz = LivingArchitectureVisualizer(graph, metrics)
            print(viz.generate_mermaid())
            return 0
        elif fmt == "html":
            viz = LivingArchitectureVisualizer(graph, metrics)
            out_file = target_path / "docs" / "architecture_blueprint.html"
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_text(viz.generate_html_blueprint(), encoding="utf-8")
            print(f"[VIZ] Living HTML blueprint written to {out_file} ({elapsed_ms:.2f} ms)")
            return 0
        elif fmt == "json":
            from src.inkloom_exporter import InkloomExporter

            exporter = InkloomExporter(graph, metrics)
            spec = exporter.generate_inkloom_spec()
            import json

            print(json.dumps(spec, indent=2))
            return 0
        else:
            print(f"[ERROR] Unsupported format: {fmt}. Use 'mermaid', 'html', or 'json'.", file=sys.stderr)
            return 1

    if args.audit:
        scanner, graph, metrics, elapsed_ms = run_pipeline(target_path)
        print(f"[AUDIT] Cartographer AST Dependency Audit for {target_path.name}")
        print(f"[PERF] Scanned {metrics.total_modules} modules ({metrics.total_lines_of_code} LOC) in {elapsed_ms:.2f} ms\n")

        print("--- Architectural Quality Checks ---")
        has_issues = False
        if metrics.circular_dependencies:
            print(f"[FAIL] {len(metrics.circular_dependencies)} Circular import cycle(s) detected via Tarjan SCC:")
            for cycle in metrics.circular_dependencies:
                print("   " + " -> ".join(cycle))
            has_issues = True
        else:
            print("[PASS] Zero circular dependencies detected (Tarjan SCC verified).")

        if metrics.god_modules:
            print(f"[WARN] {len(metrics.god_modules)} God Modules (>400 LOC or excessive coupling):")
            for gm in metrics.god_modules:
                print(f"   - {gm}")
        else:
            print("[PASS] Zero God modules detected.")

        if metrics.orphan_modules:
            print(f"[INFO] {len(metrics.orphan_modules)} Isolated / Leaf modules:")
            for om in metrics.orphan_modules[: args.depth if args.depth else 5]:
                print(f"   - {om}")

        print("\n--- Module Instability Index (Martin Metric) ---")
        sorted_instability = sorted(metrics.instability_index.items(), key=lambda x: x[1], reverse=True)
        limit = args.depth if args.depth else 5
        for mod, inst in sorted_instability[:limit]:
            status = "Volatile" if inst > 0.7 else "Stable" if inst < 0.3 else "Balanced"
            print(f"   {mod[:40]:<40} I={inst:.2f} [{status}]")

        return 1 if has_issues else 0

    return 0


def main():
    # If called with subcommands, delegate or route
    subcommands = {"scan", "lint", "docgen", "visualize", "export"}

    # Check if first arg is a known subcommand
    if len(sys.argv) > 1 and sys.argv[1] in subcommands:
        from src.cli import main as cli_main
        sys.exit(cli_main())

    parser = argparse.ArgumentParser(
        description="Cartographer: Zero-Drift Living Architecture & AST Graph CLI"
    )
    parser.add_argument("--map", "-m", metavar="PATH", nargs="?", const=".", help="Generate architecture graph for repository")
    parser.add_argument("--format", "-f", default="mermaid", choices=["mermaid", "html", "json"], help="Output format for --map (mermaid, html, json)")
    parser.add_argument("--audit", "-a", action="store_true", help="Audit circular dependencies and Martin stability metrics")
    parser.add_argument("--depth", "-d", type=int, default=5, help="Display depth for audit output")
    parser.add_argument("path", nargs="?", default=".", help="Path to codebase")

    args, unknown = parser.parse_known_args()

    if args.map or args.audit:
        sys.exit(handle_direct_flags(args))

    # If no flags passed, show help or default scan
    if len(sys.argv) == 1:
        parser.print_help()
        print("\nAvailable Subcommands: scan, lint, docgen, visualize, export")
        sys.exit(0)

    # Fallback to src.cli
    from src.cli import main as cli_main
    sys.exit(cli_main())


if __name__ == "__main__":
    main()
