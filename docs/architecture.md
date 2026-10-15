# Architecture

CLI → validated configuration → scoped demo client → deterministic Markdown report.
The core has no Codex dependency. Codex instructions live under adapters/codex.
Maysano remains authoritative; fixture references use demo: identifiers and cannot resolve to live records.
The dashboard renderer reuses the same scoped client and emits a static HTML snapshot.
The SDK adapter, authenticated transport, cache and context builder are future work.
The selected SDK is [odp-agent-sdk](https://github.com/Open-Data-Product-Initiative/odp-agent-sdk), distributed as `open-data-products` (Apache-2.0). See [integration notes](sdk-integration.md). Runtime integration and version selection remain pending.
