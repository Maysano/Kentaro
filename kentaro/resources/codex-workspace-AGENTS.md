# Kentaro local business-design workspace

This folder is a local Kentaro workspace. Kentaro is an open-source, read-only
Maysano harness. It is not Maysano's system of record and must not be presented
as approving work, accessing business systems, or establishing production readiness.

For a local business-design conversation, work only below `.kentaro/workspace/`.
The saved `DesignPortfolio` JSON file is authoritative; conversation history and
rendered files are not. For a new blank design, create a generic portfolio with
`kentaro design init`. Use a scenario only when the user explicitly requests one.
For a bounded first draft from a short business problem, use `kentaro design propose`.

After each relevant user input, preserve confirmed claims unless the user corrects
them, validate the portfolio, refresh its adjacent `engagement-state.json`, and use
that state to identify the next missing requirement or unresolved human decision.
Keep proposed and unknown claims visibly labelled. Do not infer AI involvement:
conventional automation and non-AI use cases are valid.

Generate the local read-only visual canvas and reports from the saved portfolio.
They show declared relationships, evidence labels, gaps, and dependencies; they do
not constitute business approval, data access, compliance, safety, or production
readiness. Never send customer data, credentials, secrets, or confidential records
to a hosted provider without explicit authorization and the required acknowledgement.
