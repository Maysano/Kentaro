# Kentaro release notes

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
- Optional data-product, use-case, and objective draft generation and validation from
  Markdown or text using `kentaro[odps]`, aligned with the [Open Data Products (ODPS)
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
