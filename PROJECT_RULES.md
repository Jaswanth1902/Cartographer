# Project Rules: Cartographer (Living Architecture & Docs Agent)

## Mission & Architecture
`Cartographer` is an autonomous codebase intelligence and architecture cartography agent built for **WCC Launchpad 3.0** (WeCodeCoders x Inkloom AI). It performs deterministic AST parsing of codebases in <50ms without cloud tokens, detects architectural rot (circular dependencies, god-modules, dead components), generates living Da Vinci/Mermaid DAGs, and compiles Inkloom-compatible documentation portals.

## Technical Constraints & Invariants
1. **Zero External Heavyweight SAST Dependencies**: Rely strictly on Python standard library (`ast`, `pathlib`, `typing`, `json`, `dataclasses`, `collections`) for core parsing. Zero heavy frameworks.
2. **Sub-50ms Parsing Budget**: Individual module AST extraction must execute in under 15ms; full codebase dependency DAGs in under 50ms.
3. **Inkloom AI Schema Compatibility**: Exporter must produce valid Inkloom-aligned documentation schema (`.inkloom/architecture_spec.json`) and OpenAPI endpoint mappings.
4. **Deterministic Exit Codes**:
   - `0`: Scan clean, zero circular dependencies, zero fatal architectural rot.
   - `1`: Architectural rot or circular imports detected during `lint` mode.
5. **Windows Subprocess Visibility (Law 8)**: Any CLI invocation via subprocess MUST pass `creationflags=0x08000000` (`CREATE_NO_WINDOW`).
