"""Integration tests for Cartographer CLI commands."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock
from src.cli import cmd_scan, cmd_lint, cmd_docgen, cmd_visualize, cmd_export


def test_cli_scan_command():
    args = MagicMock()
    args.path = "src"
    code = cmd_scan(args)
    assert code == 0


def test_cli_lint_command():
    args = MagicMock()
    args.path = "src"
    code = cmd_lint(args)
    assert code == 0


def test_cli_docgen_command():
    args = MagicMock()
    args.path = "src"
    args.diff = False
    code = cmd_docgen(args)
    assert code == 0


def test_cli_docgen_with_diff_output():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        (tmp_path / "mod.py").write_text("def f(x):\n    return x\n", encoding="utf-8")
        args = MagicMock()
        args.path = str(tmp_path)
        args.diff = True

        code = cmd_docgen(args)
        assert code == 0
        diff_file = tmp_path / ".cartographer" / "docstring_patches.diff"
        assert diff_file.exists()
        assert "Synthesizes behavior for f" in diff_file.read_text(encoding="utf-8")



def test_cli_visualize_command():
    with tempfile.TemporaryDirectory() as tmpdir:
        out_html = Path(tmpdir) / "blueprint.html"
        args = MagicMock()
        args.path = "src"
        args.output = str(out_html)

        code = cmd_visualize(args)
        assert code == 0
        assert out_html.exists()
        content = out_html.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content


def test_cli_export_command():
    with tempfile.TemporaryDirectory() as tmpdir:
        json_file = Path(tmpdir) / "spec.json"
        md_file = Path(tmpdir) / "docs.md"
        args = MagicMock()
        args.path = "src"
        args.json = str(json_file)
        args.markdown = str(md_file)

        code = cmd_export(args)
        assert code == 0
        assert json_file.exists()
        assert md_file.exists()


def test_root_cli_map_flag():
    import cartographer
    args = MagicMock()
    args.map = "src"
    args.path = "src"
    args.format = "mermaid"
    code = cartographer.handle_direct_flags(args)
    assert code == 0


def test_root_cli_audit_flag():
    import cartographer
    args = MagicMock()
    args.map = None
    args.path = "src"
    args.audit = True
    args.depth = 3
    code = cartographer.handle_direct_flags(args)
    assert code == 0
