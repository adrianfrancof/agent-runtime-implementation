# Agent Runtime Platform

An executable Python foundation for the harness, bounded loops, and graph patterns
described in the [technical blueprint](docs/BLUEPRINT.md). The source documents
are in the parent directory: `harness_loop_graph.md` and
`agent-engineering-handbook.md`.

**This is a prototype, not a production-ready platform.** It is intentionally
limited to one process and an in-memory approval graph. Do not expose it to
untrusted networks or sensitive workloads. See the blueprint for target
architecture and production gates.

## What works

- An async, bounded agent runtime with an offline deterministic model, optional
  OpenAI adapter, explicit tool registry, allowlist authorization and trace events.
- Five bounded control-loop implementations, an in-process graph runner with
  approval, rejection, and execution limits, and eight role/message contracts.
- A namespace-scoped, in-memory lexical memory implementation.
- Compositions for evidence-supplied research, scraping, a two-role research
  team, approval, and memory-backed question answering.
- A FastAPI endpoint for executing a run and a demonstration approval workflow.
- An experimental, separately installed Playwright text scraper with an explicit
  hostname allowlist. It is not registered or exposed by the API.
- Offline tests and a local demonstration.

The demo model **does not browse, research, reason, or validate facts**. The
reference compositions are building blocks, not production applications:
research requires supplied evidence, the scraper requires an explicitly
provided adapter, and the team exchanges in-process messages. LangGraph
orchestration, durable memory and workflow persistence, MCP, PostgreSQL, Redis,
Qdrant, Kubernetes, observability exporters, RBAC, per-tenant isolation and
cost accounting remain design targets rather than implemented features.

## Run locally

With Python 3.13, from this directory in PowerShell:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe examples\local_demo.py
$env:ARP_API_KEY = 'replace-with-a-long-random-local-key'
.\.venv\Scripts\python.exe -m uvicorn arp.api.app:app --host 127.0.0.1 --port 8000
```

In another PowerShell window:

```powershell
$headers = @{ 'X-API-Key' = 'replace-with-a-long-random-local-key' }
Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8000/runs' -Headers $headers -ContentType 'application/json' -Body '{"goal":"Demonstrate the runtime"}'
$run = Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8000/approval-runs' -Headers $headers -ContentType 'application/json' -Body '{"goal":"Review a proposal"}'
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/approval-runs/$($run.id)/decision" -Headers $headers -ContentType 'application/json' -Body '{"approved":true}'
```

For the optional OpenAI adapter set `OPENAI_API_KEY` and `ARP_OPENAI_MODEL` in
the process environment. This sends the goal, permitted tool descriptions, and
observations to OpenAI; do not enable it for sensitive data without appropriate
authorization and provider agreements. The adapter has not been validated
against a live service. With no model configured the API uses the offline demo.

Optional browser development: install `.[browser]`, then run
`.\.venv\Scripts\python.exe -m playwright install chromium`. Use
`make_browser_tool(frozenset({"example.com"}))` only in a separately isolated
environment. Application URL checks do not prevent DNS rebinding, private
resolution, browser exploits, WebSocket traffic, or all network side effects.
Enforce DNS and egress policy outside the process. Do not use this prototype to
bypass site access controls or anti-automation measures.

## HTTP behavior and limitations

`GET /health` is an unauthenticated liveness check. All other endpoints require
`X-API-Key`; requests fail closed if `ARP_API_KEY` is unset. `POST /runs`
returns completed or failed run records, including model/tool errors. `POST
/approval-runs` pauses a graph; `POST /approval-runs/{id}/decision` accepts
`{"approved": true}` or `false`. Approval state is process-local, lost on
restart, and incompatible with multiple workers or replicas. The shared API key
does not identify users, provide distinct approval authority, or support
revocation and auditing. API errors and events can contain sensitive data.
TLS termination, secret management, authorization, quotas, persistence,
redaction, concurrency controls and production-grade monitoring are required
before deployment.

## Layout

- `src/arp/runtime`: run model, model providers, bounded execution.
- `src/arp/tools`: registry, authorization boundary and experimental browser.
- `src/arp/loops`: five reusable bounded loop primitives.
- `src/arp/graphs`: graph runner and approval example.
- `src/arp/memory`: local memory interface and adapter.
- `src/arp/agents`: role and inter-agent message types.
- `src/arp/workflows`: five reference compositions using the runtime interfaces.
- `src/arp/security`: tool permission policy.
- `src/arp/api`: FastAPI endpoints.
- `src/arp/observability`: integration boundary; no exporters installed.
- `tests`, `examples`, `infrastructure/docker`, `docs`: validation, runnable
  example, development image, and architecture documentation.

The Dockerfile is a development image, not a hardened deployment. Build it from
the project root with `docker build -f infrastructure/docker/Dockerfile -t arp .`;
provide `ARP_API_KEY` securely at runtime and restrict network access.
