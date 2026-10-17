# Kentaro

Kentaro is the open-source, read-only Agentic Maysano Harness. It gives you a
working local portfolio briefing and sourced dashboard immediately, then lets you
opt in to a bounded read-only Maysano source without turning Kentaro into a system
that acts on your behalf.

Learn more at [maysano.com/kentaro](https://maysano.com/kentaro).

## Install

Kentaro requires Python 3.11 or later.

```shell
python -m pip install kentaro
```

## Run the demo

Run the complete synthetic demonstration with no account, configuration file,
repository checkout, API key, or network request:

```shell
kentaro demo
```

It prints a sourced portfolio briefing and writes a dashboard to a new timestamped
file under `.kentaro/workspace/`. Kentaro creates that directory automatically and
prints the complete local path.

## Use Kentaro locally

The normal local commands use the packaged synthetic portfolio context:

```shell
kentaro portfolio brief
kentaro dashboard
```

`kentaro dashboard` always creates a fresh timestamped HTML file in
`.kentaro/workspace/`; it never overwrites an existing dashboard.

## Connect a read-only Maysano source

Live access is explicit and opt-in. Configure a Maysano-issued read-only key through
the guided local setup, then select the source for an individual read:

```shell
kentaro configure maysano
kentaro portfolio brief --source maysano
```

The key is stored only in Kentaro's ignored local workspace and is never printed.
The pilot source is GET-only. It does not currently provide owners, decisions,
risks, evidence, approval history, or milestones; Kentaro labels those fields as
unavailable rather than inventing them.

## Safety boundary

Kentaro v0.1 retrieves bounded sourced context, validates local versioned governance
and delivery objects, generates drafts and reports, classifies proposed requests, and
exports local evidence. It does not create external records, write to Maysano or a
business-context graph, execute business actions, request or process approvals, or
claim immutable or compliance-grade audit. The optional local draft commands create
local artifacts only; a hosted provider requires explicit acknowledgement before it
receives source content.

Maysano remains the system of record for portfolio state, approvals, graph updates,
tenant controls, authoritative revocation, retention, and platform audit. An
`allowed` classification means only that a request is structurally in scope; it is
not permission to execute.

## Advanced configuration and governance

TOML profiles are an advanced team configuration mechanism for named environments,
custom API endpoints or workspace paths, model declarations, organisation policies,
and non-default profiles. They are never needed for the normal local experience.

To create proposed local data-product, use-case, or objective drafts from Markdown or
text, install the optional SDK integration. These local artifacts align with the
[Open Data Products (ODPS) family of specifications](https://opendataproducts.org/):

```shell
python -m pip install "kentaro[odps]"
kentaro data-product draft ./business-context.md
kentaro use-case draft ./business-context.md
kentaro objective draft ./business-context.md
```

Validate a saved local draft without generating anything:

```shell
kentaro data-product validate ./data-product.yaml
kentaro use-case validate ./use-case.yaml
kentaro objective validate ./objective.yaml
```

The default provider is local Ollama. A hosted provider requires an explicit provider
configuration and `--allow-hosted-content`, because it may receive the source document.
Each result remains a local draft; it never creates a Maysano record or grants authority.

Detailed material is kept out of onboarding:

- [Getting started](https://github.com/Maysano/Kentaro/blob/main/docs/getting-started.md)
- [Advanced configuration](https://github.com/Maysano/Kentaro/blob/main/docs/configuration.md)
- [Local draft artifacts](https://github.com/Maysano/Kentaro/blob/main/docs/data-product-drafts.md)
- [Governance and delivery object model](https://github.com/Maysano/Kentaro/blob/main/docs/governance-and-delivery-object-model.md)
- [Architecture](https://github.com/Maysano/Kentaro/blob/main/docs/architecture.md)
- [Security and data boundaries](https://github.com/Maysano/Kentaro/blob/main/docs/security-and-data-boundaries.md)
- [Developer guide](https://github.com/Maysano/Kentaro/blob/main/docs/developer-guide.md)

[MIT License](LICENSE) © 2026 Maysano.
