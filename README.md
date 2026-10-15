# Kentaro

## Agentic Maysano Harness

Kentaro is an open-source, MIT-licensed harness for working with Maysano through Codex, Claude Code, and OpenCode.

It gives coding agents the business context, structured artefacts, working rules, SDK capabilities, approved tools, and human approval boundaries needed to work on real business objectives, use cases, data products, implementation packages, and outcome evidence.

Kentaro sits on top of Maysano Platform. It does not replace the platform.

## What Kentaro provides

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

The Open Data Products SDK is an independent component with its own published license and release process.

## Why Kentaro

AI agents need more than a prompt and a code repository. They need a governed understanding of what the organisation is trying to achieve, which data products support that work, what actions are allowed, and what evidence proves progress.

Kentaro makes that context portable and executable in the agent workspace where teams already work.

## License

MIT License. See [LICENSE](LICENSE).
