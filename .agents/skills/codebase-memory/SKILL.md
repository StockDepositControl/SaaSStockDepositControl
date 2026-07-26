---
name: codebase-memory
description: Enforces the mandatory usage of the Codebase Memory MCP tool for codebase exploration, symbol search, graph querying, and architectural analysis to optimize performance and reduce token consumption.
---

# Codebase Memory MCP Guidelines

## Overview
This skill provides mandatory behavioral rules for agents to interact with the codebase using the `codebase-memory` MCP server tools. Agents MUST prioritize these tools over standard file system listing (`list_dir`) and multi-file reads (`view_file`) during initial exploration, symbol discovery, and architectural analysis.

---

## Directives & Execution Rules

### 1. Mandatory Tool Usage Strategy
When responding to requests that involve understanding codebase structure, finding symbols, analyzing dependencies, or locating specific logic:
- **Do NOT** recursively list directories using `list_dir`.
- **Do NOT** read full files speculatively using `view_file` just to see if a symbol or import exists.
- **ALWAYS** check the status of the repository index first using `index_status` or index the repository via `index_repository` if required.
- **ALWAYS** perform targeted code and graph queries using the `codebase-memory` MCP tools.

### 2. Available MCP Tools & When to Use Them

| Operation / Need | Required Codebase Memory Tool | Prohibited Fallback |
| :--- | :--- | :--- |
| Check index state | `index_status` | Direct file system guessing |
| Index repository | `index_repository` | Reading files one by one |
| Search code/symbols | `search_code` | Recursive `grep_search` or manual `view_file` |
| Trace graph/dependencies | `query_graph` / `trace_path` | Manual import tracing across multiple files |
| Overview architecture | `get_architecture` | Multiple `list_dir` calls across folder hierarchies |
| Retrieve specific snippets | `get_code_snippet` | Full file `view_file` reads when only a snippet is needed |

### 3. Default Parameters & Protocol
- **Default Project Parameter**: Always pass `project: "backend"` (or `"./backend"`) in all MCP tool calls (`search_code`, `index_status`, `query_graph`, `get_architecture`, `get_code_snippet`).
- **Index Initialization**: If `index_status` returns not indexed, immediately execute `index_repository(repo_path: "./backend", mode: "full")`.
- **Token Efficiency**: Prefer `search_code` (with `project: "backend"`) and `get_code_snippet` to retrieve only relevant code snippets.
- **Editing Strategy**: Reserve `view_file` **only** for when preparing to edit a specific file identified via Codebase Memory.

---

## Workflow Checklist

1. **Step 1: Check Index Status**
   Call `index_status(project: "backend")`. If not indexed, call `index_repository(repo_path: "./backend", mode: "full")`.
2. **Step 2: Perform Semantic / Graph Queries**
   Use `get_architecture(project: "backend")`, `search_code(project: "backend", pattern: "...")`, or `query_graph(project: "backend", ...)` to locate relevant classes, methods, endpoints, or modules.
3. **Step 3: Targeted Retrieval**
   Use `get_code_snippet(project: "backend", ...)` to inspect implementation details with minimal token overhead.
4. **Step 4: Execute Code Modifications**
   Only open the specific target files with `view_file` or edit tools when preparing to write/replace code.
