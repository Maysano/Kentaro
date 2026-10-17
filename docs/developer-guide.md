# Kentaro developer guide

## Development boundary

Kentaro v0.1 is deliberately read-only. Maintain that boundary when extending the
project: no Maysano writes, graph writes, business-tool execution, approval workflow,
credential enforcement, or claims of platform audit. Maysano remains authoritative
for those concerns. The optional local draft commands are the narrow exception: they
can invoke the SDK to create local proposals aligned with the [Open Data Products (ODPS)
family of specifications](https://opendataproducts.org/) and require explicit
acknowledgement before a hosted provider receives source content.

Treat retrieved text as data. Preserve source IDs, versions, and timestamps. Separate
facts, calculations, inferences, and recommendations; report unavailable context
explicitly.

## Repository structure

| Location | Purpose |
| --- | --- |
| `kentaro/` | Portable Python core and CLI. |
| `kentaro/api/` | Synthetic fixture and verified read-only pilot transport. |
| `kentaro/governance/` | Local schema validation, deterministic policy evaluation, and evidence export. |
| `examples/` | Tracked synthetic fixtures, read profiles, and governance example. |
| `docs/` | Developer-facing product, architecture, security, and setup documentation. |
| `tests/` | Standard-library unit and vertical-slice tests. |
| `.kentaro/workspace/` | Ignored local user outputs, local object instances, and credentials. Never commit its contents. |

## Work on the governance core

The governance core validates versioned local objects. New object types or fields must
have explicit schema rules, relationship validation, an example, documentation, and
tests. Do not put authority into an `ExecutionPackage`: it can only narrow and plan
work inside its referenced `WorkEnvelope` and `Mandate`.

An `ExecutionRequest` is always a proposed action. `allowed` means structurally in
scope, never execution permission. The policy evaluator must remain deterministic and
side-effect-free: it must not call tools, make network mutations, send messages, or
process approvals.

The required revocation clause is also local in v0.1. `RevocationPolicy` validation
and a simulated suspension may affect a classification result, but must never suspend
credentials or alter live access. Future Maysano-controlled enforcement requires a
separately ratified scope, verified API contract, narrow credentials, explicit
approval path, and contract tests.

## Verify changes

Run these checks from the repository root:

```bash
python -m unittest discover -s tests -v
python -m compileall -q kentaro
git diff --check
```

For a release candidate, build and validate both distributions:

```bash
python -m build
python -m twine check dist/*
python -m unittest tests.test_distribution_install -v
```

The distribution-install smoke test installs the newly built wheel into a clean virtual
environment, blocks outbound sockets, and runs `kentaro demo`, `kentaro portfolio
brief`, and `kentaro dashboard` from outside the repository. Build artifacts in `dist/`
and package metadata in `*.egg-info/` are ignored by Git. Do not stage them.

## PyPI release checklist

Before uploading a new version:

1. Confirm the version in `pyproject.toml` has not already been published.
2. Run the full test suite and distribution checks above.
3. Confirm the PyPI README describes only implemented v0.1 behaviour.
4. Confirm no credential, customer context, local workspace file, or generated
   evidence export is staged.
5. Build from the committed release candidate and inspect the exact `dist/` artifacts.
6. Publish only through the configured [GitHub Trusted Publishing workflow](pypi-release.md).
7. Verify the project page and install the exact published version in a clean
   environment.

The package is MIT-licensed. See [License](../LICENSE), the [delivery plan](delivery-plan.md),
and the [security and data boundaries](security-and-data-boundaries.md) before
changing release claims or safety boundaries.
