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

To update an existing installation, run `python -m pip install --upgrade kentaro`.

## Start in Codex

After installing, create an empty local project folder in Codex. In its first chat,
send this message exactly; Kentaro handles the technical setup on the learner's
behalf:

> Set up Kentaro in this project. Run `kentaro setup codex`, then `kentaro doctor`,
> on my behalf. Do not clone the Kentaro repository. When the checks pass, give me a
> short plain-language summary with **Setup**, **Health check**, and **What happens
> next**. Confirm the 13 skills, local workspace, ODPS validation, and visual canvas;
> then tell me to start a fresh Codex conversation here before we begin the
> DesignPortfolio, with one ready-to-send business prompt.

Codex runs the installed `kentaro setup codex` and `kentaro doctor` commands in that
folder. It installs the 13 skills in `.agents/skills/`, adds Kentaro's bounded
`AGENTS.md` guidance, and creates the local workspace while preserving existing user
instructions and changed skills.

When Codex reports that the health check passed, start a **new conversation in the
same folder**. Codex loads `AGENTS.md` and skills when a conversation starts, so the
setup conversation cannot reliably use the instructions it just installed. In the new
conversation, start with a short business prompt, for example:

> Our bank's customer risk assessments take too long. Help me improve this process.

Kentaro creates a local, evidence-labelled DesignPortfolio from that business input,
then guides the learner through the next highest-priority design question. Learners do
not clone the Kentaro repository, install skills, or type Kentaro commands themselves.

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

## Design a local business and product portfolio

Kentaro v0.2 provides a deterministic local `DesignPortfolio` for objectives, use cases,
AI products, data products, dependencies, evidence claims, readiness gaps, and reports. It is
not an authoritative Maysano portfolio and never contacts a model or service in the standard path.

```shell
kentaro design init --title "Permit Service Transformation" --portfolio-id permit-service --output .kentaro/workspace/design/permit-service.json
kentaro design add-object --input .kentaro/workspace/design/permit-service.json --id objective-speed --kind objective --name "Faster permit decisions" --purpose "Reduce avoidable delay" --owner "Service director" --lifecycle-status proposed
kentaro design validate --input .kentaro/workspace/design/permit-service.json
kentaro design analyze --input .kentaro/workspace/design/permit-service.json
kentaro design report --input .kentaro/workspace/design/permit-service.json --output-dir .kentaro/workspace/design/permit-service-outputs
```

Generic commands never select a case automatically. The optional `--scenario udemy-masterclass`
starter and the legacy `masterclass` commands explicitly select the course package.

## Run the fictional Masterclass scenario

The Integrated Data & AI Product Management Masterclass is a fictional scenario on the same
standard Kentaro installation. It uses a Customer Risk Intelligence case, keeps AI products
distinct from data products, and does not contact Maysano, Ollama, or a hosted model.

```shell
python -m pip install kentaro
kentaro masterclass init
kentaro masterclass validate --input .kentaro/workspace/masterclass/customer-risk-intelligence/portfolio.json
kentaro masterclass report --input .kentaro/workspace/masterclass/customer-risk-intelligence/portfolio.json --output-dir .kentaro/workspace/masterclass/customer-risk-intelligence/outputs
kentaro masterclass validate-odps --artifact .kentaro/workspace/masterclass/customer-risk-intelligence/customer-profile.odps.yaml
```

The reports and canvas label proposed, assumed, and unknown information. SDK validation
does not establish production readiness, business approval, compliance, or data availability.

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

Kentaro v0.1 and v0.2 retrieve bounded sourced context, validate local versioned governance
and learning objects, generate local drafts and reports, classify proposed requests, and
export local evidence. They do not create external records, write to Maysano or a
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
text, use the SDK included in the standard installation. These local artifacts align with the
[Open Data Products (ODPS) family of specifications](https://opendataproducts.org/):

```shell
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
- [Local business design](https://github.com/Maysano/Kentaro/blob/main/docs/design-portfolio.md)
- [Masterclass Companion](https://github.com/Maysano/Kentaro/blob/main/docs/masterclass-companion.md)
- [Governance and delivery object model](https://github.com/Maysano/Kentaro/blob/main/docs/governance-and-delivery-object-model.md)
- [Architecture](https://github.com/Maysano/Kentaro/blob/main/docs/architecture.md)
- [Security and data boundaries](https://github.com/Maysano/Kentaro/blob/main/docs/security-and-data-boundaries.md)
- [Developer guide](https://github.com/Maysano/Kentaro/blob/main/docs/developer-guide.md)

[MIT License](LICENSE) © 2026 Maysano.
