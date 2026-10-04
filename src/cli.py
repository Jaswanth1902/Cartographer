"""Command-Line Interface for Cartographer.
Provides scan, lint, visualize, and export commands.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from .ast_scanner import CartographerScanner
from .graph_engine import CodebaseDependencyGraph
from .inkloom_exporter import InkloomExporter
from .visualizer import LivingArchitectureVisualizer


if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def run_pipeline(root_path: Path):
    """Run scanner and graph engine, return (scanner, graph, metrics)."""
    start_time = time.perf_counter()
    scanner = CartographerScanner(root_path)
    modules = scanner.scan_codebase()
    graph = CodebaseDependencyGraph(modules)
    metrics = graph.compute_metrics()
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    return scanner, graph, metrics, elapsed_ms


def cmd_scan(args):
    root = Path(args.path).resolve()
    print(f"[SCAN] Cartographer: Scanning codebase at {root}...")
    scanner, graph, metrics, elapsed_ms = run_pipeline(root)

    print(f"[PERF] Scan completed in {elapsed_ms:.2f} ms")
    print(f"  Modules Scanned : {metrics.total_modules}")
    print(f"  Lines of Code   : {metrics.total_lines_of_code}")
    print(f"  Classes         : {metrics.total_classes}")
    print(f"  Functions       : {metrics.total_functions}")
    print(f"  Circular Cycles : {len(metrics.circular_dependencies)}")
    print(f"  God Modules     : {len(metrics.god_modules)}")
    print(f"  Orphan Modules  : {len(metrics.orphan_modules)}")

    if metrics.circular_dependencies:
        print("\n[ALERT] CIRCULAR DEPENDENCY CYCLES:")
        for cycle in metrics.circular_dependencies:
            print("   " + " -> ".join(cycle))

    return 0


def cmd_lint(args):
    root = Path(args.path).resolve()
    print(f"[LINT] Cartographer: Checking architectural invariants at {root}...")
    _, _, metrics, elapsed_ms = run_pipeline(root)

    has_errors = False
    if metrics.circular_dependencies:
        print(f"[FAIL] {len(metrics.circular_dependencies)} circular dependency cycles detected!")
        for cycle in metrics.circular_dependencies:
            print("   " + " -> ".join(cycle))
        has_errors = True

    if metrics.god_modules:
        print(f"[WARN] {len(metrics.god_modules)} God Modules (>400 LOC or high coupling):")
        for gm in metrics.god_modules:
            print(f"   - {gm}")

    if not has_errors:
        print(f"[PASS] Architecture is clean (0 circular cycles) in {elapsed_ms:.2f} ms.")
        return 0
    else:
        return 1


def cmd_visualize(args):
    root = Path(args.path).resolve()
    out_file = Path(args.output).resolve()
    scanner, graph, metrics, elapsed_ms = run_pipeline(root)

    visualizer = LivingArchitectureVisualizer(graph, metrics)
    html_content = visualizer.generate_html_blueprint(title=f"{root.name} - Living Architecture")

    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(html_content, encoding="utf-8")
    print(f"[VIZ] Living Architecture Blueprint generated at {out_file} ({elapsed_ms:.2f} ms)")
    return 0


def cmd_export(args):
    root = Path(args.path).resolve()
    scanner, graph, metrics, elapsed_ms = run_pipeline(root)

    exporter = InkloomExporter(graph, metrics, project_name=root.name)

    if args.json:
        json_path = Path(args.json).resolve()
        exporter.export_to_json(json_path)
        print(f"[EXPORT] Inkloom AI JSON spec exported to {json_path}")

    if args.markdown:
        md_path = Path(args.markdown).resolve()
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_text = exporter.generate_markdown_docs()
        md_path.write_text(md_text, encoding="utf-8")
        print(f"[EXPORT] Living Architecture Markdown exported to {md_path}")

    print(f"[EXPORT] Completed in {elapsed_ms:.2f} ms")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Cartographer - Living Architecture & Docs Agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # scan
    p_scan = subparsers.add_parser("scan", help="Scan codebase and print summary metrics")
    p_scan.add_argument("path", nargs="?", default=".", help="Codebase directory to scan")
    p_scan.set_defaults(func=cmd_scan)

    # lint
    p_lint = subparsers.add_parser("lint", help="Verify architectural integrity and flag cycles")
    p_lint.add_argument("path", nargs="?", default=".", help="Codebase directory to lint")
    p_lint.set_defaults(func=cmd_lint)

    # visualize
    p_vis = subparsers.add_parser("visualize", help="Generate interactive HTML/SVG living blueprint")
    p_vis.add_argument("path", nargs="?", default=".", help="Codebase directory to visualize")
    p_vis.add_argument("--output", "-o", default="architecture_blueprint.html", help="Output HTML file path")
    p_vis.set_defaults(func=cmd_visualize)

    # export
    p_exp = subparsers.add_parser("export", help="Export Inkloom AI JSON specification and Markdown docs")
    p_exp.add_argument("path", nargs="?", default=".", help="Codebase directory to export")
    p_exp.add_argument("--json", "-j", help="Output Inkloom JSON spec file")
    p_exp.add_argument("--markdown", "-m", help="Output Markdown architecture doc file")
    p_exp.set_defaults(func=cmd_export)

    args = parser.parse_args()
    exit_code = args.func(args)
    sys.exit(exit_code or 0)


if __name__ == "__main__":
    main()
