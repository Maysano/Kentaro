# Kentaro

## Agentic Maysano Harness

Kentaro is an open-source, MIT-licensed harness for working with Maysano through Codex, Claude Code, and OpenCode.

It gives coding agents the business context, structured artefacts, working rules, SDK capabilities, approved tools, and human approval boundaries needed to work on real business objectives, use cases, data products, implementation packages, and outcome evidence.

Kentaro sits on top of Maysano Platform. It does not replace the platform.

## Use Kentaro in Codex

Ask **"Give me a demo portfolio briefing"** or **"Which demo portfolio records have missing owners?"**
Codex can retrieve the fixture through Kentaro and explain the sourced results in chat.
The repository skill is `.agents/skills/kentaro-portfolio-brief/SKILL.md` and can also be
explicitly requested as `$kentaro-portfolio-brief` once discovered by Codex.
If the new skill is not listed in an existing session, start a new chat in this repository;
the root `AGENTS.md` also points to the workflow for conversational requests.
The current workflow uses synthetic data; live Maysano retrieval remains pending.

Ask **"List the demo data products"** to retrieve a compact, sourced inventory of data
products, their owners, recorded states, linked use cases, and provenance. The workflow is
defined in `.agents/skills/kentaro-list-data-products/SKILL.md` and uses the same synthetic
demo limitation.

Ask **"List the demo use cases"** to retrieve a compact, sourced inventory of use cases,
their owners, recorded states, supporting objectives, linked data products, and provenance.
The workflow is defined in `.agents/skills/kentaro-list-use-cases/SKILL.md` and uses the same
synthetic demo limitation.

Ask **"List the demo business objectives"** to retrieve a compact, sourced inventory of
objectives, their owners, recorded states, supported use cases, and provenance. The workflow is
defined in `.agents/skills/kentaro-list-objectives/SKILL.md` and uses the same synthetic demo
limitation.

Ask **"Show me the demo portfolio dashboard"** to display a rendered status snapshot in the conversation with
expandable source details. The dashboard skill lives at
`.agents/skills/kentaro-portfolio-dashboard/SKILL.md`. To generate it manually:

```powershell
python -m kentaro --config examples/configs/demo.toml dashboard --output .kentaro/workspace/dashboards/portfolio-dashboard.html
```

Choose a new output filename each time; existing files are never overwritten.

## Local user workspace

Create reports, dashboards, exports, and other work produced through Kentaro
under `.kentaro/workspace/`. The directory is ignored by Git, so its contents
are never part of a commit or push. It is created on demand; for example:

```powershell
New-Item -ItemType Directory -Force .kentaro/workspace/reports
```

Keep changes to the harness source, documentation, tests, and repository skills
outside this directory so they remain reviewable project changes.

## Start the demo

The first implementation is a read-only, synthetic portfolio briefing. Python 3.11+ is required.
From the repository root:

```powershell
python -m kentaro --config examples/configs/demo.toml validate-config
python -m kentaro --config examples/configs/demo.toml portfolio brief
python -m unittest discover -s tests -v
```

Install the CLI with `python -m pip install -e .`, then use `kentaro` in place of `python -m kentaro`.
No customer credentials, live API, cache or SDK model calls are implemented yet.
The dashboard is a static synthetic snapshot, with no automatic refresh or saved-view configuration.
See [implementation status](docs/roadmap.md), [API capability matrix](docs/api-contract.md),
[configuration](docs/configuration.md) and [data boundaries](docs/security-and-data-boundaries.md).

## Planned capabilities

- Workspace adapters for Codex, Claude Code, and OpenCode
- Repository structure for objectives, use cases, data products, decisions, evidence, and implementation packages
- Open Data Products SDK integration
- SDK configuration for local, cloud, or hybrid model execution
- Read-only Maysano API visibility in version 0.1
- Manager-customisable portfolio dashboard
- Governed MCP actions for Business Objectives, Use Cases, and Data Products in version 0.2
- Reviewable change sets, evidence, and approval records

## Architecture

```text
Codex / Claude Code / OpenCode
                │
        Kentaro Harness
  ┌─────────────────────────────┐
  │ Open Data Products SDK      │
  │ SDK model configuration     │
  │ Local or cloud model use    │
  │ Workspace and repo adapters │
  └─────────────────────────────┘
                │
      Maysano Platform APIs
                │
  ┌─────────────────────────────┐
  │ Context graph               │
  │ Agent services              │
  │ Workflows and approvals     │
  │ Evidence and audit          │
  │ GUI and shared APIs         │
  └─────────────────────────────┘
```

The SDK executes model work inside the Harness. Its configuration selects the local LLM server, approved cloud model, or hybrid routing policy for each deployment.

Maysano Platform remains the shared system of record. It holds the portfolio context, workflow state, approvals, evidence, audit trail, and shared services used by both the GUI and Kentaro workspaces.

## Roadmap

### Version 0.1: Visibility (in Q4 2026)

Kentaro 0.1 connects to authenticated Maysano APIs for read-only portfolio visibility.

It provides:

- Business Objective, Use Case, and Data Product visibility
- Relationship and coverage analysis
- Risks, decisions, owners, delivery state, and evidence
- Manager-customisable dashboard
- Context retrieval for Codex, Claude Code, and OpenCode
- Open Data Products SDK working capabilities

### Version 0.2: Governed actions (next)

Kentaro 0.2 adds selected MCP tools on top of the API foundation.

It enables governed actions for:

- Business Objectives
- Use Cases
- Data Products

Every action creates a reviewable change set. Maysano records the source material, proposed change, reasoning, affected relationships, required approval, decision, and resulting version.

## Open source boundary

Kentaro Harness is released under the MIT License.

The open-source release includes the Harness source, workspace adapters, repository structure, configuration templates, integration clients, and Kentaro-specific workflow and MCP-tool definitions.

Maysano Platform is a separate product. Its shared context graph, GUI, workflow state, approval services, audit model, APIs, jobs, and shared agent services are not included in this repository unless a component is explicitly released under the MIT License.

The SDK is [odp-agent-sdk](https://github.com/Open-Data-Product-Initiative/odp-agent-sdk), published as `open-data-products` with the Python namespace `open_data_products`. It is an independent Apache-2.0 component with its own release process. See [SDK integration notes](docs/sdk-integration.md).

## Why Kentaro

AI agents need more than a prompt and a code repository. They need a governed understanding of what the organisation is trying to achieve, which data products support that work, what actions are allowed, and what evidence proves progress.

Kentaro makes that context portable and executable in the agent workspace where teams already work.

## License

MIT License. See [LICENSE](LICENSE).
