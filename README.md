# Kentaro

## Agentic Maysano Harness

Kentaro is an open-source, MIT-licensed harness for working with Maysano through Codex, Claude Code, and OpenCode.

It gives coding agents sourced business context and local, versioned governance and delivery objects for reviewing objectives, use cases, data products, delivery packages, and outcome evidence. v0.1 does not execute tools or process approvals.

Kentaro sits on top of Maysano Platform. It does not replace the platform.

## Use Kentaro in Codex

Ask **"Give me a portfolio briefing"** or **"List the portfolio data products"**.
Codex can retrieve the configured live pilot portfolio through Kentaro and explain sourced results in chat.
The repository skill is `.agents/skills/kentaro-portfolio-brief/SKILL.md` and can also be
explicitly requested as `$kentaro-portfolio-brief` once discovered by Codex.
If the new skill is not listed in an existing session, start a new chat in this repository;
the root `AGENTS.md` also points to the workflow for conversational requests.
The live workflow reads only Maysano's documented external pilot API. It does not write, cache,
or expose the local API key; the synthetic demo remains available when explicitly requested.

Ask **"List the data products"** to retrieve a compact, sourced inventory of data
products, their owners, recorded states, linked use cases, and provenance. The workflow is
defined in `.agents/skills/kentaro-list-data-products/SKILL.md` and uses the same synthetic
source limitations: the external API does not return owners.

Ask **"List the use cases"** to retrieve a compact, sourced inventory of use cases,
their owners, recorded states, supporting objectives, linked data products, and provenance.
The workflow is defined in `.agents/skills/kentaro-list-use-cases/SKILL.md` and preserves the
same live-source limitations.

Ask **"List the business objectives"** to retrieve a compact, sourced inventory of
objectives, their owners, recorded states, supported use cases, and provenance. The workflow is
defined in `.agents/skills/kentaro-list-objectives/SKILL.md` and preserves the same live-source
limitations.

Ask **"Show me the portfolio dashboard"** to display a rendered status snapshot in the conversation with
expandable source details. The dashboard skill lives at
`.agents/skills/kentaro-portfolio-dashboard/SKILL.md`. To generate it manually:

```powershell
python -m kentaro --config examples/configs/live.toml --env-file .kentaro/workspace/.env dashboard --output .kentaro/workspace/dashboards/portfolio-dashboard.html
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
No cache or SDK model calls are implemented. Live pilot API retrieval is GET-only, uses the
ignored local credential file, and has no mutation capability. The dashboard is a static
snapshot with no automatic refresh or saved-view configuration.
See [implementation status](docs/roadmap.md), [API capability matrix](docs/api-contract.md),
[configuration](docs/configuration.md) and [data boundaries](docs/security-and-data-boundaries.md).

## Local governance and delivery validation

The v0.1 object model is local-only. It validates a `Mandate → Work Envelope →
Execution Package → Execution Requests → Evidence Bundle` chain without executing
an action. Start with the synthetic [governance example](examples/governance/retention-review.json):

```powershell
python -m kentaro --config examples/configs/demo.toml object validate --input examples/governance/retention-review.json
python -m kentaro --config examples/configs/demo.toml policy evaluate --input examples/governance/retention-review.json --request-id request-retention-note
python -m kentaro --config examples/configs/demo.toml evidence export --input examples/governance/retention-review.json --request-id request-retention-note --actor local-user --hash-chain --output .kentaro/workspace/evidence/retention-review.jsonl
python -m kentaro --config examples/configs/demo.toml evidence verify --input .kentaro/workspace/evidence/retention-review.jsonl
```

`allowed` means that the proposal is structurally in scope; it never permits
execution. Evidence output is append-oriented and redacted, with optional hash
chaining for tamper indication. It is not an immutable or compliance-grade audit log.

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
  │ Read-only context retrieval │
  │ Local schema validation     │
  │ Deterministic policy logic  │
  │ Redacted evidence export    │
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

The selected SDK and any model work remain outside v0.1. The harness does not invoke local or cloud models, external tools, or side-effecting adapters.

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
- Local governance/delivery validation, policy evaluation, and evidence export

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
