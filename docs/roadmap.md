# Implementation status

The v0.1 slice implements configuration validation, scoped synthetic and live read-only
retrieval, sourced portfolio briefings and dashboards, local governance/delivery-object
validation, deterministic policy evaluation, append-oriented evidence export, and no-write tests.
Existing MIT licence retained.

M0 is partially evidenced by the Maysano Platform API Client Integration Guide v1: the pilot
base URL, bearer-key authentication, GET-only resources, pagination, permissions, rate limit,
and no-store response policy are documented. Customer classification, retention policy, and
production-environment requirements remain platform-owner decisions. The SDK repository is
confirmed as [odp-agent-sdk](https://github.com/Open-Data-Product-Initiative/odp-agent-sdk);
adapter API and version selection remain pending.
M1 now includes an approved read-only pilot transport and ignored local credential file. Next:
secret-store integration, broader context analysis, remaining workflows, and SDK integration.
A static dashboard and conversational dashboard skill now support live pilot data; saved manager
views and automatic refresh remain pending.

Demo acceptance: one objective, two use cases and three products appear with relationships,
a decision, a risk and evidence; uc-2 has unknown ownership. Every source has an ID, version,
record timestamp and fixture reference. No cloud model is needed.
