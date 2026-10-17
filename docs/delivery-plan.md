# Kentaro Harness Delivery Plan

## Decision

Kentaro v0.1 is an open-source, read-only Agentic Maysano Harness. It has two
complementary delivery routes:

1. **GitHub repository** for source, contribution, examples, architecture, and self-hosting.
2. **PyPI package** for a versioned, installable command-line product and coding-agent integrations.

The package does not replace the repository. The repository remains the project home;
PyPI is the adoption route for a user applying Kentaro in an existing project.

## v0.1 Product Boundary

Kentaro v0.1 retrieves and explains bounded, sourced portfolio context from the
Maysano pilot or a synthetic demo. It validates local governance and delivery
objects, generates drafts, briefings, dashboards, and reports, evaluates proposed
actions deterministically, and exports append-oriented evidence logs.

Maysano remains the system of record for portfolio state, approvals, business-context
graph updates, tenant controls, and platform audit. Kentaro does not replace Maysano,
Codex, or any other coding agent.

The v0.1 harness may create **local schema instances or files only**. A local
`Mandate`, `WorkEnvelope`, or `ExecutionPackage` is not a Maysano record and has
no authority outside the local harness.

### v0.1 does not

- create external records;
- execute tools, calls, or side effects;
- request, receive, or process real approvals;
- write to Maysano or to its business context graph;
- use a network adapter for mutation; or
- claim immutable, compliance-grade, or platform audit.

An optional hash chain can make a local evidence-log modification detectable. It
does not make that log immutable or compliance-grade.

## Core Object Model

Kentaro keeps authority, delivery planning, proposed action, and evidence separate:

```text
Mandate → Work Envelope → Execution Package → Execution Requests → Evidence Bundle
```

- **Mandate** defines durable authority, access boundaries, ownership, and escalation.
- **Work Envelope** narrows that authority for one business assignment.
- **Execution Package** defines planned delivery work only: steps, expected outputs,
  dependencies, timing, and acceptance criteria.
- **Execution Request** represents one proposed individual action.
- **Evidence Bundle** records the context, versions, plans, evaluations, outputs,
  and corrections associated with the work.

`ContextPackage`, `EvidenceEvent`, and `Correction` support the chain. The
authoritative definitions, required fields, and relationship rules are in the
[governance and delivery object model](governance-and-delivery-object-model.md).

### Authority invariant

An `ExecutionPackage` must reference a `WorkEnvelope`. It must never add authority,
tools, data access, scope, or approval rights beyond its referenced `WorkEnvelope`
and `Mandate`. Validation rejects a package that violates this invariant.

## Primary Local Flow

The intended user flow is local and read-only:

```text
Retrieve bounded context → validate local objects → prepare delivery plan →
evaluate proposed actions → generate draft/report/dashboard → export evidence
```

For example, a user may ask:

```text
Show me the portfolio dashboard.
```

They may also create a local, versioned delivery package that explains how work
could proceed. It remains a plan. Kentaro must not execute the plan or create
external business objects.

## Interfaces

### CLI, required for v0.1

The CLI is the common baseline for users, CI, and coding agents. v0.1 commands
operate only on read-only context or local files.

```bash
kentaro validate-config
kentaro portfolio brief
kentaro dashboard --output .kentaro/workspace/dashboards/portfolio.html
kentaro object validate
kentaro policy evaluate
kentaro evidence export
kentaro evidence verify
```

`object validate`, `policy evaluate`, and `evidence export` use local JSON object
bundles. [The synthetic example](../examples/governance/retention-review.json)
is a starting point for local instances; it never creates a product, objective,
use case, or other record in Maysano.

### Python API, required for the core

The portable Python core provides the same context, schema validation, policy
evaluation, evidence export, and report services as the CLI. It has no dependency
on Codex and no mutation adapter in v0.1.

### MCP and agent integrations, later

MCP and project integrations for Codex, Claude Code, and OpenCode must call the
same core services. They must not introduce separate schemas or bypass the policy
evaluator. In v0.1, any future MCP surface remains read-only/local-only.

## Deterministic Policy Evaluation

The policy evaluator is a pure, deterministic validation service. It evaluates an
`ExecutionRequest` against the referenced `Mandate` and `WorkEnvelope`, and returns
one of:

| Outcome | v0.1 meaning |
| --- | --- |
| `allowed` | Structurally in scope. It does **not** permit execution. |
| `approval_required` | A future authority boundary would require approval. No approval is requested or processed in v0.1. |
| `denied` | The request is outside the declared boundary. |
| `escalated` | Required context, authority, or source consistency is missing or ambiguous. |

The evaluator must not call external tools, make network mutations, send messages,
or produce side effects.

## Evidence

v0.1 exports local, append-oriented evidence logs and reports. An export preserves
source identifiers, object versions, timestamps, actor identity, redacted references,
policy evaluations, and output references. Sensitive values stay out of logs and
exports. The harness may optionally hash-chain records to indicate tampering, but
does not claim immutability, retention enforcement, compliance, or platform audit.

## Repository and Workspace Boundary

`.kentaro/workspace/` is the ignored local workspace for generated dashboards,
reports, exports, evidence logs, and local object instances. Source, documentation,
schemas, and tests remain tracked repository work. Secrets, generated runtime state,
and customer content must not be committed.

## Implementation Order

1. Document and ratify the v0.1 read-only boundary and object model.
2. Define versioned schemas for `ContextPackage`, `Mandate`, `WorkEnvelope`,
   `ExecutionPackage`, `ExecutionRequest`, `EvidenceEvent`, and `Correction`.
3. Implement pure relationship validation, including the execution-package authority invariant.
4. Implement the deterministic, side-effect-free policy evaluator.
5. Implement redacted, append-oriented evidence exports and reports.
6. Add tests for missing owners, expired approvals, out-of-envelope tools, stale or
   conflicting sources, authority escalation, secret redaction, and reproducible evidence links.
7. Preserve and extend sourced read-only context retrieval, briefings, lists, and dashboards.

No live write adapter, approval workflow, external tool executor, or graph write path
belongs in this implementation order.

## Later Extensions

Future work may add explicit approval workflows, narrowly scoped write adapters,
Maysano synchronisation, external execution runtimes, or platform-level audit. Each
requires a verified Maysano API contract, narrow credentials, an explicit approval
path, contract tests, and a separately ratified scope change. A future execution
adapter remains optional and must not change the v0.1 core boundary.

## v0.1 Exit Condition

A user can retrieve sourced context, create and validate local versioned objects,
prepare a delivery package, evaluate proposed actions without execution, inspect a
dashboard or report, and export a redacted evidence log. The user can see clearly
what is known, missing, in scope, or denied—without Kentaro changing an external
system.
