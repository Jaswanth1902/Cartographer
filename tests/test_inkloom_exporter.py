"""Unit tests for Cartographer Inkloom AI Exporter."""

import json
import tempfile
from pathlib import Path
from src.ast_scanner import FunctionSignature, ImportStatement, ModuleNode
from src.graph_engine import CodebaseDependencyGraph
from src.inkloom_exporter import InkloomExporter


def test_inkloom_spec_generation_and_export():
    fn_health = FunctionSignature(
        name="health_check",
        args=[],
        return_type="dict",
        docstring="Health probe",
        line_start=10,
        line_end=15,
        decorators=["@app.get('/health')"],
        http_endpoint={"method": "GET", "path": "/health", "handler": "health_check", "decorator": "@app.get('/health')"},
    )

    mod = ModuleNode(
        file_path="src/api.py",
        module_name="api",
        docstring="API module",
        imports=[],
        classes=[],
        functions=[fn_health],
        lines_of_code=20,
    )

    modules = {"src/api.py": mod}
    graph = CodebaseDependencyGraph(modules)
    metrics = graph.compute_metrics()

    exporter = InkloomExporter(graph, metrics, project_name="TestProject")
    spec = exporter.build_inkloom_spec()

    assert spec["schema_version"] == "inkloom.v1"
    assert spec["project_name"] == "TestProject"
    assert len(spec["api_endpoints"]) == 1
    assert spec["api_endpoints"][0]["method"] == "GET"
    assert spec["api_endpoints"][0]["path"] == "/health"
    assert spec["metrics"]["total_endpoints"] == 1

    with tempfile.TemporaryDirectory() as tmpdir:
        json_file = Path(tmpdir) / "spec.json"
        exporter.export_to_json(json_file)

        assert json_file.exists()
        loaded = json.loads(json_file.read_text(encoding="utf-8"))
        assert loaded["schema_version"] == "inkloom.v1"
        assert loaded["api_endpoints"][0]["path"] == "/health"


def test_inkloom_markdown_generation():
    mod = ModuleNode(
        file_path="src/util.py",
        module_name="util",
        docstring="Utility helpers",
        imports=[],
        classes=[],
        functions=[],
        lines_of_code=15,
    )

    graph = CodebaseDependencyGraph({"src/util.py": mod})
    metrics = graph.compute_metrics()
    exporter = InkloomExporter(graph, metrics, project_name="TestDoc")

    md = exporter.generate_markdown_docs()
    assert "# 🧭 TestDoc: System Architecture & Component Catalog" in md
    assert "src/util.py" in md
    assert "Utility helpers" in md
