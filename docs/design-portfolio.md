# Local DesignPortfolio

## Connected company-graph context

`kentaro design propose` has explicit context modes. `auto` is the compatible default: it uses a
configured Maysano read connection when available and otherwise creates a visibly local,
unverified design. `local` never attempts graph verification. `graph_connected` requires a
successful live Maysano read before Kentaro represents the design as graph-grounded; on failure it
remains `source_unavailable` with a retry/configure/switch-to-local next action. Existing records
remain sourced context, while every new DesignPortfolio object remains proposed or unknown until a
human confirms it.

```shell
kentaro design propose --context-mode graph_connected \
  --business-input "Reduce customer risk-assessment delays." \
  --output .kentaro/workspace/design/risk.json
kentaro design refresh-context --input .kentaro/workspace/design/risk.json
```

The live API's `Cache-Control: no-store` policy means the full graph is held only for the
active operation. Kentaro stores only context provenance (source, scope, retrieval time,
coverage counts, and limitations) in the ignored local design workspace, not a cached
company graph. Kentaro retains source references, record revisions when supplied, retrieval
times, verification state, and comparison results. The operation identifies lexical candidates
for reuse or overlap and requires
their consumer, boundary, authority, access, quality, and service suitability to be evaluated;
a candidate does not prove equivalence or duplication. If context is unavailable, local design
continues with an explicit unverified status. A connected Maysano design is freshly re-read
before final handover export; unavailable revalidation keeps that export gated. A changed source
revision marks only affected local reuse/dependency conclusions as `stale` for review; it never
discards the DesignPortfolio or its decision history. The stale state remains a handover gate until
a linked, explicit human decision records the reconsideration.

## Human decision register and lifecycle state

`DesignPortfolio` schema v3 adds an append-only local `decisions` register. A decision is a
business-design event, not an approval or authenticated identity record. It stores its supplied
actor label, subject, scope, alternatives, resolution, rationale, evidence references, related
objects, timestamp, source portfolio revision, and optional superseded decision ID. A later
decision supersedes an earlier event without changing the earlier event.

```shell
kentaro design record-decision --input .kentaro/workspace/design/risk.json \
  --id risk-scope-v1 --subject "First risk-assessment scope" --scope "Retail pilot" \
  --alternative "Rules-first" --alternative "Human-in-the-loop assistant" \
  --resolution "Start with rules-first" --rationale "Evidence coverage is incomplete" \
  --evidence-reference "maysano:/products/risk-context" --actor "Business Owner"
```

The regenerated `engagement-state.json` presents seven flexible lifecycle stages: establish
context, define business intent, assess existing capabilities, develop alternatives, formalize the
design, validate and decide, and prepare handover. Each exposes completion state, outstanding
requirements, evidence, unresolved decisions, and a recommended next action. These are guidance
and completion gates, not a rigid conversational wizard: incomplete local drafts remain editable.

## Decision Context and delivery handover

`kentaro design propose` automatically creates a local **suggested design review package** from a
validated DesignPortfolio. It is immediately available for review and evaluation, including when
the design still has unknowns and open decisions. No approval, named reviewer, or confirmation is
needed to receive or discuss it. `kentaro design handover prepare-review` creates the same type of
review material for an existing DesignPortfolio. After the user explicitly confirms the scope and
acknowledges every unresolved decision,
`kentaro design handover generate` creates a standalone ZIP. The ZIP captures its Decision
Context, source portfolio, relationships, canvas, provenance inventory, readiness findings,
delivery brief, and draft AI-product definitions. It does not create a Maysano record, request or
grant approval, authorize implementation, or establish production readiness.

All inputs and package directories must remain below `.kentaro/workspace/`:

```bash
kentaro design handover prepare-review \
  --input .kentaro/workspace/design/permit-service.json \
  --output .kentaro/workspace/design/permit-service/review-v1
kentaro design handover generate \
  --input .kentaro/workspace/design/permit-service.json \
  --output .kentaro/workspace/design/permit-service/handover-v1.zip \
  --reviewer "Reviewing user" \
  --confirmation "I confirm this handover is ready for its intended builder." \
  --acknowledge-open-decisions
kentaro design handover validate \
  --package .kentaro/workspace/design/permit-service/handover-v1.zip
kentaro design handover status \
  --input .kentaro/workspace/design/permit-service.json \
  --package .kentaro/workspace/design/permit-service/handover-v1.zip
```

The `decision-context.yaml` and `relationships.yaml` files use JSON-compatible YAML to keep
the portable core dependency-free. Package validation checks hashes for generated artefacts;
handover status additionally detects a changed portfolio revision or content hash. Neither is
an approval or readiness verdict.

Final reviewed ZIP exports include deterministic ODPS data-product definitions, an ODPC catalog,
and an ODPG relationship graph when structural completion succeeds. The pinned SDK validates each
artifact. Draft review material instead records missing KPI, relationship, capability, quality,
access, and service information as targeted discovery questions; it does not invent values merely
to enable a formal export.

Kentaro v0.2 provides a reusable, deterministic local business-design capability. A
`DesignPortfolio` is not Maysano's portfolio, a governance object, a request for approval, or a
production system. It is a structured local artefact kept beneath `.kentaro/workspace/`.

## Generic workflow

```shell
kentaro design init --title "Service Transformation" --portfolio-id service-transformation --output .kentaro/workspace/design/service-transformation.json
kentaro design add-object --input .kentaro/workspace/design/service-transformation.json --id objective-speed --kind objective --name "Faster service" --purpose "Reduce avoidable waiting" --owner "Service owner" --lifecycle-status proposed
kentaro design validate --input .kentaro/workspace/design/service-transformation.json
kentaro design analyze --input .kentaro/workspace/design/service-transformation.json
```

For a bounded first-pass proposal from a business owner's short problem statement, use:

```shell
kentaro design propose --business-input "Our finance team spends too much time reconciling monthly reports from different systems. We want faster reporting and fewer discrepancies." --output .kentaro/workspace/design/finance.json
```

`propose` is deterministic and supports only documented problem frames: government permit-service
delay, finance monthly-report reconciliation, and customer risk-assessment delay. It records the supplied
input as `user_confirmed` and every generated object, relationship, alternative, and capability as
`proposed` or `unknown`; it never calls a model or treats a pattern as local business fact. It also
writes the canvas, executive summary, readiness report, and unresolved-decision report beside the
saved portfolio. When the input is too ambiguous, it writes a valid context-framing portfolio with
one focused clarification question instead of inventing an industry or objective.
Every recognised initial proposal also writes a suggested review package below its generated output
directory. This package is for discussion and evaluation; its unresolved topics do not block it.

Recognised patterns aim for two or three consumer-scoped, domain- or subdomain-oriented candidate
data products rather than one unbounded catch-all product. A workflow step, screen, report, or
worklist is not by itself a data-product boundary. Each candidate must be refined against a distinct
business-domain boundary, accountable domain owner, authoritative sources, and reuse hypothesis.
They also include a proposed, human-in-the-loop AI-product option alongside a non-AI alternative
when the pattern supplies a credible bounded role. That is a design option, not an AI requirement:
human users retain decisions and approvals, and an AI candidate
must have explicit oversight, evaluation criteria, prohibited actions, and supporting information
boundaries before it can progress.

Add typed use-case, AI-product, and data-product relationships with `add-object` and
`add-relationship`. `set-claim` records a sourced claim on either an object or the portfolio.
Every material attribute is a canonical Claim, including nested business-information groups.

## Model and boundaries

The model supports multiple objectives, multiple use cases per objective, reuse of AI and data
products, independent owners and lifecycle states, and use cases with `ai_involvement: none`.
Validation enforces semantic relationship endpoints, Claim provenance, and append-only decision
references. Readiness reports additionally distinguish graph verification state, advisory reuse
candidates, and local or inferred dependencies from verified graph relationships. New portfolios record
`assessment_stage: discovery`; reports and canvas rendering can use that stage or an explicit
`--assessment-stage` override for discovery, design, implementation, or operation.

Data-product qualification, reuse and operational readiness are deliberately independent. A
candidate product needs a purpose/value proposition, one identified consumer, a consumer-oriented
boundary, consumption capability, and an intended interface/service model. More consumers improve
reuse but do not make a one-consumer product invalid. Missing ownership, contracts, access, or
operating controls remain visible as a decision dependency or readiness gap; they do not turn a
well-specified concept into a dataset by definition. The assessment language distinguishes an
information requirement, candidate data capability, candidate data product, qualified design
concept, implementation-ready product, and operational data product.

Readiness findings are lifecycle-aware and machine-readable: design gaps identify information to
investigate, decision dependencies identify accountable human choices, and implementation blockers
identify conditions that prevent safe implementation or operation. The generated local canvas has
an executive relationship graph and selected-object inspection panel. It exposes full claims,
provenance, unresolved information and findings only on selection, while keeping the overview
compact and business-readable.

Where a portfolio needs to compare proposed architectures, its optional `design_alternatives`
list can name each alternative, its `object_ids`, and `shared_object_ids`. The canvas then shows
the alternatives without implying that an AI product belongs to a conventional path merely because
both paths use the same data product.

The standard `kentaro` package includes the pinned
`open-data-products==0.5.0` adapter to validate local ODPS artifacts and ODPC v1.1 AI-product profiles. An AI product remains a business product, not an implementation agent. Kentaro asks for the human-supplied ODPC product identity, structured owner, governance boundary, and evaluation metric when they are missing; it records `awaiting_odpc_input` without blocking local business design. A reviewed delivery package writes `governance/ai-product-specification-status.json`; only confirmed inputs produce `specifications/ai-products/<id>.odpc.yaml`, an ODPC v1.1 catalog inline node and product reference, and an ODPG `AIProduct` node. Structural validation is not business evidence, data access,
compliance, approval, safety, or production readiness.

The wheel also carries the Kentaro documentation and agent skill instructions under its
installation `share/kentaro/` directory. An agent host can register those instructions through its
normal skill-discovery configuration; they do not grant authority or change a portfolio on install.

## Scenario packages and compatibility

Scenarios provide optional fixtures and workflows on the same engine. To explicitly start the
Udemy banking case, use `kentaro design init --scenario udemy-masterclass --output <workspace path>`
or the backward-compatible `kentaro masterclass init`. v0.2 `LearningPortfolio` files are
migrated in memory to `DesignPortfolio` and can be persisted with `kentaro design migrate`.
