# Open Data Products SDK integration

Selected by the project owner: [Open-Data-Product-Initiative/odp-agent-sdk](https://github.com/Open-Data-Product-Initiative/odp-agent-sdk).
Upstream README and packaging metadata checked on 2026-10-15.

- Distribution: `open-data-products`; Python namespace: `open_data_products`.
- CLI: `open-data-products`, also available as `python -m open_data_products.cli`.
- Licence: Apache-2.0; Kentaro remains MIT. Preserve upstream licence and applicable notices when distributing SDK components.
- Upstream requires Python 3.8+; Kentaro requires Python 3.11+.

Sources: [README](https://github.com/Open-Data-Product-Initiative/odp-agent-sdk#readme),
[package metadata](https://github.com/Open-Data-Product-Initiative/odp-agent-sdk/blob/main/pyproject.toml).

## Intended boundary

Start with standards-document inspection and validation: upstream documents `validate`, `explain`,
`refs` and `summary` commands. These complement the Maysano read client; SDK portfolio workflows
must not become another authoritative portfolio store. The upstream SDK also exposes generation
and MCP capabilities; selecting this dependency does not enable those capabilities in Kentaro.

The SDK documents generation configuration in `generation.config.yaml` and local or hosted providers.
Kentaro's local/cloud/hybrid classification and no-send rules must be enforced before invoking
model work. Do not assume upstream provider configuration alone implements Kentaro's policy.

## Next implementation steps

1. Select a tested upstream release or immutable revision and verify its public Python API.
2. Implement a narrow adapter under `kentaro/sdk/` for inspection and validation.
3. Test valid and invalid ODPS fixtures, preserve validation diagnostics and source references.
4. Map permitted model configuration only after routing policy enforcement is implemented.

No SDK dependency is installed or declared yet. The current synthetic briefing remains runnable
without the SDK, network access or model execution.
