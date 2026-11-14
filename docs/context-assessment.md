# Local context assessment

`kentaro context assess` reviews one local UTF-8 Markdown or text source for
visible indicators that affect whether an AI tool can use it reliably. It is a
local, deterministic preparation step for business design; it does not call a
model, Maysano, or another service.

```shell
kentaro context assess \
  --input ./policy.md \
  --intended-use "Answer staff questions from this policy"
```

By default Kentaro writes a fresh directory under `.kentaro/workspace/` with:

- `context-assessment.json`: the machine-readable evidence record.
- `context-assessment.md`: the human-readable report.

Use `--output-dir .kentaro/workspace/context/hr-policy-v1` when a known local
directory is more useful. Kentaro refuses to overwrite a prior assessment in
that directory.

## What the assessment observes

The report has seven dimensions:

1. readability and source coverage;
2. terms and terminology;
3. practical interpretation;
4. decision rules and exceptions;
5. human and AI boundary;
6. ownership and freshness; and
7. verification cases.

Every observed signal is cited by source line. A missing signal is labelled
`not_evident` or `needs_review`, never converted into a fact about the wider
organisation. The report estimates a current indicator level from 1 to 4 and a
target level from the stated use:

| Level | Meaning in Kentaro |
|---|---|
| 1 | Source material only |
| 2 | Readable, traceable source material |
| 3 | Operational interpretation indicators are present |
| 4 | Governance and verification indicators are present |

An agent/workflow/action/decision use defaults to target level 4; content
generation or review defaults to level 3; question-answering defaults to level
2 unless the user supplies a more consequential purpose.

## Limits and next steps

The command is deliberately not a semantic audit. It cannot establish content
accuracy, approval, legal compliance, access rights, production readiness, or
authority to act. It reads only `.md`, `.markdown`, and `.txt` sources; convert
PDFs, images, diagrams, and tables into reviewed text before running it.

If the material is intended for an AI product, treat assessment findings as
input to local design work. Record only user-confirmed or sourced proposed
claims in a `DesignPortfolio`, then define the AI product's human oversight and
evaluation through the existing ODPC workflow.
