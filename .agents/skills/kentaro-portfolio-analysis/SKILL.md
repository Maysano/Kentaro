---
name: kentaro-portfolio-analysis
description: Analyze a local DesignPortfolio for typed relationships, reuse, dependencies, ownership gaps, conflicts, and unresolved decisions. Use for deterministic portfolio design analysis, not authoritative portfolio management.
---

# Kentaro Portfolio Analysis

Run `kentaro design validate` before `kentaro design analyze`. Explain relationship and reuse
findings as local analysis based on the supplied design artifact. Identify missing capabilities,
owners, dependencies, and unresolved decisions without promoting assumptions to facts.

Keep data-product qualification, reuse, and operational readiness separate. Qualification checks
purpose/value, one or more identified consumers, a consumer-oriented boundary, a recognizable
consumption capability, ownership/lifecycle proposal, and intended interface/service model.
Reuse reports confirmed and proposed consumers, possible cross-use-case reuse, shared
capabilities, and constraints; it must not reject a one-consumer design. Treat missing ownership
or boundary choices as explicit decision dependencies, not evidence that the product concept is
invalid.

Use the recorded `assessment_stage` (discovery by default) or an explicit `--assessment-stage`
override for analysis. Explain findings as design gaps, decision dependencies, or implementation
blockers according to the requested lifecycle stage; do not relabel all unknown claims as
blockers.

When reviewing a minimal-input proposal, confirm that every generated object and relationship is
labelled `proposed` or `unknown` unless the business owner supplied it directly. Evaluate whether
the connected design, alternatives, and first focused question are useful; do not equate a high
object count with a useful portfolio.

When a relationship is semantically invalid, correct the local design with the supported typed
predicate rather than inventing a new relationship meaning. Do not read or change Maysano unless
the user separately requests and configures a read-only workflow.
