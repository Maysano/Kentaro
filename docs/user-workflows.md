# Demo walkthrough

From the repository root run the brief command in docs/configuration.md. Check that uc-2
has missing ownership, inspect its source in examples/demo-portfolio/portfolio.json, and
compare the recommendation with the source facts. Counts derive only from listed scoped records.

To save a reviewable output in PowerShell:

```powershell
New-Item -ItemType Directory -Force reports
python -m kentaro --config examples/configs/demo.toml portfolio brief | Out-File -Encoding utf8 reports/demo-brief.md
```

Use-case review, product coverage, delivery readiness, decision trace and dashboard remain unimplemented.
