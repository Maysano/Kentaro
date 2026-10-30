# Open Data Products SDK integration

Selected by the project owner: [Open-Data-Product-Initiative/odp-agent-sdk](https://github.com/Open-Data-Product-Initiative/odp-agent-sdk).
Upstream README and packaging metadata checked on 2026-10-15.

Kentaro uses the [Open Data Products (ODPS) family of specifications](https://opendataproducts.org/)
as the semantic basis for its local data-product, use-case, and objective
draft artifacts. The SDK supplies generation and validation capabilities; ODPS
alignment does not make a local artifact authoritative or grant Maysano write access.

- Distribution: `open-data-products`; Python namespace: `open_data_products`.
- CLI: `open-data-products`, also available as `python -m open_data_products.cli`.
- Licence: Apache-2.0; Kentaro remains MIT. Preserve upstream licence and applicable notices when distributing SDK components.
- Upstream requires Python 3.8+; Kentaro requires Python 3.11+.

Sources: [README](https://github.com/Open-Data-Product-Initiative/odp-agent-sdk#readme),
[package metadata](https://github.com/Open-Data-Product-Initiative/odp-agent-sdk/blob/main/pyproject.toml).

## Implemented local-draft boundary

Start with standards-document inspection and validation: upstream documents `validate`, `explain`,
`refs` and `summary` commands. These complement the Maysano read client; SDK portfolio workflows
must not become another authoritative portfolio store. The upstream SDK also exposes generation
and MCP capabilities; selecting this dependency does not enable those capabilities in Kentaro.

Kentaro exposes a narrow standard CLI integration:

```shell
kentaro data-product draft ./business-context.md
kentaro use-case draft ./business-context.md
kentaro objective draft ./business-context.md
```

The default provider is local Ollama. Any non-Ollama provider requires an explicit
provider config file and `--allow-hosted-content`, because it may receive business
source content. The adapter preserves source digest, provider mode, validation status,
output references, timestamp, and limitations in a local append-oriented provenance
record. It does not receive or log provider credentials.

The commands invoke only the documented upstream `generate` and `validate` CLI
contracts. They create ODPS-aligned local drafts and validate them before reporting
success, or validate a specified local YAML artifact without generating anything. They
do not create or update a Maysano record, request approval, or imply production readiness.

## v0.2 Masterclass fixture

The v0.2 local design capability uses one deliberately narrow, deterministic SDK integration:
`open-data-products==0.4.0`. Its packaged Customer Profile scenario fixture is validated with
the SDK's documented `python -m open_data_products.cli validate <artifact> --json`
contract and is covered by an integration test. The normal course path does not run
generation, does not require Ollama or a hosted provider, and does not contact Maysano.

The pin is a standard Kentaro runtime dependency. A valid
fixture proves only that the artifact conforms to the SDK's structural validation; it is
not evidence that data exists, can be accessed, is safe to use, or is ready for production.

## Remaining integration work

1. Add fixture-based integration tests for intentionally invalid course artifacts and the
   bounded repair exercise.
2. Add a formal provider-routing policy that derives egress classification from provider
   configuration rather than the explicit CLI provider choice.
3. Keep the core portfolio briefing and dashboard runnable without network access or
   model generation.
