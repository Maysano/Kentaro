---
name: kentaro-portfolio-readiness
description: Generate deterministic local DesignPortfolio readiness, canvas, executive summary, and stale-output status. Use for evidence-labelled reporting, not production certification.
---

# Kentaro Portfolio Readiness and Reporting

At the beginning of an engagement, create or locate the local DesignPortfolio.
After every user interaction, incorporate any relevant information, save and
validate the portfolio, then run `kentaro design engagement refresh --input
<portfolio>`. Read `engagement-state.json` before
choosing the next response. It is a generated index of the authoritative
portfolio, recording required final deliverables, confirmed/proposed/unknown
claim counts, missing structural requirements, unresolved human decisions, and
the next discovery question. Never use the state file as an alternative source
of truth or rely on conversation history alone.

Start every engagement by making the context mode explicit. `graph_connected` requires a successful
live Maysano read before graph-grounded reasoning; if it fails, report `source_unavailable` and ask
the user to retry, configure Maysano, or explicitly switch to local design. `auto` may continue as
local-unverified; `local` never claims graph verification. The local state records only safe graph
provenance, revision/comparison metadata, and whether revalidation is required—not a cached company
graph. Run `kentaro design refresh-context --input <portfolio>` when verification is requested and
allow final handover to refresh the authoritative Maysano context. Keep a graph-connected handover
gated when retrieval is unavailable or changed evidence requires reconsideration.

The refresh is a complete evaluation: preserve confirmed decisions unless the
user explicitly corrects them; validate the mandatory Design Skeleton, KPI
targets, links, and dependencies; assess changed and impacted objects and
relationships; flag stale outputs for reconsideration; and select the
highest-priority unresolved topic. Answer the user's immediate request first.
Do not turn discovery gaps into a mandatory sequence of questions: a proposed
package may be generated and reviewed with unresolved topics. Ask one targeted
next question only when the learner asks to refine the design, assess readiness,
or choose a next design action. Never use a fixed question sequence or assume a
previous output remains current after an input change.

Do not report final completion until the state records complete objectives and
business KPI targets, connected use cases, data products and product KPI
targets, plus generated and validated ODPS, ODPC, and ODPG artifacts. Proposed
values can support a provisional design, not business approval. Human review
and confirmation are required before final local handover generation.

Generate outputs with `kentaro design render`, `report`, and `status` from the same validated
local DesignPortfolio. The outputs distinguish confirmed claims, assumptions, proposals, unknowns,
and their sources. Regenerate reports after a material input change; the dependency manifest and
stale status show when an output is no longer current.

Open the rendered canvas beside the Codex conversation by default as soon as an initial proposal
exists; a link alone is not the learner experience. After every material design update, regenerate
the same adjacent `canvas.html` from the saved portfolio and refresh or reopen it in Codex. Keep
that visual view available alongside the conversation so it reflects the latest design rather than
a stale snapshot.

Use the recorded `assessment_stage` (new portfolios default to `discovery`) or an explicit
`--assessment-stage discovery|design|implementation|operation` override. Every deterministic
finding has a stable ID, affected object, category, severity, assessment stage, explanation,
required resolution, and available claim/dependency references. Group output by category and
priority, retain complete JSON detail, and keep executive summaries aggregated and concise.

Classify missing discovery information as a **design gap**; classify unresolved accountable
business, product, or governance choices as a **decision dependency**; classify conditions that
would prevent safe proposed implementation or operation as an **implementation blocker**. The
same unverified rule can be a design gap during discovery and an implementation blocker when
automatic execution is proposed. Deduplicate the same underlying issue. Frame readiness findings
as decisions for accountable humans. Never claim approval, compliance, business value, data
availability, safety, or production readiness from a valid schema or report.

Use the portfolio's append-only `decisions` register for material human choices. Present alternatives,
recommendation consequences, and source evidence first; record a decision only after explicit human
input with `kentaro design record-decision`. A later change must supersede the earlier decision rather
than overwrite it. AI recommendations, lexical reuse candidates, and inferred dependencies never become
human decisions or established organizational facts on their own.

For an initial minimal-input proposal, retain unknowns as discovery-stage gaps and decisions, then
give a concise executive summary, canvas, and suggested review package without waiting for
confirmation. A valid canvas or report proves only that the local proposal was rendered from the
saved portfolio, not that the proposal is true or ready to implement.
