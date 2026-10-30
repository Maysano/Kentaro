# Getting started with Kentaro

Kentaro v0.2 is a read-only Agentic Maysano Harness. A package installation is enough
to retrieve and explain sourced synthetic portfolio context, create a local dashboard,
or start a deterministic local business-design portfolio. Outputs stay in an
automatically created `.kentaro/workspace/` directory.

## Install

Kentaro needs Python 3.11 or later.

```shell
python -m pip install "kentaro==0.2.6"
```

## Prepare the workspace from Codex

Create an empty project folder in Codex. In the first Codex chat, send this message:

> Set up Kentaro in this project. Run `kentaro setup codex`, then `kentaro doctor`,
> on my behalf. Do not clone the Kentaro repository. When the checks pass, give me a
> short plain-language summary with **Setup**, **Health check**, and **What happens
> next**. Confirm the 13 skills, local workspace, ODPS validation, and visual canvas;
> then tell me to start a fresh Codex conversation here before we begin the
> DesignPortfolio, with one ready-to-send business prompt.

Codex runs the installed setup and health-check commands itself. Setup installs all 13
Kentaro skills in `.agents/skills/`, adds a managed Kentaro section to `AGENTS.md`,
and creates the local workspace. Existing learner instructions and modified skills
remain in place; replacement always needs explicit approval.

When Codex reports a passing health check, start a **new Codex conversation in the
same folder**. This is required because Codex loads `AGENTS.md` and skills when a
conversation starts. The original conversation is only for setup.

In the fresh conversation, describe the business problem in plain language, for
example:

> Our bank's customer risk assessments take too long. Help me improve this process.

Kentaro creates the connected, evidence-labelled local DesignPortfolio and canvas
from that input. It preserves unknowns and asks the next most important business
question; it does not select the course scenario or assume AI is required.

## Run the local synthetic demo

```shell
kentaro demo
```

The command makes no HTTP request and needs no API key, configuration file, fixture
path, or repository checkout. It prints a portfolio briefing and reports the complete
path of the newly written timestamped dashboard.

## Get a briefing or dashboard

```shell
kentaro portfolio brief
kentaro dashboard
```

Both commands use the synthetic data packaged with Kentaro. The dashboard command
creates `.kentaro/workspace/` when needed, reports the full output path, and uses a
new timestamped filename every time.

## Start a local business design

v0.2 also supports a separate local `DesignPortfolio` for business objectives, use
cases, AI products, data products, and their evidence-labelled relationships:

```shell
kentaro design init --title "Service Transformation" --portfolio-id service-transformation --output .kentaro/workspace/design/service-transformation.json
kentaro design validate --input .kentaro/workspace/design/service-transformation.json
```

Generic design commands do not select an example. Use an explicit scenario only when wanted;
the Udemy Masterclass remains available through its compatible `kentaro masterclass` commands.
See [Local DesignPortfolio](design-portfolio.md) for editing, reporting, scenarios, and ODPS
validation.

## Connect a read-only Maysano source

Only configure a live source when you have a Maysano-issued read credential and an
authorised pilot endpoint. The guided setup stores its configuration in the ignored
local workspace; you do not need to copy or edit a hidden file.

```shell
kentaro configure maysano
kentaro portfolio brief --source maysano
```

The live pilot remains read-only. Its documented context does not include owners,
approval history, decisions, risks, evidence, or delivery milestones. Kentaro reports
those limits as unavailable and never fills them with synthetic values.

## Where to go next

See [advanced configuration](configuration.md) for team TOML profiles and custom
environments. See the [governance and delivery object model](governance-and-delivery-object-model.md)
for the local versioned objects, deterministic classifications, review-readiness,
revocation clause, secrecy controls, and append-oriented evidence exports.
