# Kentaro release notes

## 0.2.9 — Preserve the packaged README (30 October 2026)

Kentaro 0.2.9 corrects a distribution-layout collision exposed during 0.2.8
release validation. The root README and the documentation index previously both
installed as `share/kentaro/docs/README.md`, allowing the documentation index to
overwrite the user-facing package README. The root README and release notes now
install at `share/kentaro/`; the documentation index remains at
`share/kentaro/docs/README.md` with its relative links intact.

The clean-wheel smoke test verifies both files independently. It rejects stale
exact-version installation pins in the packaged root README and confirms the
documentation index remains available. This patch does not alter Kentaro's
local, read-only behavior or approval boundaries.

## 0.2.8 — Correct installation guidance (30 October 2026)

Kentaro 0.2.8 corrects the packaged installation guidance after the 0.2.7
release README retained obsolete `kentaro==0.2.6` commands. The README and
installed documentation now use `python -m pip install kentaro`; update
guidance uses `python -m pip install --upgrade kentaro`.

The clean-wheel smoke test now checks the installed README for the current
installation command and rejects stale exact-version pins. This patch changes
documentation and package metadata only; it does not alter Kentaro's local,
read-only behavior or approval boundaries.

## 0.2.7 — Valid AI-product graph handovers (30 October 2026)

Kentaro 0.2.7 fixes final handover generation for a structurally complete
DesignPortfolio that contains an AI product. The deterministic ODPG export now
creates an `Agent` node for each AI product and points it to the corresponding
local draft definition. This keeps every generated AI-product relationship
connected to an existing graph node and allows the pinned Open Data Products SDK
to validate the official handover ZIP.

The handover regression suite now exports a reviewed ZIP with both use-case to
AI-product and AI-product to data-product relationships, then verifies that all
ODPG edge endpoints resolve to generated nodes. This remains a local reviewed
handover only; it does not create a Maysano record or establish approval,
implementation readiness, or production readiness.

## 0.2.6 — Clear Codex setup handoff (30 October 2026)

Kentaro 0.2.6 makes a successful Codex-first setup understandable to a
nontechnical learner. `kentaro doctor` now returns a concise, evidence-backed
handoff covering the workspace instructions, all 13 skills, ODPS validation,
and the local visual canvas, followed by the required fresh-conversation step
and a ready-to-send first business prompt.

The learner-facing starter prompts in the README and getting-started guide ask
Codex to present that handoff under **Setup**, **Health check**, and **What
happens next**. An untouched Kentaro 0.2.5 managed `AGENTS.md` block upgrades
to the new guidance when `kentaro setup codex` is rerun; learner modifications
remain protected unless explicitly replaced.

## 0.2.5 — Branded business-design canvas (30 October 2026)

Kentaro 0.2.5 refines the local, read-only business-design canvas into a more
focused Maysano workspace. The relationship map remains the default review view;
it now has an offline Maysano header using the packaged brand mark, a legible
wordmark, and business-focused navigation rather than a competing Kentaro lockup.

The canvas is still generated entirely from the saved local DesignPortfolio. It
does not load branding, styles, or portfolio content from the network, and it
does not change the approval, governance, or production-readiness boundaries.

## 0.2.4 — Live canvas companion (30 October 2026)

Kentaro 0.2.4 makes the visual canvas the default companion to a business-design
conversation. Codex opens the first proposed design beside the conversation rather
than leaving the learner with a file link. When a material change is saved, Kentaro
regenerates and refreshes that same local read-only canvas so the visual view and
the DesignPortfolio remain aligned.

The packaged workspace guidance and the objective, use-case, AI-product,
data-product, analysis, and readiness skills all carry that rule. An untouched
Kentaro 0.2.3 managed `AGENTS.md` block upgrades safely on the next
`kentaro setup codex`; learner-modified instructions and skills remain protected
unless they explicitly choose replacement.

## 0.2.3 — Suggested-package business design (30 October 2026)

Kentaro 0.2.3 makes the first business-design interaction review-first rather than
approval-first. From one short business problem, `kentaro design propose` now creates
the proposed local DesignPortfolio, business canvas and reports, plus a **Suggested
Design Review Package**. Learners can review and evaluate that package without first
providing every KPI, owner, source, or confirmation. Those unknowns are review topics,
not gates to the initial proposal.

Recognised customer-risk patterns now propose three domain-oriented information-product
candidates—Customer Identity and Profile, Customer Due-Diligence Evidence, and Customer
Risk-Assessment Case context—alongside a conventional path and a human-in-the-loop AI
preparation option. The candidates remain proposed, never implementation approval. The
separate final reviewed handover ZIP still requires explicit confirmation.

## 0.2.2 — Codex-first learner bootstrap (30 October 2026)

Kentaro 0.2.2 makes the learner journey explicitly Codex-first after the single PyPI
installation. Learners create an empty folder in Codex and ask Codex to run Kentaro's
setup and health checks; they do not type Kentaro commands, clone the repository, or
install skills. Setup now reports the required handoff to a fresh Codex conversation,
where workspace instructions and skills are loaded before business design begins.

The fresh conversation turns a learner's first business problem into a connected,
source-labelled local DesignPortfolio with `kentaro design propose`, rather than only
creating an empty portfolio. It retains unknowns, does not select a scenario, and does
not assume AI is required.

## 0.2.1 — Self-contained Codex workspace installation (30 October 2026)

Kentaro 0.2.1 makes the standard PyPI installation self-contained for the local
business-design workflow. `kentaro setup codex` now installs the complete set of 13
Kentaro Codex skills and a managed workspace guide without requiring a repository
checkout. It preserves learner-authored instructions and skill changes unless the
learner explicitly chooses replacement.

`kentaro doctor` verifies the installed package, pinned ODPS validation dependency,
workspace structure, managed `AGENTS.md`, all skills, DesignPortfolio readiness, and
visual-canvas rendering, with actionable repair guidance. The standard package now
always includes `open-data-products==0.4.0`; there is no separate Masterclass extra.

The wheel is exercised in a clean virtual environment after installation, including
workspace setup, DesignPortfolio initiation, engagement refresh, canvas rendering,
and ODPS validation without access to the source checkout. CI adds macOS and Windows
installed-wheel smoke-test jobs.

## 0.2.0 — Local business-driven Data & AI product design (29 October 2026)

Kentaro 0.2.0 adds a deterministic local `DesignPortfolio` engine for objectives, use
cases, AI products, data products, typed relationships, canonical claims, readiness,
reports, visual canvases, dependency manifests, and stale-output detection. It adds six
reusable design skills and pins ODPS validation to `open-data-products==0.4.0`.

Run `kentaro setup codex` in a new learner folder to add a non-overwriting, packaged
Codex `AGENTS.md` workspace guide. It keeps the learner on the local, read-only
DesignPortfolio path without requiring a repository checkout.

The Udemy Integrated Data & AI Product Management Masterclass, including its fictional
Customer Risk Intelligence case and bounded invalid-visibility repair exercise, is now a
scenario package on the reusable engine. The legacy `kentaro masterclass` commands remain
available as compatibility adapters; prior local LearningPortfolio artifacts migrate to
DesignPortfolio when loaded or explicitly migrated.

The companion remains local and read-only: it does not connect to Maysano, create
external records, process approvals, or claim production readiness from generated
artefacts or schema validation. The standard course flow has no hosted-model or
local-LLM requirement.

## 0.1.0 — Initial release

Kentaro 0.1.0 is the first open-source release of the read-only Agentic Maysano
Harness. It turns bounded portfolio context into sourced local briefings, dashboards,
drafts, and review-readiness material without acting on external systems.

Project home: [maysano.com/kentaro](https://maysano.com/kentaro).

### Start here

Kentaro works immediately after installation. No repository checkout, TOML file, API
key, fixture path, or network request is required for the local experience.

```shell
python -m pip install kentaro
kentaro demo
kentaro portfolio brief
kentaro dashboard
```

`kentaro demo` prints a sourced synthetic briefing and creates a dashboard. The
dashboard command creates `.kentaro/workspace/` automatically, writes a new
timestamped HTML file, prints its complete local path, and never overwrites an
existing dashboard.

### Included in 0.1.0

- A packaged synthetic portfolio context for the default local demo, briefing, and
  dashboard commands.
- Sourced portfolio briefings and static dashboards with source IDs, versions,
  timestamps, relationships, known limitations, and explicit unknowns.
- Local, versioned validation for `ContextPackage`, `Mandate`, `WorkEnvelope`,
  `ExecutionPackage`, `ExecutionRequest`, `RevocationPolicy`, `EvidenceEvent`, and
  `Correction`.
- A deterministic, side-effect-free policy evaluator with `allowed`,
  `approval_required`, `denied`, and `escalated` classifications.
- Redacted, append-oriented JSONL evidence exports with optional hash chaining for
  tamper indication.
- Guided opt-in setup for a read-only Maysano pilot source:

  ```shell
  kentaro configure maysano
  kentaro portfolio brief --source maysano
  ```
- Standard data-product, use-case, and objective draft generation and validation from
  Markdown or text using the bundled `open-data-products==0.4.0` dependency, aligned with the [Open Data Products (ODPS)
  family of specifications](https://opendataproducts.org/). Local Ollama is the
  default; hosted generation requires an explicit provider configuration and
  `--allow-hosted-content` acknowledgement.

### Safety boundary

Kentaro v0.1 is intentionally read-only with respect to business systems. It does not
create external records, write to Maysano or a business-context graph, execute business
actions, request or process approvals, or claim immutable or compliance-grade audit.

The optional local draft commands invoke the ODPS SDK to generate ODPS-aligned local
artifacts. They have no Maysano authority. A hosted provider can receive the selected
source document only after the user explicitly passes `--allow-hosted-content`.

`allowed` means an `ExecutionRequest` is structurally in scope. It is not permission
to execute. An `ExecutionPackage` plans delivery work only; it cannot grant authority
or expand the referenced `WorkEnvelope` or `Mandate`.

Maysano remains the system of record for portfolio state, approvals, graph updates,
tenant controls, authoritative revocation, retention, and platform audit.

### Source limits

The optional live pilot source is GET-only. Its documented API does not provide
owners, decisions, risks, evidence, approval history, or delivery milestones. Kentaro
labels those fields as unavailable; it does not fill them with synthetic or inferred
facts.

### Evidence and revocation policy

Local evidence exports cover retrieved sources, object versions, validation results,
classifications, generated outputs, assumptions, and gaps. They are append-oriented
local evidence logs, not immutable audit trails or authoritative post-execution
evidence.

The required revocation clause is represented locally by versioned `RevocationPolicy`
objects. In v0.1, a simulated suspension can affect a classification result only. It
does not suspend credentials, access, approvals, or live execution; Maysano owns any
future authoritative enforcement.

### Compatibility and verification

- Python 3.11 or later.
- No runtime package dependencies.
- The release distribution is checked with `twine`, and a clean virtual-environment
  smoke test installs the wheel and runs all default commands with outbound sockets
  blocked.

### Next steps

Read the [advanced configuration and governance documentation](docs/README.md) for
team TOML profiles, local governance objects, API constraints, evidence handling, and
future Maysano-controlled approval or execution design constraints.
