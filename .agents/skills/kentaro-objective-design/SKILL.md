---
name: kentaro-objective-design
description: Guide a user to create or improve a local DesignPortfolio business objective with measurable outcomes, ownership, evidence, and explicit gaps. Use for business-objective design, not Maysano portfolio updates.
---

# Kentaro Business Objective Design

Work only with a local `DesignPortfolio` under `.kentaro/workspace/`. Ask for the business
problem, expected outcome, KPI, baseline, target, time horizon, accountable owner, and evidence.
Do not fill a missing answer with a plausible value: use a canonical Claim with `unknown`,
`assumed`, or `proposed` status and its source reference.

For a new connected engagement, initialize the company graph first through `kentaro design
propose` (its default `--company-source auto` uses configured Maysano read access). Treat
retrieved objectives as existing sourced context, not proposed local objectives; inspect related
objectives before framing a new one. If graph context is unavailable, state that this is a local,
unverified design rather than claiming absence or duplication.

For a minimal initial business statement, first create a provisional objective and candidate
success measures rather than asking for every KPI field. Label proposed outcome, baseline, target,
time-horizon, and ownership content explicitly. Ask only the single most consequential objective
question after the first connected proposal exists; require explicit user confirmation before
changing a proposal to `user_confirmed`.

Create or update objectives with `kentaro design init`, `add-object`, and `set-claim`, then run
`kentaro design validate`. Keep measurable outcome fields as canonical Claims, including nested
baseline and target claims when they have different evidence.

When this changes an existing design, regenerate its adjacent visual canvas and refresh or reopen
it beside the Codex conversation. The learner should see the updated business target without
having to request the canvas again.

This is local design work only. It does not update Maysano, request approval, or grant authority.
