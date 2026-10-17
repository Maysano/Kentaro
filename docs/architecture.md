# Architecture

Kentaro v0.1 is a read-only Agentic Maysano Harness. Its architecture separates
retrieval, local validation, deterministic evaluation, rendering, and local evidence
export from platform state and any future side effect.

```text
                    Maysano Platform
      portfolio state · approvals · graph · tenant controls · audit
                              │
                        read-only GET
                              │
CLI / Python API ──→ scoped ContextPackage ──→ briefs / dashboards / reports
         │                        │
         │                        └── source IDs, versions, timestamps
         │
         ├── local versioned-object validation
         ├── deterministic policy evaluation (no tool call)
         ├── revocation-clause validation and local simulation only
         └── append-oriented local evidence export
```

The core has no Codex dependency. Codex instructions live under `adapters/codex`.
Maysano remains authoritative for portfolio state, approvals, business-context graph
updates, tenant controls, and platform audit. Kentaro v0.1 does not write to any of
those concerns.

The live client uses an ignored local bearer-key file, HTTPS GET requests,
standard-library transport with verified TLS, no response cache, and source references
to documented external API resources. Fixture references use `demo:` identifiers and
cannot resolve to live records. The dashboard renderer uses the same scoped client and
emits a static HTML snapshot.

The local governance and delivery model is specified in
[governance and delivery object model](governance-and-delivery-object-model.md).
Its policy evaluator is deterministic: `allowed` means structurally in scope, never
permission to execute. Its evidence output is append-oriented, optionally
hash-chained for tamper indication, and is not an immutable or compliance-grade audit.

## Required revocation clause

Every future execution-capable agent or capability requires a versioned
`RevocationPolicy`. The revocation clause defines which prohibited or unsafe
behaviour suspends authority or credentials, and which named Maysano role can
suspend, restore, or narrow access. It is a required control.

Kentaro v0.1 validates local `RevocationPolicy` objects and exposes their local
validation status in review-readiness output. It does not hold credentials, suspend
live access, execute actions, submit requests, or enforce a live policy state. A
local simulated suspension can deny a proposed request's structural classification;
it is not an external dispatch or credential operation.

For a future write path, Maysano owns authoritative revocation state, credentials,
enforcement, retention, and audit evidence. A verified Maysano suspension must take
effect before the next external action, including disabling relevant credentials or
execution permissions in an emergency. Restoration requires a new versioned decision
record bound to the request version, payload/diff digest, authority chain, rationale,
evidence, scope, timestamp, expiry, and named authority. A suspended agent must not
resume from cached authority.

The selected SDK is [odp-agent-sdk](https://github.com/Open-Data-Product-Initiative/odp-agent-sdk), distributed as `open-data-products` (Apache-2.0). Its optional local drafts align with the [Open Data Products (ODPS) family of specifications](https://opendataproducts.org/). See [integration notes](sdk-integration.md). Runtime integration and version selection remain pending; model or tool execution is outside the v0.1 boundary.
