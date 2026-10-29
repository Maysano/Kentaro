---
name: kentaro-use-case-design
description: Translate local DesignPortfolio objectives into business use cases while preserving consumers, decisions, constraints, success criteria, and explicit AI involvement. Use for design work, not execution planning.
---

# Kentaro Use Case Design

Start from one or more local objectives. Ask what user or consumer makes which decision, which
workflow changes, what value is expected, which constraints apply, and how success is assessed.
Record every supplied or missing fact as a canonical Claim; do not infer AI involvement.

When the owner gives only a short problem statement, propose plausible workflow options as
`proposed`, explain that they are candidate use cases rather than local facts, and identify the
most consequential uncertainty. Do not turn one broad statement into a questionnaire: keep the
first proposal connected and ask at most one focused next question when it would change the
priority or decision boundary.

Use `ai_involvement` on a use case as a Claim. It can explicitly be `none`: non-AI use cases are
valid. Link each supported use case with `use-case-supports-objective`, validate the portfolio,
and keep implementation decisions outside Kentaro's local design scope.
