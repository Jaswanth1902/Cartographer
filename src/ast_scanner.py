"""AST Scanner for Cartographer.
Extracts module metadata, imports, classes, functions, and docstrings in <50ms.
"""

from __future__ import annotations

import ast
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set


@dataclass
class FunctionSignature:
    name: str
    args: List[str]
    return_type: Optional[str]
    docstring: Optional[str]
    line_start: int
    line_end: int
    calls: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    http_endpoint: Optional[Dict[str, str]] = None



@dataclass
class ClassSignature:
    name: str
    bases: List[str]
    docstring: Optional[str]
    methods: List[FunctionSignature] = field(default_factory=list)
    line_start: int = 1
    line_end: int = 1


@dataclass
class ImportStatement:
    module: str
    names: List[str] = field(default_factory=list)
    is_relative: bool = False
    level: int = 0


@dataclass
class ModuleNode:
    file_path: str
    module_name: str
    docstring: Optional[str] = None
    imports: List[ImportStatement] = field(default_factory=list)
    classes: List[ClassSignature] = field(default_factory=list)
    functions: List[FunctionSignature] = field(default_factory=list)
    lines_of_code: int = 0
    parse_error: Optional[str] = None


class CallVisitor(ast.NodeVisitor):
    def __init__(self):
        self.calls = []

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            self.calls.append(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            self.calls.append(node.func.attr)
        self.generic_visit(node)


class CartographerScanner:
    """Deterministic, zero-token AST scanner for Python codebases."""

    def __init__(self, root_dir: str | Path):
        self.root_dir = Path(root_dir).resolve()

    def scan_file(self, file_path: Path) -> ModuleNode:
        """Parse a single Python file into a ModuleNode."""
        rel_path = file_path.relative_to(self.root_dir).as_posix()
        module_name = file_path.stem

        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            lines_of_code = len(content.splitlines())
            tree = ast.parse(content, filename=str(file_path))
        except Exception as e:
            return ModuleNode(
                file_path=rel_path,
                module_name=module_name,
                parse_error=str(e),
            )

        module_doc = ast.get_docstring(tree)
        imports: List[ImportStatement] = []
        classes: List[ClassSignature] = []
        functions: List[FunctionSignature] = []

        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(ImportStatement(module=alias.name, names=[alias.asname or alias.name]))
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                names = [a.name for a in node.names]
                imports.append(
                    ImportStatement(
                        module=mod,
                        names=names,
                        is_relative=(node.level > 0),
                        level=node.level,
                    )
                )
            elif isinstance(node, ast.ClassDef):
                bases = []
                for b in node.bases:
                    if isinstance(b, ast.Name):
                        bases.append(b.id)
                    elif isinstance(b, ast.Attribute):
                        bases.append(f"{ast.unparse(b.value)}.{b.attr}")
                    else:
                        bases.append("...")

                methods: List[FunctionSignature] = []
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        methods.append(self._parse_function(item))

                classes.append(
                    ClassSignature(
                        name=node.name,
                        bases=bases,
                        docstring=ast.get_docstring(node),
                        methods=methods,
                        line_start=node.lineno,
                        line_end=getattr(node, "end_lineno", node.lineno),
                    )
                )
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(self._parse_function(node))

        return ModuleNode(
            file_path=rel_path,
            module_name=module_name,
            docstring=module_doc,
            imports=imports,
            classes=classes,
            functions=functions,
            lines_of_code=lines_of_code,
        )

    def _parse_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> FunctionSignature:
        args = [arg.arg for arg in node.args.args]
        ret_type = ast.unparse(node.returns) if node.returns else None
        doc = ast.get_docstring(node)

        visitor = CallVisitor()
        visitor.visit(node)

        decorators = []
        http_endpoint = None
        for dec in node.decorator_list:
            dec_str = ast.unparse(dec)
            decorators.append(dec_str)
            # Parse FastAPI / Flask route decorators: @app.get("/items"), @router.post("/items")
            if isinstance(dec, ast.Call):
                func_name = ast.unparse(dec.func)
                for method in ["get", "post", "put", "delete", "patch", "options", "head"]:
                    if func_name.endswith(f".{method}") or func_name == method:
                        route_path = ast.unparse(dec.args[0]).strip("'\"") if dec.args else "/unknown"
                        http_endpoint = {
                            "method": method.upper(),
                            "path": route_path,
                            "handler": node.name,
                            "decorator": dec_str,
                        }
                        break

        return FunctionSignature(
            name=node.name,
            args=args,
            return_type=ret_type,
            docstring=doc,
            line_start=node.lineno,
            line_end=getattr(node, "end_lineno", node.lineno),
            calls=visitor.calls,
            decorators=decorators,
            http_endpoint=http_endpoint,
        )


    def scan_codebase(self, exclude_dirs: Optional[Set[str]] = None) -> Dict[str, ModuleNode]:
        """Recursively scan codebase for all .py files."""
        if exclude_dirs is None:
            exclude_dirs = {".git", ".cache", "__pycache__", "venv", ".venv", "node_modules", "dist", "build"}

        modules: Dict[str, ModuleNode] = {}
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for file in files:
                if file.endswith(".py"):
                    full_path = Path(root) / file
                    node = self.scan_file(full_path)
                    modules[node.file_path] = node

        return modules
