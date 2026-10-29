# Governance and Delivery Object Model

## Status and scope

This specification is the target object architecture for Kentaro. In v0.1, these
objects are local, versioned schemas and validation inputs only. They do not create
Maysano records, authorise action, request approvals, invoke tools, suspend live
access, or write to the business context graph.

Maysano remains the system of record for portfolio state, approvals, graph updates,
tenant controls, and platform audit. A future write or execution capability requires
a separately ratified scope, a verified Maysano API contract, narrow credentials,
an explicit approval path, and contract tests.

## Relationship model

```text
ContextPackage ────────────────────────────────────────────────────┐
Mandate → Work Envelope → Execution Package → Execution Requests ──┼── Evidence Bundle
                           ▲                    │                   │   (Evidence Events)
                           └── RevocationPolicy ┘                   │
Correction ────────────────────────────────────────────────────────┘
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

### Planned v0.3 task-scoped cache

For an active Maysano Change Contract, v0.3 will retain the authorised graph projection in a
managed local `ContextPackage` cache. The cache is not a second graph store or a default complete
company-graph synchronisation. It contains only the active contract; in-scope objectives, use
cases, data products, relationships, decisions, risks, ownership, and evidence; record IDs and
versions or ETags; source timestamps and references; tenant/workspace and retrieval scope; cache
creation and expiry; and a Maysano graph revision or sync cursor when available.

Kentaro uses delta synchronisation only for changed in-scope records and revalidates affected
records before submitting a future `GraphChangeSet`. The cache becomes unusable when its Change
Contract expires or is revoked. Maysano remains authoritative for graph state, authority,
revocation, mutation acceptance, and audit.

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
required source references. It must reference a versioned `RevocationPolicy` that
matches its WorkEnvelope and Mandate chain. In v0.1 it is only evaluated; no request
is executed or sent to an external system.

### RevocationPolicy and the required revocation clause

Every future execution-capable agent or capability must have an active
`RevocationPolicy`; this is a required control, not an optional best practice. The
**revocation clause** answers, for the declared scope, both questions that make
authority reversible:

1. Which behaviour suspends the agent's authority or credentials?
2. Which accountable human role can suspend, restore, or narrow that access?

In v0.1, a `RevocationPolicy` is a local, versioned declaration. Kentaro validates
the declaration, includes its local status and version in review-readiness output,
and records that classification in local evidence. It does not hold credentials,
suspend live access, submit a request, execute an action, or claim that a local
status reflects Maysano's live state.

The JSON object retains the common `id` so references use the same local object
format. Its required `policyId` must equal that `id`; this avoids two competing
identifiers. Required fields are:

| Field | Requirement |
| --- | --- |
| `policyId`, `version` | Stable policy identifier and positive version. `policyId` equals `id`. |
| `scope` | One of `agent`, `capability`, `connector`, `workspace`, or `mandate`. |
| `authorityChain` | References the Mandate and WorkEnvelope and names roles allowed to suspend, restore, narrow, and perform emergency suspension. |
| `accountableOwnerRole` | The named role accountable for the agent's business purpose. |
| `suspensionTriggers`, `triggerThresholds` | Includes every minimum trigger below and a positive threshold for repeated correction, rejection, or safety failure. |
| `severity`, `immediateAction` | Declared severity and one of `disable_execution`, `disable_connector`, `require_human_review`, or `restrict_scope`. |
| `evidenceRequirements`, `notificationTargets` | Required local evidence and named recipients. |
| `restorationRequirements` | Requirements for a future restoration decision. |
| `expiryOrReviewDate` | Timestamp after which local classification escalates. |
| `localStatus` | `declared_active` or `simulated_suspended`; it is a local validation/simulation value, not live access state. |

The minimum suspension triggers are:

- action outside the approved WorkEnvelope or Mandate;
- payload, scope, or target that differs from the approved version or digest;
- required source evidence that is missing, stale, or contradictory;
- confidential, personal, or credential-derived data in an unapproved output or request;
- deterministic validation or policy-control failure;
- repeated correction, rejection, or safety failure crossing a declared threshold;
- identity, connector, or credential integrity that cannot be verified; and
- emergency suspension issued by a named accountable authority.

The named future Maysano roles are:

| Role | Responsibility |
| --- | --- |
| Service Owner | Accountable for the agent's business purpose. |
| Policy Owner | Owns the applicable governance rule. |
| Connector Owner | Suspends or restores connector credentials. |
| Security Officer | Issues emergency suspension for security or data exposure. |
| Platform Administrator | Carries out authorised technical suspension and restoration. |

Every policy must name an accountable owner and at least one emergency authority;
the v0.1 schema requires `Security Officer` in the emergency-suspension roles.

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
| ExecutionRequest lacks a matching RevocationPolicy version | validation failure |
| RevocationPolicy lacks a named owner, emergency authority, required trigger, or valid authority chain | validation failure |
| Locally simulated RevocationPolicy suspension | `denied`; no action is dispatched |
| ExecutionRequest uses a tool outside the envelope | `denied` |
| Required context is stale, conflicting, or unknown | `escalated` |
| Evidence link lacks a source ID, version, or timestamp | validation failure |

An expired future approval is represented as data and evaluated deterministically;
v0.1 neither requests nor processes an approval.

## Deterministic policy evaluator

The evaluator is a pure function of an `ExecutionRequest`, its referenced
`ExecutionPackage`, `WorkEnvelope`, `Mandate`, `RevocationPolicy`, and
`ContextPackage` metadata. It must not call tools, make network mutations, request
approval, or cause side effects. A locally simulated suspension or expired policy
review date changes only the structural classification; it cannot suspend credentials
or enforce live access.

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
- RevocationPolicy ID, version, local status, review date, and classification result.
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
- A missing or mismatched RevocationPolicy reference.
- Missing minimum revocation triggers or named emergency authority.
- A simulated suspension denying classification without any credential, approval, or execution operation.
- `allowed` producing no external call, mutation, or approval request.

## Future Maysano-controlled revocation enforcement

The revocation clause becomes authoritative only in a future Maysano-governed write
and execution path. Maysano—not local Kentaro—owns revocation state, credentials,
enforcement, retention, and audit evidence. A suspension must take effect before the
next external action; emergency suspension disables the relevant execution permission
or credential. A suspended agent must not resume from cached authority.

Restoration requires a new, versioned Maysano decision record with rationale,
evidence, exact scope, timestamp, expiry, named authority, and the bound request and
payload/diff digest. It does not mutate the ExecutionRequest. Each execution request
must reference the active RevocationPolicy version before Maysano dispatches it.
