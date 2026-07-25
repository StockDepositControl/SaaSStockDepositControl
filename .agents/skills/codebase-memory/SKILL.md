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
| Check index state | `mcp_codebase-memory_index_status` | Direct file system guessing |
| Index repository | `mcp_codebase-memory_index_repository` | Reading files one by one |
| Search code/symbols | `mcp_codebase-memory_search_code` | Recursive `grep_search` or manual `view_file` |
| Trace graph/dependencies | `mcp_codebase-memory_query_graph` / `trace_path` | Manual import tracing across multiple files |
| Overview architecture | `mcp_codebase-memory_get_architecture` | Multiple `list_dir` calls across folder hierarchies |
| Retrieve specific snippets | `mcp_codebase-memory_get_code_snippet` | Full file `view_file` reads when only a snippet is needed |

### 3. Token Efficiency Protocol
- Prefer `search_code` and `get_code_snippet` to retrieve only the relevant portion of code needed for the task.
- Reserve `view_file` **only** for when precise file modifications (editing) are required, or when inspecting exhaustive full-file contents after locating the exact target via `codebase-memory`.

---

## Workflow Checklist

1. **Step 1: Check Index Status**
   Call `index_status`. If not indexed, call `index_repository`.
2. **Step 2: Perform Semantic / Graph Queries**
   Use `get_architecture`, `search_code`, or `query_graph` to locate relevant classes, methods, endpoints, or modules.
3. **Step 3: Targeted Retrieval**
   Use `get_code_snippet` to inspect implementation details with minimal token overhead.
4. **Step 4: Execute Code Modifications**
   Only open the specific target files with `view_file` or edit tools when preparing to write/replace code.
