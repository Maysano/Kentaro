# Kentaro developer documentation

This documentation is for people installing, operating, extending, or releasing
Kentaro. Kentaro v0.1 is a read-only Agentic Maysano Harness; Maysano remains the
system of record for portfolio state, approvals, graph updates, tenant controls, and
platform audit.

Product home: [maysano.com/kentaro](https://maysano.com/kentaro).

## Start here

- [Getting started](getting-started.md): install Kentaro, run its packaged synthetic
  demo with no configuration, and explicitly opt in to a read-only Maysano source.
- [Developer guide](developer-guide.md): repository structure, contribution rules,
  tests, package build, and release checks.

## Product and technical references

- [Delivery plan](delivery-plan.md): v0.1 scope, exit condition, and later work.
- [Architecture](architecture.md): boundaries between Kentaro and Maysano.
- [Governance and delivery object model](governance-and-delivery-object-model.md):
  local schemas, deterministic policy, evidence, and the required revocation clause.
- [Advanced configuration](configuration.md): optional TOML profiles, read-only
  credentials, and disabled model configuration.
- [Local draft artifacts](data-product-drafts.md): optional data-product, use-case,
  and objective generation aligned with the [ODPS family of specifications](https://opendataproducts.org/),
  provider consent, validation, and local provenance records.
- [Read API capability matrix](api-contract.md): documented pilot API limits.
- [Security and data boundaries](security-and-data-boundaries.md): handling of
  credentials, retrieved context, and evidence exports.
- [Implementation status](roadmap.md): verified current implementation status and
  explicitly deferred work.
