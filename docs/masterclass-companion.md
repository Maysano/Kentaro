# v0.2 Masterclass Companion

The Masterclass is the first scenario package on Kentaro's reusable local
`DesignPortfolio` capability. The installed `kentaro.scenarios.udemy_masterclass` package contains
course fixtures, checkpoints, and facilitator material; `kentaro masterclass init` stages the ODPS
exercises in the learner's local workspace. The shared engine, canvas, reports, and skills are
domain-independent. It is not a Maysano portfolio editor,
business-case approval process, data-access mechanism, or production-readiness assessment.

## Start the fictional case

Install the pinned course dependency, initialise the Customer Risk Intelligence case,
and validate the resulting local `DesignPortfolio`:

```shell
python -m pip install "kentaro[masterclass]"
kentaro masterclass init
kentaro masterclass validate --input .kentaro/workspace/masterclass/customer-risk-intelligence/portfolio.json
```

The only standard-course inputs are packaged synthetic fixtures and local files. The
workflow neither contacts Maysano nor starts Ollama nor sends material to a hosted model.

## Progressive learner exercises

1. **Business outcome:** inspect the proposed 40% risk-handling target and identify the
   KPI baseline, accountable owner, and decision evidence that remain unknown.
2. **AI use case:** connect the AI-assisted risk assessment use case to its business
   objective using the canonical `use-case-supports-objective` relationship.
3. **Product boundary:** distinguish the Risk Assessment Assistant (an AI product) from
   Customer Profile, Transaction Risk, and Compliance Signals (data products). Do not
   describe a data product as an AI product or infer that a named product is available.
4. **Relationships and dependencies:** render the canvas, select a node or relationship,
   and trace declared dependencies and visibly missing claims.
5. **ODPS exercise:** validate the Customer Profile fixture:

   ```shell
   kentaro masterclass validate-odps
   ```

   Structural validity is not a claim of access, quality, compliance, safety, value, or
   operating readiness.

   For the bounded repair exercise, `masterclass init` already writes
   `.kentaro/workspace/masterclass/customer-risk-intelligence/customer-profile-repair.odps.yaml`.
   Validate it, then replace its intentionally invalid `internal`
   visibility with `organisation` and validate again. Do not add operational fields or
   infer missing business evidence as part of this repair.
6. **Implementation review:** create reports and inspect stale status after any local
   portfolio change:

   ```shell
   kentaro masterclass report --input .kentaro/workspace/masterclass/customer-risk-intelligence/portfolio.json --output-dir .kentaro/workspace/masterclass/customer-risk-intelligence/outputs
   kentaro masterclass status --input .kentaro/workspace/masterclass/customer-risk-intelligence/portfolio.json --manifest .kentaro/workspace/masterclass/customer-risk-intelligence/outputs/manifest.json
   ```

## Course deliverables

The standard path produces these local deliverables: the starting portfolio, validation
result, relationship canvas, ODPS validation result, readiness-gap report, executive
summary, unresolved-decisions report, dependency manifest, and stale-output status. All
are local artefacts under `.kentaro/workspace/` when the learner uses the default paths.

Each claim records its value, status, source ID, source revision, asserted timestamp,
and derivation-input hash. Use `user_confirmed` only after human confirmation. Proposed,
assumed, and unknown claims remain explicitly labelled.

## Facilitator answer key

The expected learning model has one relationship from the AI-assisted risk-assessment
use case to the risk-handling objective (`use-case-supports-objective`), one relationship
from that use case to the Risk Assessment Assistant, and three declared AI-product inputs:
Customer Profile, Transaction Risk, and Compliance Signals. Unknown owners and evidence
gaps are intentionally retained. Do not resolve them by guessing.

## Source contributor check

Source contributors preparing a release can run the test suite from a fresh checkout:

```shell
python3 -m unittest discover -s tests -v
```

The expected case contains one objective, one AI use case, one AI product, and three
data products. The readiness output intentionally contains unresolved ownership and
evidence gaps; those are teaching prompts, not defects to hide or approvals to grant.
