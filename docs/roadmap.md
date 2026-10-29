# Kentaro Delivery Plan: v0.1 to v0.5

## Purpose

Kentaro is an open-source, MIT-licensed local harness for governed work against a Maysano
company graph. It gives code assistants and other agentic tools a bounded way to retrieve
business context, form structured drafts, evaluate proposed work, and, from v0.3, submit
approved graph changes.

Maysano remains the company system of record. It owns graph persistence, tenant isolation,
authority, revocation, audit, and the canonical state of objectives, use cases, data products,
and their relationships.

- Kentaro understands authorised context and proposes bounded work.
- Maysano authorises, validates, persists, and records company-graph changes.
- Local model execution is configurable through the Open Data Product SDK, subject to selected
  provider, content-egress, and deployment controls.
- Kentaro does not gain broad or persistent graph authority.

## Product roadmap

| Version | Outcome | Core boundary |
| --- | --- | --- |
| v0.1 | Read, understand, validate, and explain company context | Read-only Maysano access. Local drafts and evidence only. |
| v0.2 | Provide reusable local business-driven Data & AI product design | Deterministic DesignPortfolio, reusable skills, scenario packages, visual canvas, and reports. No Maysano write, approval, or production-readiness claim. |
| v0.3 | Create and revise governed company-graph objects | Maysano-approved, scoped graph changes through a narrow mutation contract. |
| v0.4 | Expose governed graph work to external agent clients | MCP tools over the same policy and mutation contracts. |
| v0.5 | Improve repeatable delivery and portfolio workflows | Reusable workflow packages, saved views, richer evidence, and measured learning. |

The roadmap is cumulative: each version retains the controls and evidence model introduced
earlier.

## v0.1 — read-only governed context

The v0.1 slice implements configuration validation, scoped synthetic and live read-only
retrieval, sourced portfolio briefings and dashboards, local governance/delivery-object
validation, deterministic policy evaluation, append-oriented evidence export, and no-write tests.
Existing MIT licence retained.

M0 is partially evidenced by the Maysano Platform API Client Integration Guide v1: the pilot
base URL, bearer-key authentication, GET-only resources, pagination, permissions, rate limit,
and no-store response policy are documented. Customer classification, retention policy, and
production-environment requirements remain platform-owner decisions. The SDK repository is
confirmed as [odp-agent-sdk](https://github.com/Open-Data-Product-Initiative/odp-agent-sdk);
adapter API and version selection remain pending.
M1 now includes an approved read-only pilot transport and ignored local credential file. Next:
secret-store integration, broader context analysis, remaining workflows, and SDK integration.
A static dashboard and conversational dashboard skill now support live pilot data; saved manager
views and automatic refresh remain pending.

Demo acceptance: one objective, two use cases and three products appear with relationships,
a decision, a risk and evidence; uc-2 has unknown ownership. Every source has an ID, version,
record timestamp and fixture reference. No cloud model is needed.

## v0.2 — reusable local business-driven Data & AI product design

### Goal

Provide reusable, deterministic local capabilities for designing and analysing connected business
objectives, use cases, AI products, and data products. The Udemy *Integrated Data & AI Product
Management* Masterclass is the first scenario package, not the definition of the product.

### Architecture

`kentaro.design` owns the portable `DesignPortfolio`, canonical Claims, typed many-to-many
relationships, validation, deterministic analysis, dependency manifests, stale-output detection,
local HTML canvas, reports, and pinned ODPS validation. The six skills under `.agents/skills/`
guide objective, use-case, AI-product, data-product, portfolio analysis, and readiness work using
that same engine. Scenario packages contain fixtures and teaching material only.

Generic `kentaro design` commands start blank unless the user explicitly selects a scenario.
`kentaro masterclass` remains a compatibility adapter for the Udemy banking scenario. A v0.2
`LearningPortfolio` migrates locally to `DesignPortfolio`; neither artefact is a Maysano record.

### Boundary and acceptance criteria

v0.2 is local design capability, not portfolio management. It stores only local artefacts under
`.kentaro/workspace/`; it does not read or write Maysano in the standard flow, process approvals,
execute agent actions, or certify production readiness. AI products remain distinct from data
products, and non-AI use cases use an explicit `ai_involvement` Claim.

Acceptance requires a generic non-banking scenario and the banking Masterclass scenario to use
the same engine, canvas, reports, manifests, and stale checks; all material claims retain
provenance and epistemic state; ODPS validates through `open-data-products==0.4.0`; and all paths
run without a network, credentials, Ollama, hosted model, or paid API.

---

## v0.3 — governed company-graph changes

### Goal

v0.3 will allow Kentaro to perform bounded changes to the Maysano company graph. This is a
material change from v0.1's read-only and local-artifact boundary. Maysano remains the system
of record and the enforcement point for tenant isolation, authority, graph persistence,
revocation, and audit. Kentaro does not receive general graph-write authority.

Each graph mutation must be attributable to a Maysano-authorised task and must use a narrowly
scoped, short-lived capability. Before Maysano applies a mutation, it must validate the active
authority, permitted graph scope and tool, expected record versions/preconditions, idempotency
key, and revocation state. The result must return a Maysano receipt and evidence reference.

### Task-scoped company-graph context cache

v0.3 adds a managed local context cache to reduce repeated Maysano reads during active governed
work. It is never a second system of record or a complete local copy of the company graph.
Maysano remains authoritative for graph state, tenancy, authority, revocation, audit, and
mutation acceptance.

Kentaro creates one task-scoped `ContextPackage` for each active Maysano Change Contract. The
package contains only the authorised graph projection required to form, evaluate, and implement
that contract:

- the active Change Contract;
- relevant objectives, use cases, and data products;
- authorised relationships, normally one or two graph hops from contract roots;
- linked decisions, risks, ownership, and evidence;
- record IDs, versions or ETags, source timestamps, and source references;
- retrieval scope and tenant/workspace boundary;
- cache creation and expiry times; and
- Maysano graph revision or sync cursor, when available.

The cache resides only in Kentaro's ignored local workspace. Kentaro does not synchronise or
persist the complete company graph by default. Cache data is unusable after its Change Contract
expires or is revoked, and retention, encryption, and purge behaviour must follow the verified
Maysano data-handling contract.

```text
Maysano graph
  -> retrieve authorised contract scope
  -> create local ContextPackage
  -> Kentaro performs local analysis, drafting, validation, and planning
  -> refresh changed graph records through delta synchronisation
  -> revalidate affected records before GraphChangeSet submission
  -> Maysano validates and persists the mutation
  -> Kentaro replaces local state with returned canonical records and receipt
```

### Harness2 assessment

[Harness2](https://github.com/google-research/harness2) is a useful source of harness-learning
patterns, not the v0.3 graph-execution substrate. Its editable components, contrastive
Propose–Probe–Compose loop, parallel and sequential exploration, and evidence-supported lessons
can improve the quality of Kentaro's agent profiles. Its documented unrestricted executor
network access and disabled Codex sandbox are not acceptable for a company-graph write path.

Kentaro will separate learning from execution:

```text
Learning plane (no Maysano graph writes)
candidate HarnessProfile
  -> isolated probe using synthetic or snapshotted context
  -> deterministic evaluation and human review
  -> versioned, provenance-linked learning record
  -> manually released HarnessProfile

Execution plane (Maysano-controlled graph mutation)
Maysano-authorised task + scoped short-lived capability
  -> approved HarnessProfile version
  -> retrieve current context and calculate proposed graph diff
  -> Maysano validates scope, preconditions, idempotency, and revocation
  -> one graph mutation
  -> Maysano receipt and evidence reference
```

An agent may propose a harness or profile improvement, but it must not self-promote changes to
its instructions, guardrails, skills, plugins, tools, permissions, or graph scope. A learning
result is never authority to mutate Maysano.

### Working drafts and canonical records

Kentaro creates local `WorkingDraft` artefacts before it submits a change. A draft supports agent
collaboration, review, validation, and explanation; it is not a company-graph record. It may
contain rationale, information needs, proposed data products, relationships, and unresolved
questions. Kentaro must submit an explicit, inspectable `GraphChangeSet`, never arbitrary model
state or a full local graph snapshot.

When Maysano accepts a `create` operation, it assigns the canonical graph ID, record version,
timestamps, ownership state, and audit reference. A local identifier is only a draft reference
until that acceptance.

Every update begins with current authorised context and an expected current record version. If
another actor changes a record first, Maysano rejects the stale request. Kentaro then retrieves
current context, recalculates the diff, and submits a new `GraphChangeSet`; it never overwrites
newer graph state from stale context.

### GraphChangeSet contract and first operations

`GraphChangeSet` is the v0.3 execution contract between Kentaro and Maysano. Each request binds
the Maysano authorising task; tenant and workspace; actor identity; approved `HarnessProfile`
version; source-context IDs, versions, and retrieval timestamps; proposed operations and target
IDs or draft references; expected versions; relationship changes; business rationale;
deterministic policy outcome; evidence references; idempotency key; and scoped capability
identifier and expiry.

The exact request shape, authentication mechanism, capability format, and receipt model must
come from the verified Maysano graph-mutation API contract. Kentaro must not invent them.

| Operation | Initial v0.3 scope |
| --- | --- |
| Create objective | An objective within an authorised workspace. |
| Create use case | A use case linked to approved decision-context or objective context. |
| Create data product | A record with required relationships and evidence. |
| Update object | Explicitly permitted fields on an authorised objective, use case, or product. |
| Add or remove relationship | An approved relationship, with evidence and preconditions. |
| Retire or supersede | Mark an object inactive or superseded while preserving history. |

Hard deletion stays outside v0.3 so portfolio history, decision context, and evidence remain
available.

### Write-time enforcement and corrections

Immediately before a mutation, Maysano must verify tenant and workspace boundary, actor
identity, active task authority, capability scope and expiry, permitted object types and
operations, target graph scope, expected versions and other preconditions, idempotency,
authoritative revocation, and required evidence or approval state. It returns accepted or
rejected status, canonical object IDs and versions, a mutation receipt ID, audit/evidence
reference, and a safe rejection reason where relevant.

Graph corrections and compensation use a new attributable change. They reference the original
receipt, affected canonical object versions, correction reason, authorising task and capability,
and the new supporting evidence or decision. Kentaro must not silently alter or erase its local
history after Maysano accepts a mutation.

### Profile-learning controls

`HarnessProfile` improvements may cover retrieval ordering, context selection, draft structure,
graph-change planning, evidence collection, ambiguity detection, escalation behaviour, and
explanation quality. They must not change task authority, capability scope, tenant access,
available tools, plugin permissions, approval requirements, Maysano validation rules, or
write-time policy controls.

Every candidate starts from a released profile version and runs only against synthetic tasks or
approved context snapshots, without a Maysano mutation capability. A versioned `LearningRecord`
captures candidate and baseline profile versions, fixture or snapshot IDs, task type, proposed
`GraphChangeSet` digest, policy result, quality scores, control violations, corrections or
rejections, reviewer decision, and release or rejection decision.

Profile-release measures include valid object and relationship structure, source and version
coverage, handling of unknown or conflicting context, human-correction rate, stale-context
detection, out-of-envelope attempts, policy violations, explanation quality, and time to an
approved draft. Better completion rate never justifies weaker escalation, broader access, or
reduced evidence.

### Delivery sequence

1. **Ratify the write contract.** Obtain a verified Maysano graph-mutation API contract,
   including tenant boundary, identity, capability format and lifetime, supported mutations,
   optimistic-concurrency/precondition semantics, idempotency, error model, receipts, audit
   references, and authoritative revocation. Do not invent any of these interfaces. The
   [Maysano maintainer requirements](maysano-v0.3-graph-mutation-requirements.md) define the
   requested contract inputs and test-environment deliverables.
2. **Define versioned execution objects.** Add `WorkingDraft`, `GraphChangeSet`,
   `GraphOperation`, `MutationReceipt`, `CorrectionRequest`, and `LearningRecord`. Bind each
   request to its authorising task, profile version, context versions, target scope,
   preconditions, idempotency key, and required evidence.
3. **Implement local draft workflows.** Create inspectable workflows for objectives, use cases,
   data products, relationships, and revisions. Each calculates a readable diff before it submits
   a request.
4. **Implement a narrow Maysano adapter.** It may submit only validated, explicitly supported
   graph mutations. It must have no generic HTTP escape hatch, no broad credential, and no
   fallback to a local or synthetic write.
5. **Enforce write-time controls in Maysano.** Re-check authority, scope, current record versions,
   tenant, capability expiry, and revocation immediately before each mutation. A locally allowed
   classification is insufficient.
6. **Record execution evidence.** Preserve the request/diff digest, profile and object versions,
   source IDs and timestamps, policy outcome, Maysano receipt, result versions, actor identity,
   and correction/compensation reference. Kentaro's local log remains supplementary rather than
   an authoritative audit record.
7. **Build graph-change evaluations.** Use synthetic or snapshot-based tasks to test valid
   creation and updates, source integrity, idempotent retry, stale-version rejection, concurrent
   changes, out-of-envelope requests, revoked authority immediately before dispatch, expiry, and
   secret/output redaction.
8. **Add the learning plane.** Evaluate candidate HarnessProfiles only in isolated non-mutating
   probes. Promote a profile only through named human review and a versioned release after it
   improves predefined quality measures without any control violation.

### v0.3 acceptance criteria

- No mutation is possible without a verified Maysano-issued task authority and scoped capability.
- Kentaro creates objectives, use cases, data products, and relationships only through a validated
  `GraphChangeSet`.
- Every update to an existing record has an explicit expected version; Maysano rejects stale
  updates without overwriting newer graph state.
- Every accepted mutation is idempotent, precondition-checked, tenant-bound, revocation-checked
  immediately before dispatch, and linked to a Maysano receipt.
- Every accepted mutation returns canonical Maysano object IDs and versions.
- Every rejected request explains the missing or violated constraint without exposing credentials
  or confidential graph content.
- Evaluation demonstrates zero out-of-envelope tool calls and zero unauthorised mutations across
  the defined synthetic/snapshot test suite.
- Candidate harness profiles never write to Maysano, alter their own controls, or gain authority
  through their own evaluation results.

### Explicit non-goals

v0.3 will not use Harness2 directly as the production graph-mutation runtime; allow benchmark
defaults such as unrestricted network access or disabled sandboxing; grant persistent broad graph
credentials to an agent; allow hard deletion of company-graph records; or treat agent reflection,
a successful probe, or a local evidence log as approval, platform audit, or permission to write.

---

## v0.4 — governed MCP access

### Goal

Expose Kentaro capabilities through MCP so Claude, Codex, OpenCode, and other compatible
assistants can work with the same governed context and graph-change model. MCP is a delivery
interface: it does not replace Maysano authority, the `GraphChangeSet` contract, or write-time
validation.

### Scope and acceptance criteria

Initial MCP tools map to existing Kentaro capabilities: retrieve authorised portfolio context;
list objectives, use cases, products, and relationships; create a local working draft; validate a
draft; calculate a graph diff; evaluate a proposed `GraphChangeSet`; submit an already authorised
`GraphChangeSet`; and retrieve mutation receipts and evidence references.

The server must expose separate read, draft, evaluate, and submit operations, not one opaque tool
that lets a model retrieve context and write arbitrary changes. MCP tools use the same local
policy controls and Maysano write-time contract as the CLI. Clients cannot bypass draft
validation, capability checks, version preconditions, or receipt capture; the same request must
produce equivalent policy outcomes through CLI and MCP paths.

---

## v0.5 — repeatable governed delivery

### Goal

Turn the validated v0.1–v0.4 building blocks into repeatable delivery workflows for portfolio
management and data-product work.

### Candidate scope

- reusable workflow packages for objective, use-case, and data-product lifecycle work;
- saved manager views and refresh governed by workspace settings;
- richer decision, risk, evidence, and correction views;
- packaged evaluation suites for customer environments;
- profile-release reporting and learning-quality trends; and
- Maysano workflow integration based on the production API and customer operating model.

This version begins only after the v0.3 contract has operated successfully with real authority,
receipts, concurrency, and correction flows.

## Architecture principles

1. **Maysano is authoritative.** Kentaro never substitutes local data, logs, or model output for
   platform state, authority, or audit.
2. **Draft before mutation.** Agents create readable local working drafts and explicit diffs before
   requesting a graph change.
3. **Authority is specific and temporary.** Every mutation has a named task, narrow scope,
   short-lived capability, and Maysano validation immediately before persistence.
4. **Versioning prevents silent overwrite.** Existing graph changes require expected versions;
   stale changes are rejected and recalculated.
5. **Learning is separate from execution.** Candidate profiles run in isolated probes. Learning
   never grants live authority.
6. **The execution surface stays narrow.** No generic HTTP escape hatch, broad credentials,
   unrestricted network access, or opaque one-step write tool.
7. **Evidence follows work.** Requests, diffs, sources, policy outcomes, receipts, corrections,
   and profile versions remain attributable.
8. **Model choice stays deployable.** Open Data Product SDK configuration selects local or cloud
   model execution; governance controls apply regardless of model choice.

## Near-term implementation decision

Run two bounded tracks. First, ratify the v0.3 Maysano graph-mutation contract before any
production graph-write implementation; that contract determines the adapter, capability model,
receipt design, and evaluation suite. Second, begin v0.2 with the synthetic course case and its
local teaching contract. The v0.2 companion must remain useful and fully testable without the
v0.3 API, graph-write rights, or a production Maysano environment.
