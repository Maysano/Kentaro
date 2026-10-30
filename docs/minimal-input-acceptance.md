# Minimal-input business-design acceptance test

This test covers only Kentaro's local `DesignPortfolio` workflow. It does not retrieve business
data, call an LLM service, write Maysano, process approvals, or establish implementation readiness.

## Baseline before this change

The prior workflow had `design init`, `add-object`, `add-relationship`, and `set-claim`, but no
operation that accepted a business problem statement. It could not execute Tests A through D from
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
three documented problem frames used here: government permit-service delay, finance
monthly-report reconciliation, and customer risk-assessment delay. Other input receives one
focused framing question, rather than an invented domain or objective.

The supplied sentence is stored as `user_confirmed`. All generated objects, relationships,
alternatives, KPIs, capabilities, and next actions are `proposed` or `unknown`, with a
hash-derived source reference to that sentence. The operation uses the existing canonical
portfolio, analysis, readiness, rendering, and reporting paths; it does not put generative facts
into the deterministic engine. Each recognised pattern offers a non-AI path plus a proposed,
human-controlled AI-product option. The AI option is never a confirmed requirement, cannot make
or approve a business decision, and must be assessed against the non-AI path.

## Results after the change

All runs used one business-owner message, no fixture, no external service, and no manual
schema/CLI operation by the business owner.

| Test | Frame | Messages | Questions | Concepts | Alternatives | Unsupported facts | Connected portfolio | Result |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| A — permit processing | `permit_service` | 1 | 1 | 8 | 2 | 0 | Yes | Objective, three use cases, three scoped information products, and a human-in-the-loop evidence-review assistant |
| B — ambiguous AI | `needs_context` | 1 | 1 | 3 | 0 | 0 | Yes, provisional | Does not invent an industry or AI product; records that AI suitability must be assessed after process, user group, and outcome are known |
| C — finance reconciliation | `finance_reconciliation` | 1 | 1 | 6 | 2 | 0 | Yes | Objective, two use cases, reporting-input and exception-context products, data-quality/automation-first path, and a human-in-the-loop investigation assistant |
| D — customer risk assessment | `customer_risk_assessment` | 1 | 1 | 6 | 2 | 0 | Yes | Objective, assessment-preparation use case, three proposed customer-risk domain products (identity/profile, due-diligence evidence, and assessment case), and a human-in-the-loop preparation assistant |

For Tests A, C, and D, readiness remains at discovery: open source authority, access, ownership,
data-quality, and rule questions are traceable design gaps or decision dependencies, not
implementation-blocker claims. Test B intentionally keeps every domain-specific detail and AI
product unresolved until the business owner supplies the missing context.

## Remaining limit

This is not open-ended autonomous discovery. Extending the operation needs a documented,
cross-sector pattern, explicit proposed/unknown wording, and acceptance tests. The current
proposal engine deliberately does not call an LLM. Kentaro's existing provider integration only
generates optional ODPS-family drafts; it is not a DesignPortfolio suggestion service. Adding
LLM-assisted business-design suggestions requires a separate provider-routing, data-egress,
prompt-versioning, provenance, and human-review design before it can be enabled.
