# Read API capability matrix

Status: proposed local fixture contract; actual Maysano endpoints have not been supplied or verified.
This document does not claim M0 agreement or live connectivity.

| Capability | Demo | Actual platform |
| --- | --- | --- |
| Accessible scopes and delegated authentication | Fixed demo scope; no token | Unverified |
| Objective / use case / data product reads | 1 / 2 / 3 synthetic records | Unverified |
| Owners, lifecycle, typed relationships | Fixture fields and scoped edges | Unverified |
| Decisions, risks, evidence | One synthetic record each | Unverified |
| Stable IDs, versions, updated time, references | Preserved in reports | Unverified |
| Approval history, delivery milestones, ODPS content | Unavailable; reported as limitations | Unverified |
| Pagination and permission failures | Not implemented | Unverified |

Before live integration, obtain an approved OpenAPI/schema export, authentication and secret-store
requirements, pagination rules, scope semantics, error examples and a permitted test environment.
Never derive endpoint names from this fixture. Platform permissions must govern live reads.
