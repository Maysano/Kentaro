# Kentaro local business-design workspace

This is a local Kentaro workspace. Kentaro is an open-source, read-only Maysano
harness. It is not Maysano's system of record and must not be presented as approving
work, accessing business systems, or establishing production readiness.

An empty learner workspace does not need to be a Git repository. Do not treat a
failed `git status` as a setup failure, and do not ask the learner to initialize or
clone a repository in order to use Kentaro.

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

## Finish a setup conversation clearly

When the learner has asked you to run `kentaro setup codex` and `kentaro doctor` in
this same conversation, do not reduce a successful result to a version number and a
request to restart. Use the `learner_handoff` returned by `kentaro doctor` to close
with these short headings in plain language:

- **Setup** — confirm that `AGENTS.md` and all 13 Kentaro skills are ready.
- **Health check** — confirm the local workspace, ODPS validation, and local visual
  canvas are ready. Do not imply that this is business approval or production
  readiness.
- **What happens next** — tell the learner to start a new Codex conversation in the
  same folder, then give the `first_business_prompt` exactly as a ready-to-send
  example.

Do not begin business design in the setup conversation. Do not ask the learner to
run any more terminal commands, clone a repository, or explain Kentaro internals.

## First business prompt

When the learner's first message describes a business problem and this workspace has
no DesignPortfolio, create the initial local portfolio by running `kentaro design
propose` with the learner's exact business input. A completely empty portfolio created
during setup (no objects, relationships, claims, or learner-supplied content) is also
treated as no DesignPortfolio: replace that empty file with the proposed portfolio so
there is one authoritative design. Never replace a portfolio containing learner input.
Save the portfolio under `.kentaro/workspace/design/` with its adjacent generated
outputs. Do not create only an empty `design init` portfolio in response to that
business input, do not select a scenario, and do not invent a KPI, owner, system,
policy, or AI requirement. The proposal must retain supplied facts as user-confirmed
and label generated candidates as proposed or unknown. `kentaro design propose` also
creates a local suggested design review package automatically; it is for review and
evaluation, not a handover request and not an approval step. Use `kentaro design
handover prepare-review` only to create equivalent material for an existing portfolio.
Open the visual canvas in Codex beside the conversation as the default companion to the
first proposal; do not merely provide a file link and leave the learner to open it. Show
the learner the canvas, concise package summary, and its confirmed, proposed, and unknown
items. Do not turn its discovery gaps into a sequential approval questionnaire or wait for
owners, KPI targets, or confirmation before producing the suggested package.

If the learner explicitly asks for an empty DesignPortfolio before giving a business
problem, use `kentaro design init` instead. If this workspace was set up during the
current Codex conversation, tell the learner to start a fresh conversation in this
same folder before using this workflow: Codex loads `AGENTS.md` and skills when a
conversation starts.

After every relevant learner input, incorporate the information as sourced claims,
validate the saved portfolio, refresh the adjacent `engagement-state.json`, and use
that state to identify review topics, missing requirements, and unresolved human
decisions. Preserve confirmed claims unless the learner corrects them. Keep proposed
and unknown claims visibly labelled. Answer the learner's immediate request before
raising a follow-up question; do not require an answer merely to keep or review a
suggested package. After a material design update, regenerate the adjacent visual canvas
from the saved portfolio, then refresh or reopen that same canvas in Codex beside the
conversation. Treat the visual view as a live, read-only companion: it must visibly
reflect the latest saved design, rather than a stale first-draft snapshot. For a supported, sufficiently framed business
pattern, compare a conventional path with a proposed human-in-the-loop AI-product
option and two or three smaller consumer-scoped, domain- or subdomain-oriented
information-product candidates. Do not split candidates merely by workflow step,
screen, or report: each candidate needs a distinct business boundary, accountable
domain owner, authoritative sources, and a reuse hypothesis to be refined. Do not
infer that AI is required: the conventional path remains valid, and AI
suitability, oversight, evaluation, and prohibited actions must remain proposed or
unknown until the business user confirms them.

Create locally generated ODPS, ODPC, and ODPG specifications only as supporting
artefacts and validate ODPS with the installed pinned SDK. Generate the local,
read-only visual canvas and reports from the saved portfolio. They show declared
relationships, evidence labels, gaps, and dependencies; they do not establish
business approval, data access, compliance, safety, or production readiness.
Only `kentaro design handover generate` creates the separate final reviewed ZIP and
requires explicit confirmation. Never request that confirmation while the learner is
simply exploring or evaluating a suggested design package.

Never send customer data, credentials, secrets, or confidential records to a hosted
provider without explicit authorization and the required acknowledgement.
