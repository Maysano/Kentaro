# Minimal-input business-design acceptance test

This test covers only Kentaro's local `DesignPortfolio` workflow. It does not retrieve business
data, call an LLM service, write Maysano, process approvals, or establish implementation readiness.

## Baseline before this change

The prior workflow had `design init`, `add-object`, `add-relationship`, and `set-claim`, but no
operation that accepted a business problem statement. It could not execute Tests A, B, or C from
their specified single input. The comparable generic permit test required at least 13 manual CLI
operations: initialise, six objects, and six relationships.

| Measure | Before |
| --- | --- |
| Business-owner messages accepted as input | 0 |
| Clarification questions | 0 |
| Business concepts and alternatives proposed | 0 |
| Unsupported factual claims | 0 |
| Valid connected portfolio, canvas, reports from supplied sentence | No |
| Practical next step | No |

The limitation was skill orchestration and the missing minimal-input operation, not validation,
reporting, provenance, or canvas generation.

## Change under test

`kentaro design propose` is a bounded deterministic orchestration operation. It recognises only the
two documented problem frames used here: government permit-service delay and finance
monthly-report reconciliation. Other input receives one focused framing question, rather than an
invented domain or objective.

The supplied sentence is stored as `user_confirmed`. All generated objects, relationships,
alternatives, KPIs, capabilities, and next actions are `proposed` or `unknown`, with a
hash-derived source reference to that sentence. The operation uses the existing canonical
portfolio, analysis, readiness, rendering, and reporting paths; it does not put generative facts
into the deterministic engine.

## Results after the change

All runs used one business-owner message, no fixture, no external service, and no manual
schema/CLI operation by the business owner.

| Test | Frame | Messages | Questions | Concepts | Alternatives | Unsupported facts | Connected portfolio | Result |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| A — permit processing | `permit_service` | 1 | 1 | 6 | 2 | 0 | Yes | Objective, three use cases, proposed AI review support, shared candidate data product, canvas and reports |
| B — ambiguous AI | `needs_context` | 1 | 1 | 0 | 0 | 0 | No, by design | Does not invent an industry, process, or objective; asks for process, user group, and outcome |
| C — finance reconciliation | `finance_reconciliation` | 1 | 1 | 4 | 2 | 0 | Yes | Objective, two non-AI use cases, reconciliation data product, data-quality/automation-first path, and AI deferred pending evidence |

For Tests A and C, readiness remains at discovery: open source authority, access, ownership,
data-quality, and rule questions are traceable design gaps or decision dependencies, not
implementation-blocker claims. Test B intentionally makes no connected design.

## Remaining limit

This is not open-ended autonomous discovery. Extending the operation needs a documented,
cross-sector pattern, explicit proposed/unknown wording, and acceptance tests.
