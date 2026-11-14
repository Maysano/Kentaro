# Business-design journey evaluation

`kentaro design evaluate-journey` evaluates a recorded agent interaction against a
synthetic `KentaroBusinessDesignValidationCase`. It is an acceptance harness for
ordinary Business Owner prompts, not a language model and not an approval workflow.

The reusable case defines ordered Business Owner turns, source-safe synthetic graph
snapshots, and observable expectations. The supplied customer risk-assessment case
covers incomplete input, reuse, alternatives, an explicit decision, a changed decision,
a handover skip attempt, graph revalidation, and final confirmation.

An adapter records one trace event per turn:

```json
{
  "turn_id": "incomplete",
  "assistant": {
    "response": "The current proposal remains editable and records those gaps.",
    "next_question": "Which outcome should we measure first?"
  },
  "portfolio": { "model": "DesignPortfolio" },
  "observations": { "handover": "blocked" }
}
```

The embedded portfolio is authoritative for validation. `response`, `next_question`,
and `observations` are adapter-supplied evidence labels; they do not authenticate an
actor, grant approval, or establish business truth. The evaluator independently checks
each portfolio snapshot for graph provenance, readiness findings, alternatives, decision
history, completion gates, and changed-evidence impact.

Run it with case and trace files under `.kentaro/workspace/`:

```shell
kentaro design evaluate-journey \
  --case .kentaro/workspace/journeys/customer-risk-case.json \
  --trace .kentaro/workspace/journeys/customer-risk-trace.json
```

To extend a case, add a new turn rather than changing an existing prompt or expectation.
Add only observable capability-specific expectations, then provide a matching trace
snapshot and regression assertion.
