# ODPC v1.1 AI Product Integration Design

**Status:** Approved for implementation on 2026-11-06

## Goal

Make ODPC v1.1 the only AI-product specification used by Kentaro. Kentaro will
ask a business user for the standard's missing design information, preserve the
answers as sourced DesignPortfolio claims, and export a standalone AI-product
profile, inline catalog object, catalog product reference, and ODPG AI-product
node when that information is available.

The Open Data Products SDK owns ODPC v1.1 validation. Kentaro owns business
design intake, provenance, package assembly, and coverage reporting.

## Authoritative standard

The target is the ODPC v1.1 AI Product profile and ODPC v1.1 catalog contract
in `Open-Data-Product-Initiative/odpc-v1.1`:

- `source/schema/v1.1/ai-product.yaml`
- `source/schema/v1.1/odpc.yaml`
- `source/v1.1/examples/rag-knowledge-assistant.yaml`
- `source/v1.1/examples/catalog-ai-products.yaml`

ODPC `AIProduct` is the accountable business product. It is not an `Agent`.
Agents, models, tools, workflows, services, and evaluations are implementation
components referenced by the product rather than embedded in it. ODPG remains
the relationship layer.

## Scope and explicit boundary

### In scope

- First-class ODPC v1.1 AI-product validation in `open-data-products`.
- Kentaro claim intake and question selection for the mandatory profile fields.
- Standalone profile, inline catalog `aiProduct` node, product reference, and
  ODPG `AIProduct` node generation.
- Clear package-level status for complete, incomplete, invalid, and validated
  standard coverage.
- Replacement of all existing Kentaro AI-product export wording, fixtures,
  tests, delivery outputs, and documentation.

### Out of scope

- Maysano writes, approvals, execution, or production-readiness claims.
- Model cards, prompts, credentials, deployment configuration, runtime traces,
  or agent implementation in the AI-product document.
- Inventing product type, autonomy, oversight, risk, or evaluation values.
- Backward compatibility for old Kentaro AI-product exports or handover package
  schemas.

## DesignPortfolio intake model

`ai_product` remains a DesignPortfolio object kind and remains distinct from a
data product. Its existing business claims remain available. It gains an
ODPC-specific, sourced claim group with the following required export inputs:

| ODPC concern | Required user-provided claims |
| --- | --- |
| Product identity | `product_id`, `product_version`, `product_type` |
| Accountable owner | one or more of `organization`, `team`, and `role` |
| Governance | `autonomy_level`, human-oversight required flag and requirements, consequential-action-approval required flag and requirements, `risk_classification`, and known limitations |
| Evaluation | at least one metric with identifier, name, measurement method, target value, unit, and status |

Existing name, purpose, owner, capabilities, human-oversight, evaluation, and
prohibited-action claims are not silently reclassified or discarded. They may
be used only where a direct, sourced mapping exists. A generic owner string,
for example, is not assumed to identify an ODPC organization, team, or role.

The standard fields are represented as ordinary provenance-bearing claims,
including nested claim values for the owner, governance requirements, and
evaluation metrics. Only values supplied as case facts or confirmed by the
user qualify for standard export. Proposed and unknown values stay visible in
the DesignPortfolio and readiness reports, but cannot fill mandatory ODPC
fields.

## Conversation and engagement behavior

When an AI product is added, read, or changed, Kentaro refreshes the adjacent
`engagement-state.json`. If any mandatory ODPC v1.1 claim is missing, its
highest-priority AI-product topic is a single grouped, targeted question. The
question names the AI product and requests only unresolved fields, for example:

> For the Risk-assessment preparation assistant, what stable product ID and
> version, product type, accountable organization/team/role, autonomy and
> oversight rules, consequential-action approval rule, risk classification,
> known limitations, and evaluation metric should Kentaro record?

The user can answer incrementally. After every answer, Kentaro persists the
new sourced claims, validates the portfolio, refreshes engagement state, and
asks only for the remaining highest-priority detail. No default, placeholder,
or inferred policy value is emitted.

Missing ODPC details are a design question, not a blocker for continuing
business design or producing a local review package. Existing structural
completion requirements unrelated to this profile remain unchanged.

## Upstream SDK responsibilities

`open-data-products` gains ODPC v1.1 support before Kentaro changes its
dependency pin. The SDK change includes:

1. Canonical AI-product profile and catalog schemas, versioned resources, and
   license/provenance metadata copied from the official ODPC v1.1 source.
2. Auto-detection for a document with the ODPC v1.1 AI-product schema URL and
   `kind: AIProduct`, alongside existing ODPC catalog detection.
3. Public profile validation and loading functions, and CLI validation that
   reports the profile as ODPC v1.1 rather than trying to load it as a catalog.
4. Catalog validation for `aiProduct` nodes and `productReference` records
   whose model is `ODPC` version `1.1` and profile `AIProduct`.
5. Cross-document validation helpers for a profile, catalog entry, product
   reference, and ODPG node whose identities and references must agree.

The upstream repository supplies valid and invalid profile fixtures, a catalog
with both AI-product representations, public API tests, CLI tests, and clean
wheel-install tests. It is released before Kentaro is updated; Kentaro pins the
exact released SDK version rather than a branch, local path, or Git URL.

## Kentaro export contract

For each AI product with complete confirmed ODPC claims, a new Kentaro
handover contains:

```text
specifications/
  ai-products/<ai-product-id>.odpc.yaml
  odpc.yaml
  odpg.yaml
governance/
  ai-product-specification-status.json
```

- The standalone file has `schema` set to the ODPC v1.1 AI-product profile,
  `version: "1.1"`, `kind: AIProduct`, and its `aiProduct` object.
- `odpc.yaml` contains both an inline `node.kind: aiProduct` object and a
  `node.kind: productReference` for that product. The reference declares
  `productCategory: ai_product`, `productModel.standard: ODPC`,
  `productModel.version: "1.1"`, `productModel.profile: AIProduct`, and a
  relative reference to the standalone profile.
- `odpg.yaml` uses an `AIProduct` node referencing the standalone profile.
  It preserves DesignPortfolio relationship edges. Kentaro must not export the
  business product as an `Agent` node.

`ai-product-specification-status.json` is generated for every package. For
each local AI product, it records the DesignPortfolio object ID, required
standard field paths, source claim IDs, generated artifact paths, SDK version,
and one of these coverage states:

| State | Meaning |
| --- | --- |
| `awaiting_odpc_input` | Mandatory claims are absent, unknown, or only proposed; no normative profile, catalog node, or product reference is emitted. |
| `invalid` | Inputs exist but the SDK or cross-document validation failed; diagnostics identify the invalid field or reference. |
| `validated` | The profile, inline node, product reference, and ODPG node were generated and validated. |

For `awaiting_odpc_input`, the package retains the product in the frozen
DesignPortfolio and Decision Context. A generated ODPG graph can retain its
relationship node as a local DesignPortfolio reference, explicitly labelled
non-normative. It must not point to a missing ODPC artifact. A catalog contains
only normative, validated AI-product entries.

Package integrity and standards coverage are separate results. A package may
be integrity-valid with partial ODPC AI-product coverage. Its manifest,
README, delivery brief, canvas, and CLI inspection output must say so directly
and must not claim that all specifications are validated.

## Replacement and compatibility decision

This is a replacement, not a migration.

- Remove the private `KentaroAIProductDefinition` format and references to it.
- Replace its output files, delivery-package wording, examples, snapshots, and
  tests with the ODPC v1.1 design.
- Bump the handover package schema for newly generated packages and reject old
  package schemas in `inspect` and `validate`; there is no fallback reader.
- Existing DesignPortfolio files remain source material. They are not
  automatically upgraded into standards-complete AI products. They receive the
  normal ODPC intake questions and must be regenerated to produce any new
  handover or specification output.

## Validation and failure behavior

Kentaro delegates standard validation to the released SDK. After SDK
validation, Kentaro performs package-specific checks that the profile,
catalog's inline object, product reference, graph node, and all graph edge
endpoints agree on product identity and relative paths.

Validation failure does not manufacture replacement values. Kentaro records
the failure in the status artifact and asks for a correction where the failure
comes from missing or invalid business input. A malformed generated mapping is
a Kentaro defect and must fail the handover test suite.

## Test strategy

### Open Data Products SDK

- Profile schema accepts the official valid YAML and JSON examples.
- Missing required governance or evaluation fields fail with a precise path.
- Document detection and CLI validation recognize `AIProduct` documents.
- Catalog validation accepts the inline AI-product node and corresponding
  product reference, and rejects mismatched profile/standard/version values.
- A clean wheel install validates the profile and catalog without a sibling
  repository checkout.

### Kentaro

- A newly proposed AI product produces an ODPC topic and focused question in
  refreshed engagement state.
- Incremental confirmed answers reduce that topic without replacing unrelated
  claim provenance.
- An incomplete product produces `awaiting_odpc_input`, no normative ODPC
  artifacts, and no false validation claim.
- A complete product produces the standalone profile, inline catalog node,
  product reference, and `AIProduct` ODPG node with matching references.
- Tampering with any identity, reference, or artifact digest fails package
  validation.
- Old Kentaro AI-product handover fixtures are removed; a deliberately old
  package is rejected rather than silently interpreted.
- Canvas, README, delivery brief, and CLI inspection show the same coverage
  state as the package manifest.

## Release order

1. Implement, test, build, clean-install, and release ODPC v1.1 support in
   `open-data-products`.
2. Update Kentaro's exact SDK pin and implement the new intake and export
   mapping using test-first changes.
3. Run Kentaro's full unit suite, package a wheel, clean-install it, and
   generate/validate a complete handover.
4. Publish only after the SDK release and Kentaro release artifacts provide
   fresh verification evidence.
