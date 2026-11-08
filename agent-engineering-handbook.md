# Engineering Reliable AI Agents: Harnesses, Loops, and Graphs

## Abstract

Agent engineering is the design and operation of software systems in which a language model or other learned policy selects actions that are executed through tools in an external environment. A production agent is therefore not a model call alone: its behavior depends on the runtime, tool interfaces, state, policies, control flow, and evidence used to judge completion. Harness engineering, loop engineering, and graph engineering are useful complementary lenses for these responsibilities. Harness engineering defines the agent's operating environment and enforceable boundaries; loop engineering defines repeated action, feedback, retry, and termination; graph engineering defines the stages, data contracts, routing, joins, and approval gates of a task. They are often conflated because the same implementation can contain all three, and because frameworks use overlapping terminology. The distinction matters because a prompt cannot repair a missing permission boundary, an unbounded retry policy, or a workflow with invalid dependencies. This guide develops the three lenses into a systems-oriented design and operational method.

## Executive Summary

An AI agent is best treated as a software system whose model is one decision-making component. Start by specifying a task contract, allowed actions, independent success evidence, resource budgets, and a human escalation path. Build a harness that exposes only necessary context and capabilities, validates tool inputs, records events, and persists recoverable state. Add a bounded verification loop when the task can improve from objective feedback. Introduce a graph only when the work has distinct stages, conditional routes, useful parallel branches, durable pauses, or different trust boundaries.

The central engineering rule is to place each responsibility at the narrowest reliable layer: deterministic code for policy, validation, state transitions, and side-effect control; models for semantic interpretation and judgment where the model adds value; humans for decisions whose consequences or ambiguity exceed the system's authority. Measure task success, safety, latency, cost, retries, and human corrections across representative evaluations. More autonomy and more agents are not proxies for quality.

## Background

### From prompt engineering to agent systems

A prompt specifies model-visible instructions and context. Prompt quality remains important, but modern applications increasingly allow a model to call tools, observe results, and choose subsequent actions. Once model output can cause external effects, the application must engineer more than text: it must decide what data and tools are available, what happens after an action, how state survives interruption, and which evidence permits completion.

A useful evolution of concerns is:

1. **Prompt engineering:** shape a single model request and its response.
2. **Context and workflow engineering:** supply task-specific information and compose fixed model/tool stages.
3. **Agent engineering:** let a model choose among actions within a bounded runtime, observing tool results between decisions.
4. **Autonomous-system engineering:** operate agents over longer periods with persistence, budgets, policy enforcement, recovery, monitoring, and human oversight.
5. **Multi-agent architecture:** coordinate multiple model-driven or deterministic workers, including their interfaces, state ownership, failure isolation, and join rules.

These are not mutually exclusive historical eras. A production application may still use a carefully engineered prompt inside a deterministic workflow, while a long-running autonomous process may use fixed workflow stages around one agent loop.

### Workflow versus agent

A **workflow** executes a mostly predefined path through model calls and tools. An **agentic system** permits a model to choose some actions or direct part of its execution dynamically. Real systems are hybrids: an application may fix the outer workflow while allowing an agent to choose tools within one node. The choice is a control-allocation decision, not a binary product category. Fixed paths are easier to inspect and reproduce; model-directed paths are useful when the required steps cannot be fully specified in advance.

### Three engineering lenses

The terms harness, loop, and graph are used here as an operational taxonomy, not as a universal standards-body classification:

- **Harness:** the capabilities, context, policies, state, infrastructure, and measurement surrounding an agent run.
- **Loop:** the temporal cycle in which an agent acts, receives evidence, retries or stops.
- **Graph:** the task structure describing stages, state, transitions, routes, joins, and gates.

They nest: a harness hosts a graph; graph nodes can contain loops; and the harness enforces policies over both. A single hook may participate in more than one layer, so classify by responsibility rather than by file or framework name.

## Agent Engineering Foundation

A useful systems model is:

```text
Agent system = Model + Runtime + Environment + Control layer
```

This is a conceptual decomposition, not an equation asserting independent components. The **model** proposes interpretations, plans, outputs, or actions. The **runtime** drives model requests, parses structured outputs, dispatches tools, and handles provider-specific behavior. The **environment** includes tools, data, services, filesystem, browser, and other state the model can observe or change. The **control layer** applies policies, budgets, routing, validation, persistence, and approval requirements.

### Logical layers

- **Reasoning layer:** interprets the task and chooses a next step. Do not equate hidden model reasoning with an auditable plan; expose only the structured decision evidence the application needs.
- **Execution layer:** performs model calls and invokes tools. Tool execution must be deterministic where feasible, typed, bounded, and independently authorized.
- **Memory layer:** carries relevant context within a run and across runs. Conversation history, durable workflow state, retrieved knowledge, and learned preferences have distinct lifetimes and trust levels.
- **Orchestration layer:** sequences tasks, handles branches and parallel work, controls retries, and pauses for humans or external events.
- **Observability layer:** records model requests, tool calls, state transitions, policy decisions, timings, token usage, outcomes, and failures with correlation identifiers.

A run should have a task contract with a goal, input provenance, constraints, allowed actions, expected output, objective checks, budget, and escalation policy. Completion should be an application decision based on evidence, not merely a model's assertion.

## Section 1: Agent Harness Engineering

### Definition

The **agent harness** is the runtime and surrounding infrastructure that supplies context and capabilities to an agent, executes its proposed actions, maintains state, constrains authority, and records evidence. In a narrow usage, harness can mean only the loop runner. This guide uses the broader systems meaning and names the model-execution loop separately.

### Purpose

The harness converts an unconstrained model interface into a bounded application component. It establishes what the agent can observe and do; makes tools understandable and predictable; prevents unauthorized effects; limits resource consumption; and provides the evidence needed to debug, resume, and evaluate runs.

### Architecture

```text
                           +----------------------+
 User / event ----------> | Request normalizer   |
                           | contract + identity  |
                           +----------+-----------+
                                      |
                                      v
+-----------------+       +----------+-----------+       +------------------+
| Durable state   |<----->| Agent runtime        |<----->| Model provider   |
| checkpoints     |       | context + loop       |       | model API        |
+-----------------+       +----+-------------+---+       +------------------+
                               |             ^
                    proposed call             | bounded result
                               v             |
                         +-----+-------------+-----+
                         | Policy / middleware      |
                         | schema, auth, budget,    |
                         | approval, redaction      |
                         +-----+-------------+-----+
                               |             ^
                               v             |
                    +----------+--+     +----+----------------+
                    | Tool gateway |     | Evidence / verifier|
                    | APIs, MCP,   |     | tests, rules, judge |
                    | browser      |     +---------------------+
                    +-------------+

            All components emit correlated, access-controlled traces
```

The diagram is logical. A tool gateway, state store, verifier, and agent runtime may be separate services or libraries. The security boundary must be enforced by trusted code and infrastructure, not by the model's prompt.

### Components

#### System prompts and task context

Prompts define role, task constraints, tool semantics, and output expectations. Keep stable policy separate from per-request data. Treat retrieved documents, issue text, webpages, tool outputs, and user input as untrusted data; do not promote them into privileged instruction channels. Use schemas and application validation for machine-consumed outputs. A prompt is a behavioral aid, not an authorization mechanism.

#### Tool interfaces

A tool is an application capability exposed through a narrow contract: name, purpose, typed arguments, result schema, errors, side-effect class, timeout, and authorization context. Prefer one action per tool and domain-specific names over generic shell-like interfaces. Validate arguments and object ownership in application code. Return concise, useful results and stable error codes; cap large outputs or provide paginated references.

#### MCP connections

The Model Context Protocol standardizes client-server discovery and invocation patterns for tools and resources. Treat each server as an integration and trust boundary: inventory its capabilities, authenticate it, constrain available tools, validate responses, set timeouts, and control data egress. Protocol support does not make a server trustworthy or its output safe. Avoid exposing broad credentials to a server or passing a tenant's data across trust boundaries without explicit policy.

#### Browser automation

Browser tools act on a mutable, often adversarial environment. Use isolated browser profiles, least-privilege accounts, domain and navigation policies, download restrictions, and explicit approval for consequential submissions. Prefer semantic locators and application APIs when available, while retaining visual checks for workflows whose behavior depends on rendering. Record relevant URLs and action results without unnecessarily capturing sensitive page contents.

#### API access

Place API calls behind application-owned clients or gateways that enforce identity, tenant scope, rate limits, schema validation, timeouts, retries, and idempotency. Give an agent a business operation such as `get_order_status` rather than arbitrary network access. Separate read and write authority, and require stronger checks for irreversible actions.

#### Memory and persistence

Memory is not one database. Distinguish:

- **Working context:** information needed in the current model request.
- **Conversation history:** messages or events needed to continue interaction.
- **Run state:** typed workflow values such as current stage, attempts, and verification results.
- **Long-term knowledge:** curated or retrieved information across tasks.
- **Audit record:** append-only evidence of what occurred.

Each needs an owner, retention policy, access policy, provenance, and deletion strategy. Do not treat generated summaries as authoritative records. Persist facts and decisions with sources and timestamps; retrieve the minimum relevant subset.

#### Checkpointing

A checkpoint is a recoverable snapshot of run state at a defined boundary. It should include a schema version, run ID, current node, state version, pending work, and references to outputs. Resume logic must validate checkpoint compatibility and re-check external preconditions. Checkpoints do not make side effects transactional: use idempotency keys, deduplication, or transactional outboxes for operations that can be repeated after a crash.

#### Permissions and safety controls

Enforce authorization outside the model. Derive permissions from authenticated principal, task contract, tenant, and policy. Apply deny-by-default tool allowlists, path/domain scopes, filesystem and network isolation, secret redaction, output filtering, and human approvals. Separate untrusted-content processing from privileged actions where possible. Logging must not leak secrets or regulated data. A safety classifier can supplement policy but should not be the only enforcement layer.

#### Middleware

Middleware wraps model and tool boundaries to implement cross-cutting behavior: input normalization, policy checks, output validation, retries, rate limits, telemetry, content filtering, and approval pauses. Keep middleware composable and observable. Define ordering explicitly; for example, authorization should precede tool execution, while result redaction should precede exposure to the model or user.

#### Logging and tracing

Use structured events and distributed trace spans. At minimum capture run and parent IDs, tenant/principal identifiers (pseudonymized where possible), model/provider/version, prompt or policy version, node, tool name, redacted arguments, result status, latency, retries, token/cost estimates, approval decisions, and final outcome. Keep raw transcripts under stricter controls than aggregate metrics. Traces are diagnostic records, not automatically safe training data.

#### Cost controls

Bound model turns, tool calls, output tokens, wall-clock time, concurrency, retries, and per-run spend. Enforce budgets in the runtime and tool gateway. Record cost per successful task, not just cost per invocation. Use caching only when cache keys encode all result-relevant inputs and privacy boundaries; use cheaper models for well-bounded low-risk tasks only after evaluation demonstrates acceptable quality.

### Responsibilities

The harness owns the available capabilities, context assembly, identity propagation, policy enforcement, resource controls, persistence integration, and evidence collection. It should expose explicit extension points without allowing an agent to silently widen its own authority. It does not own every workflow decision: graph routing and loop termination may live in orchestration code, while the harness supplies their runtime and gates.

### Benefits

- Makes behavior repeatable enough to test and operate.
- Limits damage from incorrect or manipulated model decisions.
- Reduces context waste through targeted retrieval and concise tools.
- Supports crash recovery, trace-based debugging, and policy audits.
- Lets application teams evolve models without rewriting all business controls.

### Limitations

- A harness cannot make a weak model or inadequate evaluation reliable by itself.
- Abstractions can hide provider behavior, prompt construction, retries, and state transitions.
- More middleware increases latency and creates configuration interactions.
- Persistent memory can retain incorrect, stale, sensitive, or cross-tenant information.
- Sandboxes and tool policies reduce risk but do not prove safety.

### Common failures

| Symptom                                         | Likely harness defect                                | First diagnostic                                               |
| ----------------------------------------------- | ---------------------------------------------------- | -------------------------------------------------------------- |
| Agent edits or reads unrelated resources        | Broad tool permissions or ambiguous task context     | Inspect tool inventory, identity scope, and call arguments     |
| Correct action is unavailable                   | Missing tool capability or poor interface contract   | Reproduce with the exact context and inspect tool discovery    |
| Important decisions disappear after restart     | Only conversation state was retained                 | Compare durable run state and audit events before/after resume |
| Model context is dominated by logs or documents | Unbounded tool output or eager context injection     | Measure per-call tokens and inspect tool result sizes          |
| Works locally but not in deployment             | Environment, credentials, or dependency drift        | Compare runtime configuration and tool health checks           |
| Sensitive data appears in a trace or prompt     | Weak redaction, access control, or data minimization | Trace data lineage and enforce redaction before persistence    |

### Production best practices

1. Define a typed task contract, explicit completion evidence, and ownership for each state field.
2. Make permissions principal-aware and default-deny; keep model instructions separate from policy enforcement.
3. Isolate execution, limit network egress, and use short-lived scoped credentials.
4. Validate tool inputs and outputs, sanitize model-visible errors, and cap results.
5. Use idempotency keys and deduplication for external side effects; design resume as at-least-once unless stronger semantics are proven.
6. Persist state and audit events separately; encrypt data, enforce retention, and version schemas.
7. Set independent turn, time, token, concurrency, and financial budgets.
8. Instrument before increasing autonomy; maintain representative offline evaluations and production outcome metrics.
9. Red-team prompt injection and cross-tenant access in controlled test environments.
10. Re-evaluate harness assumptions after model, tool, or policy upgrades; remove components only when regression tests support removal.

### Example implementations

These snippets illustrate harness-level configuration surfaces, not complete production systems. Pin dependency versions and consult current framework documentation before deployment.

#### Python: explicit tool boundary

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Principal:
    tenant_id: str
    can_refund: bool


def get_invoice(principal: Principal, invoice_id: str) -> dict:
    invoice = invoice_store.get(invoice_id)
    if invoice is None or invoice.tenant_id != principal.tenant_id:
        raise PermissionError("invoice_not_available")
    return {"id": invoice.id, "status": invoice.status, "total": invoice.total}


def issue_refund(principal: Principal, invoice_id: str, amount: int, key: str) -> dict:
    if not principal.can_refund:
        raise PermissionError("refund_not_authorized")
    return payment_service.refund(
        tenant_id=principal.tenant_id,
        invoice_id=invoice_id,
        amount_minor_units=amount,
        idempotency_key=key,
    )
```

The trusted application supplies `Principal`; the model cannot choose its tenant or grant itself refund authority. Production code also validates currency, limits amounts, authenticates the principal, and audits authorization outcomes.

#### LangChain: minimal agent harness

```python
from langchain.agents import create_agent


def lookup_status(order_id: str) -> str:
    """Return the caller-authorized status for one order."""
    return order_service.status_for_current_principal(order_id)

agent = create_agent(
    model="openai:gpt-5.5",
    tools=[lookup_status],
    system_prompt="Answer from tool evidence. Do not infer access to other accounts.",
)
```

`create_agent` supplies an agent loop and middleware extension points. The tool must still derive and enforce identity from trusted request context; prompt text is not access control.

#### OpenAI Agents SDK: tools and run loop

```python
import asyncio
from agents import Agent, Runner, function_tool


@function_tool
def lookup_status(order_id: str) -> str:
    """Return an authorized order status."""
    return order_service.status_for_current_principal(order_id)

agent = Agent(
    name="Order support",
    instructions="Use the order tool for status. Do not claim an action succeeded without its result.",
    tools=[lookup_status],
)

async def main() -> None:
    result = await Runner.run(agent, "Check order A-1042")
    print(result.final_output)

asyncio.run(main())
```

The SDK runs the tool-using loop and provides agent handoffs, sessions/state options, guardrails, and tracing surfaces. The application remains responsible for authorization, persistence choice, approvals, and its business workflow.

#### CrewAI: role/task harness

```python
from crewai import Agent, Crew, Process, Task

researcher = Agent(
    role="Policy researcher",
    goal="Find evidence relevant to the requested policy question",
    backstory="You distinguish sourced facts from uncertainty.",
    tools=[authorized_search_tool],
    allow_delegation=False,
    max_iter=5,
)

research_task = Task(
    description="Research the question using only the supplied organization scope.",
    expected_output="A short finding with source identifiers and unresolved questions.",
    agent=researcher,
)

crew = Crew(agents=[researcher], tasks=[research_task], process=Process.sequential)
result = crew.kickoff(inputs={"question": "..."})
```

CrewAI provides agent/task/crew abstractions and Flow orchestration. Tool access, data scope, output checks, budgets, and checkpoint behavior still need application-level configuration.

#### PydanticAI: typed output and dependency injection

```python
from dataclasses import dataclass
from typing import Protocol
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext

class Principal(Protocol):
    tenant_id: str

class CaseService(Protocol):
    async def search(self, principal: Principal, query: str) -> list[dict[str, str]]: ...

@dataclass
class SupportContext:
    principal: Principal
    case_service: CaseService

class CaseAnswer(BaseModel):
    answer: str
    source_ids: list[str]

agent = Agent(
    "openai:gpt-5.5",
    deps_type=SupportContext,
    output_type=CaseAnswer,
    instructions="Use authorized evidence; return source identifiers for factual claims.",
)

@agent.tool
async def search_cases(ctx: RunContext[SupportContext], query: str) -> list[dict]:
    return await ctx.deps.case_service.search(ctx.deps.principal, query)
```

The service and principal types are application-specific. PydanticAI's typed dependencies, tools, structured output, usage limits, and run inspection help make contracts explicit; they do not replace service authorization.

## Section 2: Loop Engineering

### Definition

A **loop** is the temporal control mechanism that repeatedly lets an agent or workflow act, observes the resulting evidence, and decides whether to continue, revise, escalate, or stop. Frameworks often provide an inner model-tool loop; application engineering adds task-level verification and termination policy around it.

### Purpose and core concept

A practical control cycle is:

```text
Observe -> Think -> Act -> Verify -> Reflect -> Retry / Route / Stop
```

“Think” and “reflect” describe decision operations, not independently verifiable system states. Observe supplies the latest environment state; think selects a candidate action; act invokes a permitted capability; verify compares the result with independent criteria; reflect summarizes what the evidence implies for the next attempt; retry is conditional on policy, budget, and progress. For reliable operation, use observable outputs such as tool results, test reports, policy decisions, evaluation scores, or human feedback. Do not require hidden reasoning traces to establish correctness.

A loop contract specifies:

- **Trigger:** event that begins an iteration.
- **Goal:** measurable desired state.
- **State:** data carried between iterations.
- **Action policy:** allowed operations and budget.
- **Evidence:** how progress and correctness are assessed.
- **Feedback:** actionable result returned to the next decision.
- **Stop rule:** success, budget exhaustion, stall, cancellation, or escalation.

### Feedback, validation, self-correction, evaluator, and critic loops

- **Feedback loop:** any repeated action informed by a new observation.
- **Validation loop:** deterministic checks such as tests, schema validation, static analysis, or business invariants.
- **Self-correction loop:** an agent incorporates observed errors and proposes a revision. It is not independent validation because the actor may preserve its own blind spots.
- **Evaluator loop:** a separate evaluator scores an output against a rubric or contract and provides bounded feedback. Calibrate evaluators against human judgments and retain hard programmatic gates.
- **Critic loop:** a role or agent proposes specific objections. A critic is a sensor, not proof; a critic that can edit the artifact or define success creates correlated failure risk.

### State-machine representation

```text
             +-----------------+
             | READY           |
             +--------+--------+
                      | trigger
                      v
             +--------+--------+
             | EXECUTE         |<----------------+
             +--------+--------+                 |
                      | action result            | bounded retry
                      v                          |
             +--------+--------+       +---------+---------+
             | VERIFY          |------>| REVISE / RETRY    |
             +---+----------+--+       +-------------------+
                 | pass     | fail budget/stall
                 v          v
             +---+--+   +---+-----------+
             | DONE |   | ESCALATE      |
             +------+   +---------------+
```

All states should have explicit failure and cancellation behavior. Persist before crossing a non-idempotent external effect or pausing for a human. On resume, revalidate preconditions and deduplicate effects.

### Reliability patterns

- **Bounded retries:** cap attempts and distinguish transient transport failures from semantic failures.
- **Exponential backoff with jitter:** for retryable service errors; honor provider `Retry-After` and total deadline.
- **Idempotency:** attach a stable operation key to side effects; do not retry an uncertain payment, message, or deployment blindly.
- **Circuit breaking and bulkheads:** stop calling unhealthy dependencies and isolate concurrency by tenant or service.
- **All-checks verification:** run independent required checks and aggregate all outcomes; do not let the first failed parallel branch hide others.
- **Stall detection:** stop if a progress measure does not improve over a defined window, such as no reduction in failing tests across two iterations.
- **Cancellation propagation:** propagate user cancellation, timeouts, and shutdown through child calls; clean up while recording partial state.
- **Dead-letter and escalation:** preserve the input, failed stage, and evidence for a human or later retry rather than silently dropping work.

### Error recovery

Classify errors before retrying:

1. **Transient infrastructure error:** retry within deadline and rate limit.
2. **Invalid model/tool output:** return a concise schema error; allow a small validation retry budget.
3. **Business-rule denial:** do not retry as though it were transient; route to explanation or approval.
4. **Stale precondition/conflict:** refresh authoritative state and replan.
5. **Unknown side-effect outcome:** query by idempotency key or external reference before deciding whether to repeat.
6. **Budget, safety, or permission failure:** terminate or escalate; never automatically increase authority or budget.

### Cost optimization and early exits

Track per-stage token usage, tool cost, wall-clock time, retries, and success. Stop immediately when a deterministic success predicate is met, when the request is invalid, when a mandatory policy gate fails, or when the budget is exhausted. For model evaluations, set a threshold and a maximum number of rounds. Use cheaper models or fewer evaluator calls only after measuring impact on end-to-end success and safety. Prevent retries from multiplying across SDK, HTTP client, job queue, and application layers; assign one owner for each retry class.

### Verification strategies

Use layered evidence, ordered by strength and relevance:

1. Structural checks: schema, required fields, allowed enum values, size limits.
2. Deterministic invariants: database constraints, business rules, static analysis.
3. Execution checks: tests, builds, API probes, browser flows, replayed transactions.
4. Semantic evaluation: rubric-based model judge or human rating with evidence.
5. Outcome checks: observed task state in the source-of-truth system.

A green tool invocation does not imply the task is correct. Verify the intended end state and independently confirm that the relevant evidence corresponds to the current run and artifact version.

### Production examples

- **Coding agent:** edit source, run focused test and full required checks, inspect actual diff, reject out-of-contract changes, route failures back to implementation, stop on a bounded attempt or stall threshold.
- **Customer operations:** read-only investigation can proceed automatically; refunds or account changes require principal-scoped tools and policy-based approval; confirm the operation from the authoritative ledger.
- **Research agent:** gather sources, deduplicate findings, and stop after a defined number of dry rounds; retain provenance and report unresolved claims rather than fabricating completeness.

### Pseudocode

```text
function run_task(contract, state):
    assert validate_contract(contract)
    state = load_or_initialize(contract.run_id)

    while state.attempts < contract.max_attempts:
        if cancelled() or deadline_exceeded() or budget_exceeded(state):
            return persist_and_escalate(state, reason="limit")

        proposal = agent_decide(contract, minimal_context(state))
        decision = policy.authorize(proposal, principal, contract)
        if not decision.allowed:
            return persist_and_stop(state, reason=decision.reason)

        result = execute_with_timeout_and_idempotency(proposal)
        evidence = verify(contract, result, authoritative_state())
        state = persist(advance(state, proposal, result, evidence))

        if evidence.success:
            return state.result
        if no_progress(state.progress_history, window=2):
            return persist_and_escalate(state, reason="stall")

        state.feedback = actionable_summary(evidence)
        state.attempts += 1

    return persist_and_escalate(state, reason="attempt_budget")
```

## Section 3: Graph Engineering

### Definition and purpose

A **task graph** is a directed representation of work stages and the transitions between them. Nodes may be deterministic functions, model calls, tools, agent teams, timers, or human approvals. Edges transfer typed state and express ordering or routing. Graph engineering makes dependencies, ownership, failure paths, and recovery inspectable.

Use a graph when task stages have different capabilities or trust levels, when branches depend on intermediate results, when independent tasks can be joined, or when a run must pause and resume. Do not draw a graph merely because a framework supports one.

### Workflow modeling

- **DAG:** directed acyclic graph; suitable for a finite set of dependencies with no retry edge. Retries are commonly implemented by an external scheduler or explicit cycle in a broader state machine.
- **Stateful graph:** nodes read and update a shared typed state. Define field ownership and merge semantics to prevent conflicting concurrent writes.
- **Runtime graph:** a graph interpreter executes transitions, checkpointing and streaming state as configured.
- **Dynamic graph:** a model or planner proposes tasks or routes at runtime. Validate the proposed graph against schemas, policy, budget, and allowed node types before execution.
- **Directed agent workflow:** nodes may contain agents; edges may carry structured outputs, not unrestricted conversation history.

A graph definition should specify node input/output contracts, edge conditions, retry behavior, timeouts, cancellation, checkpoint boundaries, and join semantics.

### Branching, routing, parallel execution, and concurrency

- **Branching:** select among known transitions based on validated state.
- **Routing:** classify an input or state and direct it to a specialized node. Log the router's input features and route choice.
- **Parallel execution:** run independent branches concurrently. Concurrency reduces latency only where dependencies permit it and provider/service limits allow it.
- **Concurrency control:** cap in-flight work, queue depth, per-tenant share, and fan-out size. Use immutable branch inputs or isolated state; merge explicitly.
- **Joins:** choose `ALL` when every branch is mandatory, `ANY` when one valid result suffices, `QUORUM` for a defined voting rule, or `SETTLED` when every branch outcome must be preserved. Timeouts and branch failures need explicit policy.

```text
                    +--> tests ------+
Plan -> Implement --+--> lint -------+--> ALL join -> Review
                    +--> typecheck --+                    |
                                                           +-- pass --> Publish
                                                           +-- fail --> Implement (bounded)
                                                           +-- stall --> Human escalation
```

### Human approval, failure, recovery, and subgraphs

A human approval node is a durable pause with an authenticated approver, a review payload, a deadline, and a resume decision. On resume, revalidate state because the underlying resource may have changed. Place irreversible effects after approval; if they occur before a pause, make them idempotent and verify they already happened.

Failure nodes classify exceptions and decide retry, compensation, escalation, or terminal failure. Recovery nodes restore a checkpoint, reconcile external effects, and re-check preconditions. A subgraph packages a reusable process with a documented input/output contract and an independent budget. Avoid nesting graphs solely to hide complexity.

### Multi-agent coordination

A multi-agent graph should define roles by capability and data ownership, not just persona. Use fan-out for genuinely independent work; join with a deterministic merge rule and provenance. Use an orchestrator only when task decomposition is input-dependent. Use isolated contexts or workspaces where concurrent agents could overwrite shared files or state. Track the cost and latency of coordination; extra agents often add more context transfer and merge work than useful parallelism.

### Graph diagrams

#### Human-gated task flow

```text
[Trigger]
    |
    v
[Validate contract] --invalid--> [Reject / clarify]
    |
    v
[Plan] --> [Implement loop] --> [Run independent checks]
                                   |              |
                                   +---- ALL -----+
                                          |
                                    +-----+-----+
                                    | pass      | fail / stalled
                                    v           v
                                 [Review]   [Retry or escalate]
                                    |
                           approve /|\ request changes
                                  / | \
                         [Publish] [Implement] [Escalate]
                              |
                       [Human decision]
```

#### Trust-separated issue processing

```text
Untrusted issue text
        |
        v
[Read-only intake agent] -> [Validated typed contract] -> [Policy validator]
                                                        /                 \
                                             invalid /                   \ valid
                                                  [Human]       [Implementation worker]
                                                                       |
                                                              [Isolated workspace]
                                                                       |
                                                          [Independent verifier]
                                                                       |
                                                         [Approval before publish]
```

The key security property is enforced through tool capability assignment and policy: the component reading arbitrary external text should not automatically receive privileged write or communication tools.

### Framework examples

Framework capabilities evolve. The examples below show architectural mapping, not a claim that the libraries are interchangeable or that any one framework supplies a complete enterprise platform.

#### LangGraph: explicit state and transitions

```python
from typing import Literal, TypedDict
from langgraph.graph import END, START, StateGraph

class State(TypedDict, total=False):
    question: str
    draft: str
    passed: bool
    attempts: int

def draft(state: State) -> dict:
    return {"draft": writer.invoke(state["question"])}

def verify(state: State) -> dict:
    return {"passed": deterministic_check(state["draft"]),
            "attempts": state.get("attempts", 0) + 1}

def route(state: State) -> Literal["done", "revise", "escalate"]:
    if state["passed"]:
        return "done"
    if state["attempts"] >= 3:
        return "escalate"
    return "revise"

def escalate(state: State) -> dict:
    return {"draft": state["draft"]}

def build_graph():
    graph = StateGraph(State)
    graph.add_node("draft", draft)
    graph.add_node("verify", verify)
    graph.add_node("escalate", escalate)
    graph.add_edge(START, "draft")
    graph.add_edge("draft", "verify")
    graph.add_conditional_edges("verify", route, {
        "done": END, "revise": "draft", "escalate": "escalate"
    })
    graph.add_edge("escalate", END)
    return graph.compile()
```

Persistence and human interrupts are runtime features that must be configured for a production deployment. Keep node functions idempotent where they perform external effects.

#### AutoGen: conversational team as a graph node

```python
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient

client = OpenAIChatCompletionClient(model="gpt-4o")
writer = AssistantAgent("writer", model_client=client,
                        system_message="Produce a draft for the given criteria.")
critic = AssistantAgent("critic", model_client=client,
                        system_message="Check the draft against the criteria; say APPROVE only if all pass.")
team = RoundRobinGroupChat(
    [writer, critic],
    termination_condition=TextMentionTermination("APPROVE"),
)

# In an async application:
# result = await team.run(task="Draft and evaluate ...")
```

AutoGen AgentChat teams provide conversation patterns and termination conditions. For safety-critical use, replace a free-text approval token with a validated structured verdict and an independent deterministic gate; bound messages and handle timeouts/cancellation.

#### CrewAI Flows: event-driven orchestration

```python
from pydantic import BaseModel
from crewai.flow.flow import Flow, listen, router, start

class WorkState(BaseModel):
    request: str = ""
    result: str = ""

class ReviewFlow(Flow[WorkState]):
    @start()
    def prepare(self):
        return self.state.request

    @listen(prepare)
    def produce(self, request: str):
        self.state.result = producer.kickoff(request).raw
        return self.state.result

    @router(produce)
    def decide(self):
        return "accepted" if deterministic_check(self.state.result) else "rework"

    @listen("accepted")
    def finish(self):
        return self.state.result

    @listen("rework")
    def escalate(self):
        return {"status": "needs_review", "draft": self.state.result}
```

CrewAI Flows provide event-driven state, listeners, routers, persistence, and human-feedback patterns. Verify router labels and persistence configuration for the installed version; this example intentionally routes failure to review rather than introducing an unbounded cycle.

#### OpenAI Agents SDK and application-owned workflows

OpenAI documents the Agents SDK as a code-first runtime with agents, tools, handoffs, guardrails, sessions/state surfaces, and tracing. It does not require the application to represent all business logic as a dedicated graph object. A workflow can be owned by ordinary application code, with SDK runs at model-driven stages:

```python
from agents import Agent, Runner

planner = Agent(name="Planner", instructions="Return a bounded plan with explicit steps.")
worker = Agent(name="Worker", instructions="Complete only the supplied step.")
reviewer = Agent(name="Reviewer", instructions="Check the result against the stated criteria.")

async def workflow(request: str) -> str:
    plan = await Runner.run(planner, request)
    validate_plan(plan.final_output)  # schema and policy validation in application code

    result = await Runner.run(worker, plan.final_output)
    if not deterministic_checks(result.final_output):
        raise RuntimeError("Verification failed; route to bounded recovery policy")

    review = await Runner.run(reviewer, result.final_output)
    validate_review(review.final_output)
    return result.final_output
```

The example is intentionally linear and does not demonstrate a full durable graph. Use application state storage, idempotent nodes, and an orchestration runtime if durable pause/resume, complex routing, or transactional coordination is required. Do not imply that model-generated prose alone validates a plan or approves a side effect.

## Comparative Analysis

| Dimension              | Harness engineering                                                      | Loop engineering                                            | Graph engineering                                                        |
| ---------------------- | ------------------------------------------------------------------------ | ----------------------------------------------------------- | ------------------------------------------------------------------------ |
| Scope                  | Capabilities, context, policies, tools, runtime environment              | Repeated actions, feedback, retries, termination            | Stages, state, dependencies, routes, joins, gates                        |
| Primary responsibility | Define what is possible and safely observable                            | Define when to act again and when to stop                   | Define which step runs next and what data moves                          |
| Typical complexity     | Low to high; often cross-cutting                                         | Low to high; grows with retries and evaluation              | Low for a chain, high for durable or dynamic orchestration               |
| Typical failures       | Excess authority, poor context, weak tools, lost state                   | Spinning, premature completion, oscillation, budget overrun | False dependencies, invalid routes, broken joins, duplicate effects      |
| Common tooling         | Tool gateways, MCP clients, sandboxes, stores, telemetry                 | Test runners, evaluators, retry/budget controllers          | State machines, workflow runtimes, queues, checkpoint stores             |
| Scalability concern    | Isolation, tenancy, tool throughput, state retention                     | Retry amplification, evaluator load, queue pressure         | Coordination overhead, shared-state contention, fan-out size             |
| Latency impact         | Tool/proxy overhead; context retrieval                                   | Additional turns and verification                           | Sequential dependencies add latency; parallelism may reduce it           |
| Cost impact            | Context, storage, tools, telemetry, model choice                         | Retries and evaluator calls                                 | Orchestration plus worker calls; fan-out can multiply usage              |
| Maintainability        | Clear interfaces and policy centralization help; hidden middleware hurts | Explicit exit rules and evidence simplify operations        | Typed edges and modular nodes help; excessive graphing obscures behavior |

## Production Failure Analysis

### 1. Wrong harness

- **Symptoms:** the agent cannot find relevant information, uses an unsafe or irrelevant tool, floods context, loses decisions after a restart, or behaves differently between environments.
- **Root causes:** poor tool contracts, broad or missing permissions, eager context injection, unversioned instructions, memory without provenance, environment drift, or incomplete trace coverage.
- **Debugging:** correlate the run ID with model requests, context sources, tool discovery, policy outcomes, state snapshots, environment versions, and data access. Check whether the required capability existed and whether the model received the right, minimal evidence.
- **Mitigation:** improve tool interfaces and repository/domain maps; retrieve context on demand; scope permissions; validate state schemas; pin dependencies; add environment health checks; redact and trace consistently.

### 2. Broken loop

- **Symptoms:** the agent says it is done while checks fail; repeats identical actions; fixes one check while breaking another; retries after authorization denial; or consumes an unbounded budget.
- **Root causes:** model-controlled success criteria, feedback without precise evidence, checks the actor can modify, no attempt/deadline limits, retry layers multiplying, or no stall detection.
- **Debugging:** graph attempt count, normalized error fingerprints, artifact hashes, check outcomes per iteration, budget accounting, and the exact stop reason. Compare progress with a measurable baseline rather than judging transcript confidence.
- **Mitigation:** make verification independently executable, protect its inputs, return concise actionable errors, define success/budget/stall exits, classify retryability, and escalate when progress plateaus.

### 3. Poor graph design

- **Symptoms:** unnecessary waits, missing branch outputs, one optional branch aborts useful work, workers overwrite each other, resume duplicates a side effect, or a router sends sensitive work to an untrusted node.
- **Root causes:** false dependencies, untyped/free-text edges, unspecified join semantics, shared mutable state, non-idempotent nodes, inadequate failure routes, or model-generated routing without validation.
- **Debugging:** inspect a trace of node start/end times, input/output schemas, route decisions, join outcomes, checkpoint versions, side-effect IDs, and branch ownership. Replay with the same input and deterministic fakes where possible.
- **Mitigation:** remove edges without data dependencies; define typed node contracts and merge functions; choose explicit `ALL`/`ANY`/`QUORUM`/`SETTLED` joins; bound concurrency; isolate state; make effects idempotent; validate dynamic plans before execution.

## AI Agent Design Framework

Use this sequence to select architecture:

1. **Can one model call plus retrieval or a deterministic function meet the requirement?** If yes, do not add an autonomous loop.
2. **Does a model need to select among tools or gather evidence over multiple actions?** Add a harness with a narrow tool set and observable results.
3. **Can completion be checked independently?** If yes, add a bounded verification loop. If not, define a human or calibrated evaluation path before granting more authority.
4. **Does the task contain semantically distinct stages, conditional routes, approvals, useful independent branches, or durable resume points?** Add a graph to control those transitions.
5. **Is parallel work truly independent and worth its coordination, merge, and model cost?** Fan out only those tasks; define a join and failure policy.
6. **Does the system repeatedly fail in the same way?** Improve the interface, policy, evaluation, or check first; add model complexity only when evidence identifies that as the defect.

### Architecture selection

- **Only harness:** one agent with tool use; one-session tasks; no complex multi-stage flow; minimal persistence if the request is ephemeral.
- **Harness + loops:** coding, research, data operations, or support flows with repeated work and measurable checks; bounded retries and escalation are required.
- **Harness + loops + graphs:** long-running tasks, human approval, multiple trust domains, distinct stages, route-dependent work, parallel branches, or restart/resume requirements.

If the graph state schema cannot be stated clearly, the task is not yet understood well enough to orchestrate. Explore with a single agent or deterministic prototype, then formalize the graph after real transitions are known.

## Enterprise Architecture Patterns

### Pattern 1: Single-agent architecture

```text
API -> policy/context assembly -> agent <-> narrow tools -> verifier -> response
```

Use for bounded tasks where one context is beneficial. Keep tool scopes small, enforce request identity, set a run budget, and instrument every tool call. Scale stateless runs horizontally; keep per-run state external when needed.

### Pattern 2: Tool-augmented agent

```text
Client -> agent runtime -> tool gateway -> domain services / data systems
                         |                 |
                         +-> policy         +-> audit events
```

The gateway performs authentication, authorization, schema validation, rate limiting, and idempotency. The model receives business-level tools, not raw database credentials or unrestricted network access. Treat retrieved content as untrusted.

### Pattern 3: Multi-agent team

```text
                 +--> specialist A --+
Request -> planner+--> specialist B --+--> typed merge -> verifier
                 +--> specialist C --+
```

Use specialists for independent expertise or clean context, not merely to assign human-like titles. Restrict fan-out, specify whether branches are independent, pass structured outputs, retain provenance, and resolve conflicts deterministically or with a defined evaluator.

### Pattern 4: Human-in-the-loop system

```text
Agent proposal -> deterministic policy -> approval queue -> human decision
       ^                                              |             |
       +---------------- rejected feedback -----------+             +--> effect
```

The approval request should include action, target, impact, evidence, and expiration. Bind approval to a specific action hash and state version. Reauthorize and revalidate before execution; approval is not blanket future permission.

### Pattern 5: Enterprise agent platform

```text
                 +---------------- Control plane ----------------+
                 | identity | policy | model/tool registry       |
                 | budgets  | evals  | deployment/configuration   |
                 +-----------------------+------------------------+
                                         |
Client/API -> admission -> workflow runtime -> isolated workers/tools
                  |             |                 |
                  +-------- telemetry/audit -------+
                                         |
                     state store / queues / secrets broker
```

A platform centralizes identity, policy, versioning, quotas, observability, and lifecycle management, while domain teams own narrowly scoped tools and task contracts. Tenant isolation, data residency, retention, incident response, and model-provider governance are platform requirements, not prompt conventions.

## Implementation Roadmap

### Level 1 — Prompt engineering

Use direct model requests with explicit inputs and output expectations. Establish an evaluation set, record provider/model versions, and validate output shape. Do not use the output as authority to perform consequential actions without application checks.

### Level 2 — Agent harness

Add typed tools, identity-aware authorization, context retrieval, timeouts, scoped credentials, structured logging, and a deployment sandbox. Define task contracts and data retention.

### Level 3 — Structured loops

Add deterministic verification, actionable feedback, bounded retries, budgets, stall detection, cancellation, idempotency, and escalation. Measure successful task outcomes and human corrections.

### Level 4 — Graph orchestration

Represent stages, state, route conditions, parallel branches, joins, approval pauses, checkpoints, and recovery explicitly. Version node contracts and test routes, resume, duplicate events, and partial branch failures.

### Level 5 — Distributed multi-agent systems

Scale independent workers with queue-based dispatch, workload isolation, quotas, leases, deduplication, trace correlation, and robust merge semantics. Introduce agents incrementally, benchmark cost/latency/quality against a single-agent baseline, and keep human ownership of platform policy changes.

Maturity is not a mandate to reach Level 5. The correct level is the least complex architecture that meets measured quality, safety, latency, and availability requirements.

## Research Perspective

### Agent runtime architectures

Runtime research spans direct tool-calling loops, hosted managed agents, application-owned runtimes, event-driven actor systems, and durable workflow engines. A useful comparison asks who owns model invocation, state, sandboxing, tool execution, approval, trace retention, and recovery. No runtime is complete without specifying its failure and data semantics.

### Cognitive architectures and planning

An agent can be modeled as a policy repeatedly selecting actions from observations and state. Explicit planners can decompose goals into subgoals, but generated plans are hypotheses: validate feasibility, permissions, dependencies, and budgets before execution. Search-based approaches such as Tree of Thoughts explore alternative reasoning paths; they incur additional inference cost and still need external correctness checks.

### Tool use and environment grounding

Tool use closes the gap between parametric knowledge and current external state. ReAct is a foundational formulation that interleaves reasoning and actions with environmental observations. Production systems should expose the smallest effective action space and preserve the provenance of each observation. Tool success is evidence that a call completed, not proof that the user's goal was satisfied.

### Reflection and learning

Reflection can transform failure feedback into revised plans or retained notes. Reflexion studies verbal feedback and episodic memory as a way to improve later decisions without updating model weights. In deployed systems, reflection should be grounded in verifiable outcomes, scoped to a task or tenant, and evaluated for stale or harmful memory. Self-critique is correlated with the generator and should supplement, not replace, independent tests or human judgment.

### Long-term memory

Persistent memory requires policies for provenance, freshness, contradiction resolution, privacy, access control, and deletion. Retrieval quality and memory selection are separate from storage durability. Store compact, source-linked facts or workflow state rather than treating an entire transcript as durable truth. Evaluate the effect of memory ablations and retrieval errors.

### Future directions

Important research questions include how to evaluate long-horizon task success rather than activity; how to attribute failures across model, tool, policy, and workflow layers; how to make durable execution safe under retries and partial failure; how to calibrate automated evaluators; how to quantify the cost and value of multi-agent coordination; and how to reduce prompt-injection risk across tool and memory boundaries. As models improve, harness components should be re-tested: retain controls justified by risk and measured performance, but remove brittle scaffolding that no longer provides value.

## Key Takeaways

1. An agent is a socio-technical system, not just a prompt or model.
2. Harness, loop, and graph name different responsibilities, even when they share code.
3. The harness determines what the agent can see and do.
4. A loop determines how work repeats, receives feedback, and terminates.
5. A graph determines the next task stage and what data crosses each edge.
6. The model's statement that it is done is not sufficient completion evidence.
7. Authorization belongs in trusted application code and infrastructure.
8. Tool descriptions and schemas are part of the agent-computer interface.
9. Untrusted text must not silently become privileged instruction or policy.
10. Conversation history, workflow state, long-term memory, and audit logs are distinct.
11. Checkpoints do not make external side effects exactly-once.
12. Idempotency and reconciliation are required for reliable resume around effects.
13. Every retry needs a class, owner, limit, and stop condition.
14. A useful loop has success, budget, cancellation, and stall outcomes.
15. Exact diagnostic feedback usually beats a generic request to retry.
16. Independent checks are stronger than an actor grading its own work.
17. Protect evaluator inputs so the actor cannot redefine success.
18. Parallelize only tasks with real data independence.
19. Every fan-out requires a join rule and a partial-failure policy.
20. Typed edges reduce ambiguity and context transfer.
21. Model-generated plans and routes must be validated before execution.
22. Human approval should bind to a specific proposal and state version.
23. Traces need correlation, redaction, access control, and retention policies.
24. Measure cost per successful outcome, including retries and human rework.
25. Add architectural complexity only when evaluation shows a measurable benefit.

## Glossary

| Term                     | Definition                                                                                                        |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------- |
| Agent                    | A system in which a model or learned policy selects actions in an environment through a runtime.                  |
| Agent runtime            | Software that drives model requests, tool dispatch, state handling, and run lifecycle.                            |
| Approval gate            | A control point that pauses execution until an authorized human or policy approves a specific action.             |
| Audit record             | A retained, access-controlled record of decisions, actions, state changes, and outcomes.                          |
| Checkpoint               | A persisted snapshot from which a workflow can recover or resume.                                                 |
| Context                  | Information supplied to a model for a particular request.                                                         |
| Control layer            | Application logic and infrastructure enforcing policy, routing, budgets, verification, and state rules.           |
| DAG                      | Directed acyclic graph; a directed dependency graph with no cycles.                                               |
| Evaluator                | A component that judges output against criteria; may be deterministic, model-based, or human.                     |
| Fan-out / join           | A graph pattern that launches branches and later combines their outcomes under an explicit rule.                  |
| Feedback                 | Evidence from an action or evaluation used to inform the next decision.                                           |
| Graph                    | A directed model of task stages, dependencies, state transitions, and routing.                                    |
| Harness                  | Runtime capabilities and surrounding infrastructure controlling context, tools, policies, state, and observation. |
| Idempotency key          | Stable identifier used by a service to avoid repeating the same logical side effect.                              |
| Loop                     | Repeated execution of action, observation, feedback, and stop logic.                                              |
| MCP                      | Model Context Protocol, a protocol for connecting model applications to external tools and resources.             |
| Middleware               | Code around model/tool boundaries that applies reusable policy, validation, retries, or telemetry.                |
| Node                     | A unit of work in a graph, such as a tool, model call, deterministic function, or human interaction.              |
| Observation              | Data returned from an environment or verifier after an action.                                                    |
| Orchestrator             | A component that decomposes work, assigns tasks, or selects graph transitions.                                    |
| Persistence              | Durable storage of selected state or records beyond a process lifetime.                                           |
| Policy enforcement point | Trusted component that allows, denies, constrains, or escalates an action.                                        |
| Retry budget             | Maximum permitted retries or attempts for a specified class of failure.                                           |
| Router                   | A function or model that selects a next node based on state or input.                                             |
| Run                      | One execution instance of an agent task or workflow, with an identity and lifecycle.                              |
| Sandbox                  | Isolated execution environment that constrains filesystem, process, and network access.                           |
| State                    | Structured information required to determine a run's current status and next action.                              |
| Tool                     | A callable operation made available to an agent or graph node.                                                    |
| Trace                    | Correlated events and spans describing an execution across components.                                            |
| Verification             | Assessment against independent criteria that determines whether an output or side effect meets requirements.      |

## References

Framework APIs change; treat these as entry points and verify versioned documentation before implementation.

1. OpenAI, [Agents overview](https://developers.openai.com/api/docs/guides/agents), [Agents SDK quickstart](https://developers.openai.com/api/docs/guides/agents/quickstart), and [orchestration and handoffs](https://developers.openai.com/api/docs/guides/agents/orchestration). The SDK is application-hosted; the separate Agents API is a managed runtime option.
2. LangGraph, [overview](https://docs.langchain.com/oss/python/langgraph/overview), [graph API](https://docs.langchain.com/oss/python/langgraph/graph-api), [persistence](https://docs.langchain.com/oss/python/langgraph/persistence), and [interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts).
3. LangChain, [Python documentation](https://docs.langchain.com/oss/python/langchain/overview) and [agents](https://docs.langchain.com/oss/python/langchain/agents).
4. Anthropic, [Building effective agents](https://www.anthropic.com/research/building-effective-agents), including workflow patterns and tool-interface guidance.
5. CrewAI, [agents](https://docs.crewai.com/concepts/agents), [tasks](https://docs.crewai.com/concepts/tasks), [crews](https://docs.crewai.com/concepts/crews), and [flows](https://docs.crewai.com/concepts/flows).
6. Microsoft AutoGen, [AgentChat quickstart](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/quickstart.html), [teams](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/teams.html), and [Core](https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/index.html).
7. PydanticAI, [agents](https://pydantic.dev/docs/ai/core-concepts/agent/), [multi-agent applications](https://pydantic.dev/docs/ai/guides/multi-agent-applications/), and [durable execution](https://pydantic.dev/docs/ai/capabilities/durable_execution/overview/).
8. Yao et al., [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629), ICLR 2023.
9. Shinn et al., [Reflexion: Language Agents with Verbal Reinforcement Learning](https://arxiv.org/abs/2303.11366), NeurIPS 2023.
10. Yao et al., [Tree of Thoughts: Deliberate Problem Solving with Large Language Models](https://arxiv.org/abs/2305.10601), NeurIPS 2023.
11. Anthropic, [Model Context Protocol](https://modelcontextprotocol.io/), specification and implementation resources.
12. For broader agentic-system patterns, see the workflow and agent distinctions in Anthropic's reference above and the primary papers linked above. Framework patterns should be evaluated against the application's own task distribution and risk model.

---

**Source note:** This handbook is an original technical synthesis based on the user-provided article and checked framework/research documentation. It preserves the conceptual model while redrawing diagrams in ASCII and adding explicit production caveats. The Harness/Loop/Graph taxonomy is an engineering lens, not a claim that all cited frameworks use these terms identically.
