# Changelog

## 0.2.13 — Local context assessment (14 November 2026)

- Added `kentaro context assess` for local UTF-8 Markdown and text sources.
- Added source-line evidence for seven context-readiness dimensions, maturity
  indicators, intended-use target levels, and suggested review cases.
- Added non-overwriting JSON and Markdown local reports plus the fourteenth
  Kentaro Codex skill.
- The feature is an indicator scan only: it does not use a model or service,
  interpret visual files, establish approval or compliance, or mutate Maysano.

## 0.2.12 — Business decision impact assessment (14 November 2026)

- Added local, deterministic business-assumption change records and decision impact assessment.
- Decisions can snapshot their supporting assumption assessments and explicitly resolve a later
  reassessment without changing historical resolutions.
- Added `kentaro design record-assumption-change`, `assess-impact`, and `impact-report`.
- Material unresolved assumption changes now surface in readiness, reports, canvas inspection,
  decision context, and final-handover gating. These remain advisory local workflow controls and
  never create Maysano mutations or approvals.

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
