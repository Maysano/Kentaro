# Demo walkthrough

In a Codex chat for this repository, ask "Give me a demo portfolio briefing."
The `kentaro-portfolio-brief` skill runs the command below and returns a sourced answer in chat.
You can follow up with "Which records lack owners?" or request a saved Markdown report.
The skill is stored under `.agents/skills/` for repository discovery. A new chat may be
needed to discover newly added skills; root instructions also link to the workflow.


From the repository root run the brief command in docs/configuration.md. Check that uc-2
has missing ownership, inspect its source in examples/demo-portfolio/portfolio.json, and
compare the recommendation with the source facts. Counts derive only from listed scoped records.

To save a reviewable output in PowerShell:

```powershell
New-Item -ItemType Directory -Force reports
python -m kentaro --config examples/configs/demo.toml portfolio brief | Out-File -Encoding utf8 reports/demo-brief.md
```

Ask "Show me the demo portfolio dashboard" to display a rendered read-only snapshot directly in the conversation.
Expand record titles to inspect versions, timestamps, references and relationships.
Ask for a refresh to retrieve a new snapshot. Delivery health remains unknown where inputs are absent.

Use-case review, product coverage, delivery readiness and decision trace remain unimplemented.
