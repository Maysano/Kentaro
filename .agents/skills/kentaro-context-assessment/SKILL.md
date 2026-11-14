---
name: kentaro-context-assessment
description: Assess one local Markdown or text policy, handbook, or instruction source for traceable AI-context readiness indicators. Use when a user asks whether supplied material can support AI question answering, content work, an assistant, or an agent. Do not use this as approval, compliance, or production-readiness assessment.
---

# Kentaro Context Assessment

Use this skill for one source document at a time. Kentaro's assessment is local
and deterministic: it records visible text indicators and source-line evidence;
it does not use a model, contact Maysano, or establish that the material is
correct, approved, compliant, or safe for production.

## Workflow

1. Confirm the user has authority to process the material in their local AI
   environment. Do not ask them to paste secrets or confidential material into
   chat when a local file is available.
2. Obtain the intended AI use in plain language. If it is not supplied, ask
   only what the AI is meant to do with the source.
3. Run:

   ```shell
   kentaro context assess --input <path-to-source.md> --intended-use "<intended use>"
   ```

   The input must be UTF-8 `.md`, `.markdown`, or `.txt`. For PDFs, images,
   diagrams, or tables, request a reviewed text conversion first. Never claim
   to have interpreted visual content that the source text does not contain.
4. Read `context-assessment.md` and `context-assessment.json` from the printed
   `.kentaro/workspace/` output directory. Present the current indicator level,
   target level, evidence-linked gaps, and limits.
5. Keep every distinction explicit:
   - **Observed** means a configured indicator appeared on a cited source line.
   - **Needs review** means a potentially relevant gap or ambiguity needs an
     accountable human's interpretation.
   - **Not evident** means the indicator was not found in this one source; it
     may exist elsewhere.

## Boundaries

- Do not convert an indicator into a claim that the organisation has approved a
  rule, owns a policy, meets legal obligations, or is production-ready.
- Do not add assessment results to a `DesignPortfolio` as confirmed facts. A
  user may separately record a sourced proposed claim or an explicit human
  decision when appropriate.
- The workload class is indicative and derived from visible gaps; it is not a
  time estimate or a delivery commitment.
- Kentaro is read-only with respect to Maysano. This workflow creates only
  local ignored workspace artifacts.
