# Governance and Delivery Object Model

## Status and scope

This specification is the target object architecture for Kentaro. In v0.1, these
objects are local, versioned schemas and validation inputs only. They do not create
Maysano records, authorise action, request approvals, invoke tools, or write to the
business context graph.

Maysano remains the system of record for portfolio state, approvals, graph updates,
tenant controls, and platform audit. A future write or execution capability requires
a separately ratified scope, a verified Maysano API contract, narrow credentials,
an explicit approval path, and contract tests.

## Relationship model

```text
ContextPackage ─┐
                ├── Mandate → Work Envelope → Execution Package
                │                                  │
                │                                  └── Execution Requests
                │                                           │
Correction ─────┴──────────────────────────────────────────┴── Evidence Bundle
                                                       (Evidence Events)
```

The primary authority and delivery path is:

```text
Mandate → Work Envelope → Execution Package → Execution Requests → Evidence Bundle
```

`ContextPackage` supplies bounded, sourced business context. `Correction` records
feedback with a declared destination; it does not silently rewrite another object.

## Common schema requirements

Every object has these fields:

| Field | Requirement |
| --- | --- |
| `id` | Stable, locally unique identifier. |
| `schema_version` | Version of the object schema used for validation. |
| `version` | Version of this object instance. |
| `created_at` | ISO 8601 timestamp with timezone. |
| `actor` | Local actor identity or declared system actor. |
| `source_references` | Zero or more source IDs, versions, and retrieval timestamps. |
| `relationship_references` | IDs and versions of linked local objects. |

Objects must preserve source references rather than copying mutable source text into
every event. Sensitive values must be represented by a redacted reference, never
stored in evidence exports.

## Objects

### ContextPackage

A bounded, read-only collection of Maysano or synthetic-demo context for one
assignment. It records the retrieval scope, source IDs, source versions, retrieval
time, freshness, and conflicts or unknowns. It is evidence of what Kentaro saw, not
a replacement portfolio record.

### Mandate

A durable definition of authority and boundaries for a business area. It identifies
the business owner, allowed data categories, allowed tools or operations for future
use, excluded activities, escalation route, expiry, and review cycle. In v0.1 it is
a local declaration and has no effect on external systems.

### WorkEnvelope

An assignment-specific narrowing of one `Mandate`. It identifies the assignment,
business objective, decision context where available, requested result, included
scope, exclusions, permitted data, expected output, owner, reviewers, expiry, and
future approval conditions. It must reference exactly one active `Mandate` version.

### ExecutionPackage

A delivery-planning object. It references exactly one `WorkEnvelope` and describes
planned steps, expected outputs, dependencies, timing, assumptions, and acceptance
criteria. It is not an authority object.

**Invariant:** An `ExecutionPackage` must never add authority, tools, data access,
scope, or approval rights beyond its referenced `WorkEnvelope` and `Mandate`.

### ExecutionRequest

A proposed individual action linked to an `ExecutionPackage`. It contains the
declared action, target, redacted parameters, requested authority level, and any
required source references. In v0.1 it is only evaluated; no request is executed or
sent to an external system.

### EvidenceEvent and Evidence Bundle

An `EvidenceEvent` records one local event: context retrieval, validation, plan,
policy evaluation, generated output, or correction. An `EvidenceBundle` is a
queryable/exportable grouping of events for the same work envelope. The export is an
append-oriented local evidence log. Hash chaining may signal tampering but does not
provide immutability, retention enforcement, compliance, or platform audit.

### Correction

Structured feedback linked to the object it should improve. Its `kind` is one of
`output`, `context`, `mandate`, `policy`, or `tool`. Its destination must be explicit.
In v0.1, recording a correction never applies a graph, mandate, policy, or tool change.

## Relationship validation

The validator rejects or escalates the following conditions:

| Rule | Result |
| --- | --- |
| Missing or expired Mandate | `escalated` |
| WorkEnvelope does not reference its Mandate version | `denied` |
| WorkEnvelope expands Mandate scope, data, or declared tools | `denied` |
| Missing named owner for a decision or requested change | `escalated` |
| ExecutionPackage has no WorkEnvelope reference | `denied` |
| ExecutionPackage expands its envelope or mandate | `denied` |
| ExecutionRequest uses a tool outside the envelope | `denied` |
| Required context is stale, conflicting, or unknown | `escalated` |
| Evidence link lacks a source ID, version, or timestamp | validation failure |

An expired future approval is represented as data and evaluated deterministically;
v0.1 neither requests nor processes an approval.

## Deterministic policy evaluator

The evaluator is a pure function of an `ExecutionRequest`, its referenced
`ExecutionPackage`, `WorkEnvelope`, `Mandate`, and `ContextPackage` metadata. It
must not call tools, make network mutations, request approval, or cause side effects.

| Outcome | Meaning in v0.1 |
| --- | --- |
| `allowed` | The proposal is structurally in scope. This is not execution permission. |
| `approval_required` | The declared future boundary needs approval. No real approval is created, requested, or processed. |
| `denied` | The proposal violates a declared boundary. |
| `escalated` | Context, ownership, source consistency, or authority is missing or ambiguous. |

Every result contains the evaluated object IDs and versions, rule IDs, reasons, and
evaluation timestamp so that a later evidence export can reproduce the conclusion.

## Evidence export requirements

An export includes:

- Context source IDs, source versions, and retrieval timestamps.
- Mandate, WorkEnvelope, and ExecutionPackage IDs and versions.
- Proposed execution requests and policy outcomes.
- Generated output references and redaction status.
- Actor identities, event timestamps, and correction references.
- Optional predecessor hash and record hash when hash chaining is enabled.

Exports must redact secrets and sensitive values. They must describe unavailable,
stale, conflicting, or permission-limited source information explicitly rather than
inferring a favourable state.

## Required v0.1 test cases

- Missing owners.
- Expired approval data.
- Tools outside the WorkEnvelope.
- Stale or conflicting sources.
- Authority escalation.
- Secret redaction.
- Evidence links that reproduce the context and authority used.
- An ExecutionPackage attempting to exceed its WorkEnvelope or Mandate.
- `allowed` producing no external call, mutation, or approval request.
