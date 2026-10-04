"""Unit tests for Cartographer Inkloom Exporter."""

import json
import tempfile
from pathlib import Path
import pytest
from src.ast_scanner import CartographerScanner
from src.graph_engine import CodebaseDependencyGraph
from src.inkloom_exporter import InkloomExporter


def test_inkloom_export_schema_and_markdown():
    code_mod = """
class DataPipeline:
    '''Core pipeline class.'''
    def process(self, raw_data: str) -> bool:
        return True
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        (tmp_path / "pipeline.py").write_text(code_mod, encoding="utf-8")

        scanner = CartographerScanner(tmp_path)
        modules = scanner.scan_codebase()
        graph = CodebaseDependencyGraph(modules)
        metrics = graph.compute_metrics()

        exporter = InkloomExporter(graph, metrics, project_name="TestProject")
        spec = exporter.build_inkloom_spec()

        assert spec["schema_version"] == "inkloom.v1"
        assert spec["project_name"] == "TestProject"
        assert len(spec["modules"]) == 1
        assert spec["modules"][0]["classes"][0]["name"] == "DataPipeline"

        # Test writing JSON
        json_out = tmp_path / "inkloom_spec.json"
        exporter.export_to_json(json_out)
        assert json_out.exists()
        loaded = json.loads(json_out.read_text(encoding="utf-8"))
        assert loaded["project_name"] == "TestProject"

        # Test Markdown generation
        md_text = exporter.generate_markdown_docs()
        assert "TestProject" in md_text
        assert "DataPipeline" in md_text
