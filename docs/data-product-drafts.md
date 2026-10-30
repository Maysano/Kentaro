# Local draft artifacts

Kentaro can create and validate proposed data-product, use-case, and objective
artifacts from a Markdown or text source. They align with the [Open Data Products
(ODPS) family of specifications](https://opendataproducts.org/). This local drafting
workflow does not create a Maysano record, update a portfolio,
request approval, or establish ownership, legal clearance, data availability, or
production readiness.

## Standard installation

The standard `kentaro==0.2.6` installation includes the pinned ODPS SDK required for
local draft generation and validation. No optional installation variant is needed.

## Generate a local draft

```shell
kentaro data-product draft ./business-context.md
kentaro use-case draft ./business-context.md
kentaro objective draft ./business-context.md
```

The default provider is local Ollama. Kentaro writes unique output directories under
`.kentaro/workspace/products/`, `.kentaro/workspace/use-cases/`, or
`.kentaro/workspace/objectives/`, validates every generated YAML artifact, and prints
a compact JSON summary. It never overwrites an existing draft.

Validate an existing local artifact without generating anything:

```shell
kentaro data-product validate ./draft.yaml
kentaro use-case validate ./draft.yaml
kentaro objective validate ./draft.yaml
```

The generated artifact and its schema validity are not business proof. Treat generated
SLA, quality, pricing, access, ownership, lifecycle, or implementation fields as
proposals unless directly supported by the source.

## Hosted provider acknowledgement

Any provider other than Ollama is treated as hosted. Hosted generation requires both a
provider configuration and an acknowledgement that selected source content may leave
the machine:

```shell
kentaro data-product draft ./business-context.md \
  --provider openai \
  --config .kentaro/workspace/config/generation.yaml \
  --allow-hosted-content
```

Kentaro does not print provider credentials. Store them only in your approved local
secret mechanism. Do not put them in a command, report, evidence record, or tracked
configuration file.

## Provenance and local evidence

For each successful draft or validation, Kentaro appends a local record to the matching
`.kentaro/workspace/evidence/<artifact-type>-drafts.jsonl` file. It records the source
path and SHA-256 digest for a draft, generation provider and egress mode, selected
profile, output references, validation status, timestamp, and limitations. It does not
store source content or credentials.

These are append-oriented local provenance records. They are not immutable audit
evidence, approval records, or authoritative post-execution evidence.

## Profiles and boundaries

`--profile minimal` is the default evidence-led data-product draft.
`--profile complete-draft` may propose data-product operational fields; it remains a
proposal and requires business review. Use-case and objective drafts accept only the
minimal profile.

The workflow accepts Markdown and plain-text sources only. Preserve an original PDF,
DOCX, or other binary source as the source of record, extract it through an appropriate
document workflow, and pass the resulting text explicitly. Kentaro does not silently
extract, alter, or replace source material.
