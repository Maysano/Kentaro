---
name: kentaro-data-product-design
description: Define reusable local data-product requirements and validate a supplied ODPS artifact through Kentaro's pinned SDK adapter. Do not treat schema validation as data availability or approval.
---

# Kentaro Data Product Design

Create kind `data_product` separately from any AI product. Ask for purpose and value,
at least one consumer or consumer group, a consumer-oriented boundary, consumption capability,
owner and lifecycle responsibility, intended interface/service model, semantics, quality,
freshness, contract, and access requirements. Preserve unknown, assumed, and proposed
information as canonical Claims rather than inventing operating facts.

Assess product qualification separately from reuse and operational readiness. One meaningful
identified consumer is sufficient for a candidate data product; additional consumers improve the
reuse assessment but are never a qualification gate. A dataset or pipeline is not a product just
because it has a name: the portfolio needs an explicit consumer-oriented boundary and intended
consumption capability. Missing ownership, contracts, or access are visible design/readiness gaps,
not automatic proof that the concept is not a data product. Distinguish information requirement,
candidate data capability, candidate data product, qualified design concept,
implementation-ready product, and operational data product in reports.

For minimal input, begin with information requirements and one or more candidate consumer-oriented
boundaries only where a proposed use case needs them. Mark source systems, authority, access,
quality, interface, and ownership as unknown or proposed. Do not ask the business owner to design
the data product or technical architecture before presenting the first connected proposal.

Use `kentaro design validate-odps --artifact <file>` for structural ODPS validation. The adapter
uses the pinned SDK version and does not establish access, data quality, compliance, safety, or
production readiness. Keep generated local design artifacts under `.kentaro/workspace/`.
