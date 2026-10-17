# Local portfolio walkthrough

Run the packaged synthetic briefing from any working directory after installing
Kentaro:

```shell
kentaro portfolio brief
```

The output identifies the synthetic source references. If a record has no owner,
Kentaro presents that as a source limitation rather than inferring an owner. Counts
derive only from the records in the bounded synthetic context.

To generate a dashboard, run:

```shell
kentaro dashboard
```

Kentaro creates `.kentaro/workspace/` automatically, writes a fresh timestamped HTML
file there, and prints its complete path. It never overwrites an existing dashboard.

In a Codex chat for this repository, ask “Give me a demo portfolio briefing” or
“Show me the portfolio dashboard.” The skills retrieve the same sourced read-only
context and expose source details. The demo is not a live platform connection or a
model-assisted analysis.

For an authorised live pilot read, use the guided setup first:

```shell
kentaro configure maysano
kentaro portfolio brief --source maysano
```

The external pilot omits ownership, approvals, decisions, risks, evidence, and
milestones. Kentaro marks those fields unavailable. It never substitutes demo data
for a live result, executes actions, or writes to the platform.
