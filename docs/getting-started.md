# Getting started with Kentaro

Kentaro v0.1 is a read-only Agentic Maysano Harness. A package installation is enough
to retrieve and explain sourced synthetic portfolio context, create a local dashboard,
and keep its outputs in an automatically created `.kentaro/workspace/` directory.

## Install

Kentaro needs Python 3.11 or later.

```shell
python -m pip install kentaro
```

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
