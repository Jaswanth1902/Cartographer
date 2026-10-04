"""Unit tests for Cartographer AST Scanner."""

import tempfile
from pathlib import Path
import pytest
from src.ast_scanner import CartographerScanner


def test_scanner_extracts_classes_and_functions():
    sample_code = '''
"""Sample module docstring."""

import os
from sys import path

class BaseService:
    """Base service class."""
    def run(self, flag: bool) -> int:
        return 1

def compute_total(a: int, b: int) -> int:
    """Compute total of two numbers."""
    return a + b
'''
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        test_file = tmp_path / "sample.py"
        test_file.write_text(sample_code, encoding="utf-8")

        scanner = CartographerScanner(tmp_path)
        node = scanner.scan_file(test_file)

        assert node.module_name == "sample"
        assert node.docstring == "Sample module docstring."
        assert len(node.imports) == 2
        assert len(node.classes) == 1
        assert node.classes[0].name == "BaseService"
        assert len(node.classes[0].methods) == 1
        assert node.classes[0].methods[0].name == "run"
        assert len(node.functions) == 1
        assert node.functions[0].name == "compute_total"
        assert node.functions[0].return_type == "int"


def test_scanner_extracts_fastapi_and_flask_route_decorators():
    sample_api = '''
from fastapi import FastAPI, APIRouter

app = FastAPI()
router = APIRouter()

@app.get("/api/v1/health")
def health_check():
    """Health probe endpoint."""
    return {"status": "ok"}

@router.post("/api/v1/scan")
async def trigger_scan(payload: dict):
    """Trigger AST scan endpoint."""
    return {"accepted": True}
'''
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        api_file = tmp_path / "api.py"
        api_file.write_text(sample_api, encoding="utf-8")

        scanner = CartographerScanner(tmp_path)
        node = scanner.scan_file(api_file)

        endpoints = [fn.http_endpoint for fn in node.functions if fn.http_endpoint]
        assert len(endpoints) == 2

        get_ep = next(e for e in endpoints if e["method"] == "GET")
        assert get_ep["path"] == "/api/v1/health"
        assert get_ep["handler"] == "health_check"

        post_ep = next(e for e in endpoints if e["method"] == "POST")
        assert post_ep["path"] == "/api/v1/scan"
        assert post_ep["handler"] == "trigger_scan"


def test_scanner_handles_syntax_errors_gracefully():
    broken_code = '''
def broken_syntax(
    print("missing closing paren")
'''
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        bad_file = tmp_path / "broken.py"
        bad_file.write_text(broken_code, encoding="utf-8")

        scanner = CartographerScanner(tmp_path)
        node = scanner.scan_file(bad_file)

        assert node.module_name == "broken"
        assert node.parse_error is not None
        assert "was never closed" in node.parse_error

