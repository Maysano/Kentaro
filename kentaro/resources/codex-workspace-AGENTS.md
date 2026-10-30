# Kentaro local business-design workspace

This is a local Kentaro workspace. Kentaro is an open-source, read-only Maysano
harness. It is not Maysano's system of record and must not be presented as approving
work, accessing business systems, or establishing production readiness.

## Use the installed Kentaro skills

The `.agents/skills/` directory contains the complete Kentaro skill set. When a
request matches a Kentaro skill, read that skill's `SKILL.md` completely before
acting and follow its workflow. Use `kentaro-objective-design` for business
objectives, `kentaro-use-case-design` for use cases, `kentaro-ai-product-design`
for AI products, and `kentaro-data-product-design` for reusable data products.
Use `kentaro-portfolio-analysis` and `kentaro-portfolio-readiness` to assess a
design, and `kentaro-masterclass` only when the learner explicitly chooses the
fictional course scenario. The list, briefing, dashboard, and ODPS skills cover
their named requests. Never ask a learner to install skills or clone a repository.
Run Kentaro through the installed `kentaro` command (for example, `kentaro design
propose`), not `python -m kentaro`; the latter can select a different Python
installation in Codex's terminal. If it is unavailable, run `kentaro doctor` and
give the learner its displayed fix rather than guessing an internal package path.

## Business-design workflow

For a local business-design conversation, work only below `.kentaro/workspace/`.
The saved `DesignPortfolio` JSON file is authoritative; conversation history and
rendered files are not. For a new blank design, create a generic portfolio with
`kentaro design init`; use `kentaro design propose` for a bounded first draft from
a short business problem. Use a scenario only when the learner explicitly requests it.

After every relevant learner input, incorporate the information as sourced claims,
validate the saved portfolio, refresh the adjacent `engagement-state.json`, and use
that state to identify the highest-priority missing requirement or unresolved human
decision. Preserve confirmed claims unless the learner corrects them. Keep proposed
and unknown claims visibly labelled. Do not infer AI involvement: conventional
automation and non-AI use cases are valid.

Create locally generated ODPS, ODPC, and ODPG specifications only as supporting
artefacts and validate ODPS with the installed pinned SDK. Generate the local,
read-only visual canvas and reports from the saved portfolio. They show declared
relationships, evidence labels, gaps, and dependencies; they do not establish
business approval, data access, compliance, safety, or production readiness.

Never send customer data, credentials, secrets, or confidential records to a hosted
provider without explicit authorization and the required acknowledgement.
