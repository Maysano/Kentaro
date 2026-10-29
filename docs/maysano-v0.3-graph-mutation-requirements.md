# Maysano v0.3 graph-mutation requirements for Kentaro

**Status:** Proposal for Maysano maintainer review. It is not an API contract, approval, or
implementation authorisation.

## Decision requested

Maysano must provide a narrowly scoped, governed company-graph mutation capability that Kentaro
can use for one authorised task at a time. It must not expose a general-purpose graph-write API
or a persistent broad credential to an agent.

Kentaro will prepare local working drafts, calculate explicit graph changes, validate them
locally, and present the confirmed Maysano result. Maysano remains authoritative for graph state,
tenant isolation, authority, revocation, persistence, and audit.

## Required Maysano deliverables before Kentaro implements a write adapter

| # | Deliverable | Required content | Kentaro dependency |
| --- | --- | --- | --- |
| 1 | Versioned mutation API contract | OpenAPI/schema, endpoint(s), authentication, request/response objects, errors, and versioning policy. | Kentaro cannot implement or test an adapter without it. |
| 2 | Task-authority model | Task lifecycle, issuer, actor identity, tenant/workspace binding, permitted operations, graph scope, required evidence, expiry, and revocation. | Kentaro must bind every change set to this authority. |
| 3 | Scoped capability format | Claim semantics, signing/validation, audience, lifetime, replay protection, revocation behaviour, and transport. | Kentaro must not infer claims or persist the capability. |
| 4 | Graph-change semantics | Supported v0.3 object types, fields, operations, relationship rules, validation, atomicity, and lifecycle behaviour. | Kentaro must constrain drafts and diffs to the supported surface. |
| 5 | Concurrency and idempotency contract | Record-version representation, precondition evaluation, stale-write response, idempotency key lifetime, retry result, and duplicate handling. | Kentaro must generate safe diffs and recover predictably. |
| 6 | Receipt and audit contract | Accepted/rejected response, canonical IDs and versions, receipt ID, audit/evidence reference, safe rejection reason, and retrieval method. | Kentaro must show confirmed outcomes rather than infer success. |
| 7 | Correction model | How to correct or compensate an accepted change while preserving history and linking the original receipt. | Kentaro must propose a new attributable correction, never overwrite history. |
| 8 | Contract-test environment | Non-production tenant, seeded fixtures, test identities/capabilities, controllable expiry/revocation/version conflicts, and receipt inspection. | Kentaro must run contract and adversarial tests before production use. |
| 9 | Authorised context and delta-sync contract | Task-scoped graph projection, permitted hops and record types, graph revision or sync cursor, delta response, cache-expiry signal, and revalidation endpoint or semantics. | Kentaro must cache only authorised context and revalidate before a write. |

## Required v0.3 write boundary

Maysano must accept a single explicit **GraphChangeSet**, not arbitrary model output, a full graph
snapshot, or generic record-level CRUD access. Its exact field names and wire format are Maysano
design decisions; the contract must represent at least:

- authorising task identifier;
- tenant and workspace boundary;
- actor identity;
- requested operations and their canonical target IDs or client draft references;
- expected versions and other mutation preconditions;
- source/context references used to make the proposal;
- business rationale and evidence references;
- idempotency key;
- scoped capability reference and expiry; and
- the approved Kentaro `HarnessProfile` version used to generate the proposal.

Kentaro requires an explicit result for the whole change set: accepted, rejected, or another
documented terminal state. The result must contain canonical object IDs and versions when changes
are accepted.

## Task-scoped context and delta synchronisation

Maysano must enable a task-scoped authorised context projection for each active Change Contract.
This is the input to Kentaro's local `ContextPackage` cache, not permission to retrieve or copy
the whole company graph. The Maysano contract must specify:

- how Kentaro identifies the active Change Contract and retrieves its authorised projection;
- the tenant and workspace boundary, allowed record types, contract roots, and maximum graph-hop
  scope;
- record IDs, canonical versions or ETags, source timestamps, source references, and linked
  decisions, risks, ownership, and evidence that may be returned;
- cache expiry, invalidation, and behaviour after Change Contract expiry or revocation;
- graph revision or sync cursor semantics, when supported;
- a delta-sync request and response for records that changed since a known revision or cursor;
- how a missing, expired, or unavailable cursor is represented; and
- the revalidation operation or semantics Kentaro must use immediately before a
  `GraphChangeSet` submission.

Kentaro will retain this data only in its ignored local workspace for active governed work. It
will not synchronise the complete company graph by default, continue to use a cache after contract
expiry or revocation, or treat cached context as authoritative graph state.

## Initial allowed operations

Keep the initial mutation surface deliberately narrow.

| Operation | v0.3 requirement |
| --- | --- |
| Create objective | Only within the authorised workspace. |
| Create use case | Only with authorised objective or decision-context linkage. |
| Create data product | Only with required relationships and evidence. |
| Update object | Only permitted fields on an authorised objective, use case, or data product. |
| Add or remove relationship | Only allowed relationship types within authorised scope; removal requires preconditions and evidence. |
| Retire or supersede | Preserve object history rather than deleting it. |

Hard deletion is outside v0.3.

## Maysano write-time checks

Immediately before persistence, Maysano must enforce all of the following independently of
Kentaro's local evaluation:

1. Tenant and workspace boundary.
2. Actor identity and authorised task state.
3. Capability validity, audience, scope, expiry, and replay protection.
4. Allowed object types, fields, operations, and target graph scope.
5. Current record versions and every declared precondition.
6. Idempotency and duplicate submission handling.
7. Authoritative revocation and emergency suspension state.
8. Required evidence and approval state.
9. Graph and relationship integrity rules.

A locally `allowed` Kentaro result is never sufficient permission to persist a change.

## Concurrency, atomicity, and correction decisions

Maysano must decide and document these before an adapter is built:

1. **Atomicity:** whether a multi-operation `GraphChangeSet` is all-or-nothing or can partially
   succeed. Kentaro recommends all-or-nothing for v0.3.
2. **Optimistic concurrency:** the canonical record-version format and the exact stale-write
   response. Maysano must reject stale updates rather than apply them over newer state.
3. **Idempotency:** the idempotency-key scope, retention, conflict behaviour, and how a retry
   retrieves the first result.
4. **Corrections:** how a new change references the original receipt and preserves history.
5. **Relationship constraints:** the allowed types, directionality, cardinality, cross-workspace
   prohibition, and lifecycle constraints.

## Receipt, audit, and safe failure requirements

For each request, Maysano must provide:

- accepted or rejected status;
- canonical IDs and versions for accepted records;
- mutation receipt ID;
- authoritative audit or evidence reference;
- correlation ID for support and reconciliation; and
- a safe rejection reason that does not disclose credentials or confidential graph data.

The authoritative Maysano audit record should associate task, actor, tenant/workspace, capability
identity, request/diff digest, evaluated preconditions, decision, timestamps, resulting versions,
and correction links. Kentaro's local evidence export is supplementary only.

## Revocation and operational controls

Maysano must provide authoritative revocation that takes effect before the next mutation. An
emergency suspension must disable outstanding capabilities and reject further submissions. The
maintainer must define operational ownership, alerting, incident response, rate limits, service
identity rotation, capability-key rotation, and reconciliation for interrupted submissions.

## Contract-test requirements

The Maysano test environment must allow Kentaro to prove all of the following:

- a valid creation and update receive canonical IDs, versions, and receipts;
- a stale update is rejected and does not overwrite newer graph state;
- duplicate submission returns the documented idempotent result;
- an out-of-scope object, field, relationship, or workspace is rejected;
- expired and revoked capabilities are rejected immediately before dispatch;
- an invalid or missing evidence/approval requirement is rejected;
- confidential data and credentials do not appear in safe errors or receipts;
- correction creates an attributable new change rather than rewriting history; and
- cross-tenant attempts are rejected.

## Explicit exclusions

This requirement does not ask Maysano to:

- grant a persistent broad graph credential to Kentaro or an agent;
- expose generic graph CRUD, a generic HTTP escape hatch, or opaque one-step agent writes;
- accept local agent reflection, a successful probe, or a Kentaro evidence log as approval;
- rely on Kentaro for authoritative tenant controls, revocation, or audit; or
- support hard deletion in v0.3.

## Maintainer response template

Please return the following machine-readable contract inputs or their authoritative locations:

```text
mutation_api_contract: <OpenAPI/schema URL and version>
task_authority_contract: <schema URL and version>
capability_contract: <claim schema, audience, expiry, revocation semantics>
supported_operations: <object types, fields, relationships, lifecycle rules>
atomicity: <atomic | partial, with documented semantics>
concurrency: <record version and precondition semantics>
idempotency: <scope, retention, retry and conflict semantics>
context_projection_contract: <scope, roots, hops, cache expiry and invalidation semantics>
delta_sync_contract: <revision/cursor format, request/response, unavailable-cursor behaviour>
write_revalidation_contract: <required current-record or scope validation before submission>
receipt_contract: <response schema and retrieval endpoint>
audit_contract: <reference format, retention, access model>
correction_contract: <supersede/compensate semantics>
test_environment: <base URL, test tenant provisioning, contract-test process>
security_operations: <identity, rotation, rate limits, incident and revocation owner>
```

Kentaro implementation begins only after these contracts are verified and a test environment is
available.
