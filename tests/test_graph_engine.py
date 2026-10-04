"""Unit tests for Cartographer Dependency Graph Engine and Tarjan SCC."""

from src.ast_scanner import ImportStatement, ModuleNode
from src.graph_engine import CodebaseDependencyGraph


def test_tarjan_scc_finds_cycles():
    # Construct 3 modules with a circular loop: a -> b -> c -> a
    mod_a = ModuleNode(
        file_path="src/a.py",
        module_name="a",
        docstring=None,
        imports=[ImportStatement(module="b", names=["b"], is_relative=True, level=1)],
        classes=[],
        functions=[],
        lines_of_code=10,
    )
    mod_b = ModuleNode(
        file_path="src/b.py",
        module_name="b",
        docstring=None,
        imports=[ImportStatement(module="c", names=["c"], is_relative=True, level=1)],
        classes=[],
        functions=[],
        lines_of_code=10,
    )
    mod_c = ModuleNode(
        file_path="src/c.py",
        module_name="c",
        docstring=None,
        imports=[ImportStatement(module="a", names=["a"], is_relative=True, level=1)],
        classes=[],
        functions=[],
        lines_of_code=10,
    )

    modules = {"src/a.py": mod_a, "src/b.py": mod_b, "src/c.py": mod_c}
    graph = CodebaseDependencyGraph(modules)
    cycles = graph.find_cycles()

    assert len(cycles) == 1
    cycle_nodes = set(cycles[0])
    assert "src/a.py" in cycle_nodes
    assert "src/b.py" in cycle_nodes
    assert "src/c.py" in cycle_nodes


def test_tarjan_scc_on_acyclic_graph():
    # Construct clean unidirectional DAG: a -> b -> c (no cycles)
    mod_a = ModuleNode(
        file_path="src/a.py",
        module_name="a",
        docstring=None,
        imports=[ImportStatement(module="b", names=["b"], is_relative=True, level=1)],
        classes=[],
        functions=[],
        lines_of_code=10,
    )
    mod_b = ModuleNode(
        file_path="src/b.py",
        module_name="b",
        docstring=None,
        imports=[ImportStatement(module="c", names=["c"], is_relative=True, level=1)],
        classes=[],
        functions=[],
        lines_of_code=10,
    )
    mod_c = ModuleNode(
        file_path="src/c.py",
        module_name="c",
        docstring=None,
        imports=[],
        classes=[],
        functions=[],
        lines_of_code=10,
    )

    modules = {"src/a.py": mod_a, "src/b.py": mod_b, "src/c.py": mod_c}
    graph = CodebaseDependencyGraph(modules)
    cycles = graph.find_cycles()

    assert len(cycles) == 0


def test_martin_instability_and_metrics():
    # Module with 1 outgoing, 0 incoming: I = 1.0 (maximally unstable)
    # Module with 0 outgoing, 1 incoming: I = 0.0 (maximally stable)
    mod_entry = ModuleNode(
        file_path="src/main.py",
        module_name="main",
        docstring=None,
        imports=[ImportStatement(module="core", names=["core"], is_relative=True, level=1)],
        classes=[],
        functions=[],
        lines_of_code=25,
    )
    mod_core = ModuleNode(
        file_path="src/core.py",
        module_name="core",
        docstring=None,
        imports=[],
        classes=[],
        functions=[],
        lines_of_code=50,
    )

    modules = {"src/main.py": mod_entry, "src/core.py": mod_core}
    graph = CodebaseDependencyGraph(modules)
    metrics = graph.compute_metrics()

    assert metrics.total_modules == 2
    assert metrics.total_lines_of_code == 75
    assert metrics.instability_index["src/main.py"] == 1.0
    assert metrics.instability_index["src/core.py"] == 0.0
