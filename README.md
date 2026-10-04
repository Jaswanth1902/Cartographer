<div align="center">

# 🗺️ Cartographer
### Zero-Drift Living Architecture & AST Graph CLI

[![CLI](https://img.shields.io/badge/CLI-Python%203.10%2B-blue?style=flat-square)](https://github.com/Jaswanth1902/Cartographer)
[![Diagrams](https://img.shields.io/badge/Output-Mermaid.js%20%26%20Reladraw-purple?style=flat-square)]()
[![Latency](https://img.shields.io/badge/Map%20Time-<100ms-brightgreen?style=flat-square)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)

**Stop letting architecture documentation drift into irrelevance.**  
Cartographer generates real-time Mermaid sequence diagrams, symbol coordinate maps, and circular dependency audits directly from source code AST in milliseconds.

[🚀 Quickstart](#quickstart) • [✨ Features](#features) • [📊 Example Outputs](#examples)

</div>

---

### 🚀 Quickstart

```bash
pip install -r requirements.txt

# Generate live Mermaid architecture graph for current repository
python cartographer.py --map . --format mermaid

# Audit circular dependencies
python cartographer.py --audit --depth 3
```
