# Kentaro Harness Delivery Plan

## Decision

Kentaro Harness will use two complementary delivery routes:

1. **GitHub repository** for source, contribution, issues, examples, architecture, and self-hosting.
2. **PyPI package** for a versioned, installable command-line product and integrations for coding agents.

The PyPI package does not replace the repository. The repository is the project home. PyPI is the fast adoption route for users who want to apply Kentaro to an existing project.

## Product Boundary

Kentaro is the governed business-facing harness. It turns a use case into a structured execution package, coordinates its delivery, collects evidence, and makes the result reviewable.

Codex is an implementation agent that works inside a project. Kentaro gives Codex structured context, tasks, gates, and evidence requirements. Codex does not replace Kentaro and Kentaro does not attempt to become a general-purpose coding agent.

The Open Data Products SDK and its model configuration remain inside Kentaro Harness. The SDK supports local or cloud models through its configuration. The Maysano Platform sits above Kentaro and hosts platform agents and the graphical product experience.

## Primary Installation Flow

The initial developer and power-user flow should be:

```bash
pipx install kentaro-harness
cd customer-project
kentaro init --codex
```

`pipx` is the preferred human installation route because it provides the `kentaro` command without adding Kentaro to the target project's Python dependencies. Support `uv tool install kentaro-harness` as an equivalent modern route. Keep `pip install kentaro-harness` available for environments that manage their own virtual environments.

After `kentaro init --codex`, the project contains a small `.kentaro/` directory and Codex instructions. The directory stores configuration, execution packages, evidence, generated artifacts, and local run history. It should be safe to commit selected configuration and package definitions, while generated artifacts, secrets, and local runtime state stay ignored by Git.

The user then opens Codex in that project and requests a governed task, for example:

```text
Use Kentaro to prepare and execute the customer onboarding automation use case.
```

Codex reads the Kentaro instructions and invokes Kentaro instead of inventing its own uncontrolled workflow.

## Agent Interfaces

Kentaro should expose three interfaces from one core engine.

### 1. CLI, required for v0.1

The CLI is the common baseline for users, CI, and coding agents.

Initial command set:

```bash
kentaro init --codex
kentaro inspect
kentaro product create
kentaro objective create
kentaro usecase create
kentaro package create
kentaro package validate
kentaro run
kentaro status
kentaro evidence verify
kentaro report
```

Names may be refined during implementation, but commands must remain task-oriented and stable. Every command should return structured JSON through a `--json` option for agent use.

### Core hierarchy

Kentaro must keep the business and delivery hierarchy explicit:

```text
Product
└── Objective
    └── Use case
        └── Execution package
            └── Execution, artifacts, and outcome evidence
```

`kentaro product create` creates the durable managed product that contains the work. `kentaro objective create` defines a measurable intended outcome for that product. A use case is connected to its objective but remains the direct driver for an execution package. One objective may have several use cases; one use case may require one or more data products, datasets, or implementation tasks.

Use explicit parent references in the CLI, for example:

```bash
kentaro product create --name "Customer Onboarding"
kentaro objective create --product customer-onboarding --name "Reduce onboarding time"
kentaro usecase create --objective reduce-onboarding-time --name "Automate document verification"
kentaro package create --usecase automate-document-verification
```

### 2. MCP server, target for v0.2

Kentaro should expose its key actions as an MCP server over stdio. This gives Codex named tools instead of relying only on shell commands.

Initial MCP tools:

- `inspect_project`
- `create_use_case`
- `create_execution_package`
- `validate_package`
- `run_package`
- `get_run_status`
- `collect_evidence`
- `verify_evidence`
- `generate_report`

The MCP server must call the same internal application services as the CLI. Do not create a second Kentaro implementation for MCP.

### 3. Python API, secondary

Expose a small documented Python API for customers and partners who want to embed Kentaro in their own automation. This is not the primary v0.1 user journey.

## Codex Integration

`kentaro init --codex` should install a narrow instruction file in the target project. Use the current Codex convention supported by the target environment, such as `AGENTS.md` or a dedicated skill folder.

The instruction must state:

- Use Kentaro before starting governed implementation work.
- Inspect existing Kentaro configuration and packages first.
- Create or update an execution package before implementation.
- Record artifacts and outcome evidence.
- Stop for human approval at explicitly reserved gates.
- Never place secrets in package files, prompts, or evidence.

Kentaro should work through the CLI even when MCP is unavailable. MCP improves the experience later but must not block adoption.

## v0.1 Scope

Build the smallest complete flow:

1. Install Kentaro from PyPI.
2. Initialise a project for Codex.
3. Create one product, objective, and use case.
4. Generate and validate one execution package.
5. Execute through the Kentaro local harness and configured SDK/model path.
6. Store artifacts and evidence locally.
7. Produce a concise outcome report.

v0.1 should support local-first model configuration with cloud-model fallback through the existing SDK configuration. It should not require Docker, a hosted account, or the Maysano Platform.

## Repository Structure

Use a standard Python package structure:

```text
Kentaro/
├── pyproject.toml
├── README.md
├── LICENSE
├── src/kentaro/
│   ├── cli/
│   ├── core/
│   ├── packages/
│   ├── evidence/
│   ├── sdk/
│   ├── codex/
│   └── mcp/                 # v0.2 target
├── templates/
│   └── use-cases/
├── examples/
├── tests/
└── docs/
```

Declare the `kentaro` console script in `pyproject.toml`. Publish reproducible versioned releases to PyPI from GitHub Actions after tests and package checks pass.

## Distribution Positioning

The message is:

> Kentaro is an open-source, local-first AI harness for governed business execution. Install it in minutes, run it with your own model, and use it with Codex or another coding agent.

Do not frame Kentaro as an SDK alone. The immediate value is a usable harness with a CLI, project-level configuration, structured execution packages, gates, and evidence.

## Later Extensions

### External harness runtime adapter

HarnessRouter is a possible Phase 4 execution backend. Kentaro would submit a governed execution package to an external agent harness and receive status, artifacts, traces, and evidence. This adapter must remain optional.

Kentaro remains the policy and governance layer. HarnessRouter or a similar product is an execution substrate beneath it.

### Maysano Platform connection

Later, the Maysano Platform may manage portfolios, platform-based agents, shared governance, and enterprise deployment. Kentaro retains a useful standalone local mode and must not depend on Maysano for v0.1.

## Non-Goals for v0.1

- Replacing Codex or building a general-purpose coding agent.
- Running the Maysano platform agents locally inside every user installation.
- Requiring Docker or a cloud account.
- Supporting every agent framework or external harness.
- Building an enterprise multi-user platform before the local single-user flow works.
- Building a separate local business UI, portfolio view, or platform-hosted agent experience.

## Implementation Order

1. Create the Python package and `kentaro` CLI shell.
2. Implement `kentaro init --codex` and the project directory contract.
3. Implement one use-case and execution-package schema.
4. Connect the existing Open Data Products SDK and model configuration.
5. Implement artifact and evidence storage, validation, and report output.
6. Add tests, example projects, release automation, and PyPI publishing.
7. Add the MCP server using the same core services.
8. Evaluate the optional HarnessRouter adapter after the core flow is stable.

## Product Roadmap

The roadmap should protect one principle: prove a complete governed delivery loop before adding more agent frameworks, deployment modes, or enterprise features.

### Phase 0: Product Foundation

**Goal:** Establish a coherent open-source product that developers understand and trust.

**Deliverables:**

- MIT-licensed GitHub repository with a clear README and architecture.
- Python package skeleton, `pyproject.toml`, test setup, linting, and release workflow.
- Product vocabulary and schemas for use case, execution package, gate, artifact, and evidence.
- One demonstrable reference use case and realistic sample project.
- Clear boundary documentation: Kentaro Harness, Open Data Products SDK, Maysano Platform, and optional external harness runtimes.

**Exit condition:** A developer understands what Kentaro is, installs the development version, and runs the sample flow locally.

### Phase 1: Kentaro v0.1, Local Governed Harness

**Goal:** Deliver the smallest complete product loop for one person using Codex in one project.

**Deliverables:**

- Published `kentaro-harness` package on PyPI.
- `kentaro init --codex` project setup.
- CLI flow from use case to execution package, execution, evidence, and report.
- Open Data Products SDK integration with local or cloud model configuration.
- One explicit human approval gate and one evidence-verification step.
- Local project history, artifacts, and reports.
- One polished walkthrough that proves the outcome from start to finish.

**Exit condition:** A new user installs Kentaro, opens Codex in an existing project, completes one governed use case, and reviews the resulting evidence without manual product setup.

### Phase 2: Kentaro v0.2, Maysano Platform API

**Goal:** Prove a clean, usable contract between standalone Kentaro and the Maysano Platform.

Kentaro remains useful without Maysano. This phase adds an optional configured connection for organisations that want to manage local Kentaro work through the Maysano portfolio and platform experience.

**Deliverables:**

- Maysano API client and connection configuration.
- Authenticated read operations for products, objectives, use cases, and relevant platform context.
- Authenticated create and update operations that push Kentaro products, objectives, and use cases to Maysano.
- Stable external identifiers and idempotent synchronisation, so retried requests do not create duplicate objects.
- Explicit sync status, failures, conflict handling, and audit records in Kentaro.
- Contract tests covering both read and write API flows against a Maysano test environment.
- A complete demonstration: create a product, objective, and use case locally, post them to Maysano, then read the same objects and status back.

**Exit condition:** Kentaro and Maysano exchange products, objectives, and use cases reliably through tested read and write APIs. The API is ready for later platform workflow, reporting, and agent use.

### Phase 3: Kentaro v0.3, Agent-Client Integrations

**Goal:** Make Kentaro work natively with Codex, Claude Code, and OpenCode while retaining the CLI as the durable baseline.

**Deliverables:**

- Stdio MCP server exposing Kentaro actions as named tools.
- Codex, Claude Code, and OpenCode project integrations, with agent-specific instructions that use the same Kentaro core, CLI, schemas, and MCP server when it is available.
- Structured JSON output from every key CLI command.
- Reusable templates for several use-case types.
- Package versioning, change history, reruns, and comparison of evidence across versions.
- Improved gate handling, including human approval, rejection, revision, and audit trail.

MCP tools should include the existing product, objective, use-case, package, evidence, and Maysano synchronisation actions. MCP must call the same core services and API client used by the CLI. Agent-client integrations must not create parallel workflows, schemas, or execution engines.

**Exit condition:** Codex, Claude Code, and OpenCode perform the normal Kentaro workflow through the shared CLI or, where configured, named MCP tools, and push approved work to Maysano without the user explaining the process each time.

### Phase 4: Kentaro v0.4, Optional External Execution Runtimes

**Goal:** Add optional external execution runtimes, such as HarnessRouter, without changing Kentaro's governance and execution-package logic.

**Deliverables:**

- Stable internal external-runtime interface.
- Optional adapter for HarnessRouter or a similar external execution runtime, initially with Codex as the supported backend.
- Runtime status, streamed progress, files, and structured failure mapping into Kentaro evidence.
- Strict secret handling and customer-controlled credentials.
- Clear deployment guidance for local, private-cloud, and approved enterprise environments.

**Exit condition:** The same Kentaro package runs through its built-in local execution route or an external harness runtime, while producing comparable evidence.

### Phase 5: Maysano Portfolio and Enterprise Operations

**Goal:** Expand the tested Kentaro-to-Maysano API connection into portfolio-level decision-making and platform-hosted agents.

**Deliverables:**

- Synchronisation of approved Kentaro packages, evidence, outcomes, and execution status to Maysano.
- Portfolio view of use cases, delivery status, risks, dependencies, and outcome evidence.
- Platform agents that analyse and assist through the Maysano GUI.
- Enterprise administration, shared policy, and organisation-level governance.

**Exit condition:** Kentaro remains useful as a standalone local harness, while Maysano adds portfolio coordination and managed enterprise operations above it.

## Roadmap Rules

- Phase 1 is the only active build target now.
- Each phase needs a working user journey and a demonstration before the next phase starts.
- Do not add MCP, a second agent framework, or an external runtime before the preceding phase is proven.
- Keep the core product usable without a Maysano account.
- Keep all platform agents in Maysano. Kentaro runs the local SDK, configured models, governed packages, and local execution workflow.
