# Agent Runtime Implementation Workspace

This workspace contains the **Agent Runtime Platform (ARP)** reference project,
its architecture blueprint, and the source material used to shape that design.
The project directory is named `agent-runtime-platform` (with hyphens); there is
no separate `agent_runtime_platform` directory.

## What this project is for

ARP is a Python reference implementation for building bounded, observable agent
systems. It demonstrates the foundations that surround a model:

- **Harness:** controls which model and tools are available, what permissions
  apply, and how runs are bounded and recorded.
- **Loops:** provide bounded reasoning, reflection, validation, planning, and
  learning patterns.
- **Graphs:** make workflow stages and transitions explicit, including a
  human-approval pause and resume.

The goal is to give engineers a runnable starting point and a detailed target
architecture—not to claim the full enterprise platform is already implemented.
The current code is a prototype. Durable orchestration and memory, full
multi-tenant identity and authorization, MCP, LangGraph integration, and
production observability and deployment controls remain design targets.
Review the project [README](./agent-runtime-platform/README.md) for implemented
capabilities, setup instructions, and limitations.

## What is in this workspace

### `agent-runtime-platform/`

The executable Python project:

- `src/arp/runtime/` — run models, model adapters, and bounded execution.
- `src/arp/tools/` — tool registry, permission boundary, and experimental
  Playwright scraper.
- `src/arp/loops/` — reusable bounded control-loop implementations.
- `src/arp/graphs/` — graph runner and approval-workflow example.
- `src/arp/memory/` — memory interface and ephemeral local adapter.
- `src/arp/agents/` — agent roles and collaboration-message contracts.
- `src/arp/workflows/` — reference workflow compositions.
- `src/arp/security/` — tool authorization policy.
- `src/arp/api/` — FastAPI endpoints for agent runs and approval workflows.
- `src/arp/observability/` — integration boundary; exporters are not
  implemented.
- `tests/` — tests for runtime behavior, loops, graphs, API, memory, browser
  URL policy, and workflow compositions.
- `examples/local_demo.py` — runnable runtime and approval demonstration.
- `infrastructure/docker/` — development Dockerfile, not a hardened production
  deployment.
- `docs/BLUEPRINT.md` [BLUEPRINT](./agent-runtime-platform/docs/BLUEPRINT.md) — the proposed system architecture and engineering
  requirements.
- `pyproject.toml` — package metadata and Python dependencies.

### Source material

- [`harness_loop_graph.md`](./harness_loop_graph.md) — structured article about
  harness, loop, and graph engineering.
- [`agent-engineering-handbook.md`](./agent-engineering-handbook.md) — source
  handbook material informing the architecture.

The source documents provide background. The blueprint converts their themes
into an implementation-oriented design, while the Python project implements
only the subset described as currently working in its README.

## Start the project

From PowerShell:

```powershell
Set-Location .\agent-runtime-platform
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe examples\local_demo.py
```

See the [project README](./agent-runtime-platform/README.md) for starting the
API, using the optional model adapter, and important security limitations.
