"""Dependency Graph & Architectural Rot Engine for Cartographer.
Builds directed dependency graphs, detects circular imports, and scores architectural stability.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from .ast_scanner import ModuleNode


@dataclass
class ArchitectureMetrics:
    total_modules: int
    total_classes: int
    total_functions: int
    total_lines_of_code: int
    circular_dependencies: List[List[str]]
    god_modules: List[str]
    orphan_modules: List[str]
    instability_index: Dict[str, float]  # Ce / (Ca + Ce)


class CodebaseDependencyGraph:
    """Directed dependency graph and topological architectural rot analyzer."""

    def __init__(self, modules: Dict[str, ModuleNode]):
        self.modules = modules
        self.edges: Dict[str, Set[str]] = defaultdict(set)  # outgoing: u -> v (u depends on v)
        self.reverse_edges: Dict[str, Set[str]] = defaultdict(set)  # incoming: v <- u (v is depended on by u)
        self._module_path_map: Dict[str, str] = {}  # "pkg.submod" -> "pkg/submod.py"

        self._build_path_map()
        self._build_graph()

    def _build_path_map(self):
        """Map Python dotted module names and file stems to relative file paths."""
        for file_path, node in self.modules.items():
            path_obj = Path(file_path)
            # Map bare filename without extension
            self._module_path_map[path_obj.stem] = file_path
            # Map dotted path: foo/bar/baz.py -> foo.bar.baz
            parts = list(path_obj.with_suffix("").parts)
            dotted = ".".join(parts)
            self._module_path_map[dotted] = file_path

    def _resolve_target(self, source_path: str, mod_name: str, is_relative: bool, level: int) -> Optional[str]:
        """Resolve an imported module name to a scanned project module path."""
        if not mod_name and not is_relative:
            return None

        if is_relative:
            src_parts = list(Path(source_path).parent.parts)
            if level > 1:
                src_parts = src_parts[: -(level - 1)]
            if mod_name:
                src_parts.extend(mod_name.split("."))
            target_dotted = ".".join(src_parts)
            if target_dotted in self._module_path_map:
                return self._module_path_map[target_dotted]

        if mod_name in self._module_path_map:
            return self._module_path_map[mod_name]

        # Check sub-tokens (e.g. from foo.bar import baz -> check foo.bar, then bar)
        parts = mod_name.split(".")
        for i in range(len(parts), 0, -1):
            sub = ".".join(parts[:i])
            if sub in self._module_path_map:
                return self._module_path_map[sub]

        return None

    def _build_graph(self):
        """Resolve import statements into directed edges."""
        for file_path, node in self.modules.items():
            for imp in node.imports:
                target_path = self._resolve_target(file_path, imp.module, imp.is_relative, imp.level)
                if target_path and target_path != file_path:
                    self.edges[file_path].add(target_path)
                    self.reverse_edges[target_path].add(file_path)

    def find_cycles(self) -> List[List[str]]:
        """Detect circular dependency cycles using DFS 3-color coloring."""
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {node: WHITE for node in self.modules}
        cycles: List[List[str]] = []
        path: List[str] = []

        def dfs(u: str):
            color[u] = GRAY
            path.append(u)

            for v in self.edges.get(u, set()):
                if v not in color:
                    continue
                if color[v] == GRAY:
                    # Cycle found
                    idx = path.index(v)
                    cycle = path[idx:] + [v]
                    cycles.append(cycle)
                elif color[v] == WHITE:
                    dfs(v)

            path.pop()
            color[u] = BLACK

        for node in self.modules:
            if color[node] == WHITE:
                dfs(node)

        # Deduplicate identical cycles with different rotations
        unique_cycles = []
        seen_sets = []
        for c in cycles:
            nodes_set = set(c[:-1])
            if nodes_set not in seen_sets:
                seen_sets.append(nodes_set)
                unique_cycles.append(c)

        return unique_cycles

    def compute_metrics(self) -> ArchitectureMetrics:
        """Calculate overall architectural health, rot, and stability indices."""
        total_loc = sum(n.lines_of_code for n in self.modules.values())
        total_classes = sum(len(n.classes) for n in self.modules.values())
        total_functions = sum(len(n.functions) for n in self.modules.values())

        cycles = self.find_cycles()
        god_modules: List[str] = []
        orphan_modules: List[str] = []
        instability: Dict[str, float] = {}

        for path, node in self.modules.items():
            ce = len(self.edges.get(path, set()))  # efferent (outgoing)
            ca = len(self.reverse_edges.get(path, set()))  # afferent (incoming)

            # Instability I = Ce / (Ca + Ce). 0 = maximally stable, 1 = maximally unstable
            if ca + ce > 0:
                instability[path] = round(ce / (ca + ce), 3)
            else:
                instability[path] = 0.0

            # God module check: high coupling or > 400 LOC
            if node.lines_of_code > 400 or (ce >= 8 and ca >= 5):
                god_modules.append(path)

            # Orphan check: 0 incoming, 0 outgoing (excluding __init__.py, cli.py, main.py)
            stem = Path(path).stem
            if ca == 0 and ce == 0 and stem not in ("__init__", "cli", "main", "__main__"):
                orphan_modules.append(path)

        return ArchitectureMetrics(
            total_modules=len(self.modules),
            total_classes=total_classes,
            total_functions=total_functions,
            total_lines_of_code=total_loc,
            circular_dependencies=cycles,
            god_modules=god_modules,
            orphan_modules=orphan_modules,
            instability_index=instability,
        )
