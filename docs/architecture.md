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

The selected SDK is [odp-agent-sdk](https://github.com/Open-Data-Product-Initiative/odp-agent-sdk), distributed as `open-data-products` (Apache-2.0). See [integration notes](sdk-integration.md). Runtime integration and version selection remain pending; model or tool execution is outside the v0.1 boundary.
