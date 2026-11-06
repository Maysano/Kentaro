# Changelog

## 0.2.11 — ODPC v1.1 AI-product delivery (6 November 2026)

- Pinned `open-data-products==0.5.0` and added ODPC v1.1 AI-product validation.
- Replaced private AI-product handover JSON and `Agent` graph nodes with the standard profile,
  catalog nodes, product reference, and ODPG `AIProduct` node.
- Added non-blocking, sourced ODPC input coverage and targeted user questions.

## 0.2.10 — Stateful business-design lifecycle (4 November 2026)

- Added explicit `auto`, `local`, and `graph_connected` design-session context modes.
- Added source-safe Maysano revalidation metadata and affected-design review markers; no graph
  payloads or snapshots are persisted.
- Added append-only local business-design decision events and lifecycle-stage state.
- Added readiness findings for advisory reuse candidates and unverified dependencies.
- Added a reusable customer risk-assessment end-to-end test, including an inspectable
  DesignPortfolio JSON, rendered HTML canvas, and final-handover ZIP fixture.
