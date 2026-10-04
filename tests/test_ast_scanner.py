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
