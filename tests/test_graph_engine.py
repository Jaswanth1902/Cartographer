"""Unit tests for Cartographer Graph Engine and Cycle Detection."""

import tempfile
from pathlib import Path
import pytest
from src.ast_scanner import CartographerScanner
from src.graph_engine import CodebaseDependencyGraph


def test_dependency_resolution_and_cycle_detection():
    # Create module A that imports B, and B that imports A (circular dependency)
    code_a = """
import b
def func_a():
    return b.func_b()
"""
    code_b = """
import a
def func_b():
    return a.func_a()
"""
    code_c = """
# Independent module
def standalone():
    return 42
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        (tmp_path / "a.py").write_text(code_a, encoding="utf-8")
        (tmp_path / "b.py").write_text(code_b, encoding="utf-8")
        (tmp_path / "c.py").write_text(code_c, encoding="utf-8")

        scanner = CartographerScanner(tmp_path)
        modules = scanner.scan_codebase()
        graph = CodebaseDependencyGraph(modules)
        metrics = graph.compute_metrics()

        assert metrics.total_modules == 3
        # Should detect circular dependency between a.py and b.py
        assert len(metrics.circular_dependencies) >= 1
        cycle = metrics.circular_dependencies[0]
        assert "a.py" in cycle and "b.py" in cycle
        # c.py should be marked as orphan since it has 0 in and 0 out
        assert "c.py" in metrics.orphan_modules
