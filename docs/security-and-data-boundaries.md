# Data boundaries

The current slice reads synthetic local JSON only. It has no HTTP transport, authentication,
cache, model execution or platform mutation implementation. The request guard allows GET only.
Scope filtering applies to records and to both relationship endpoints. Local filtering is not
an authorization mechanism; future live reads must enforce permissions at Maysano retrieval.

Only public synthetic data is supported. Customer retention, encryption, cache exclusions and
cloud classification policy need platform-owner decisions before customer data is introduced.
Reports display fixture retrieval time separately from record timestamps and are not live status.
No execution log exists yet. Future logs should contain request identifiers, not sensitive bodies.
