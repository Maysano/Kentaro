---
name: kentaro-masterclass
description: Guide the local Integrated Data and AI Product Management Masterclass workflow when a learner wants to work from the synthetic case, update a LearningPortfolio, render its canvas, validate its ODPS fixture, or generate course reports. Do not use for live Maysano portfolio work.
---

# Kentaro Masterclass Companion

Use the Udemy scenario package on the reusable deterministic design engine. It is a learning
exercise, not a Maysano portfolio editor or approval process.

1. Start with `kentaro masterclass init` unless the learner supplies an existing local
   `DesignPortfolio` JSON file. The legacy command explicitly selects the Udemy banking scenario;
   generic work should use `kentaro design` without a scenario default.
2. Keep AI products distinct from data products. Preserve every Claim's status,
   source ID, revision, asserted timestamp, and derivation-input hash. Never
   convert `proposed`, `assumed`, or `unknown` into a confirmed fact.
3. Ask for an accountable owner, measurable KPI baseline, source evidence, dependency,
   lifecycle status, or decision whenever the learner needs one and it is absent. Record
   the response as `user_confirmed` only after the learner explicitly confirms it; otherwise
   leave the claim as `unknown`, `assumed`, or `proposed`.
4. Model the supported objective-to-use-case relationship as
   `use-case-supports-objective`, then model AI-product and data-product dependencies.
   Do not add a relationship whose meaning or endpoints are not represented by the local
   course schema.
5. Validate before rendering or reporting: `kentaro masterclass validate --input <portfolio.json>`.
6. Render and report from the same portfolio file. Use `kentaro masterclass render`,
   `report`, and `status`; do not hand-edit generated HTML or reports.
7. Validate the supplied ODPS exercise with `kentaro masterclass validate-odps`.
   Schema validity is not evidence of data availability, compliance, safety,
   approval, or production readiness.

The standard workflow uses only synthetic local fixtures and does not need a
Maysano account, Maysano API access, a hosted model, or Ollama. A learner may
use a Codex conversation to discuss changes, but human review is required before
marking any claim `user_confirmed`.
