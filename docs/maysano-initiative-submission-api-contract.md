# Maysano Initiative Submission API contract

**Status:** Proposed contract for Maysano maintainer review. It defines an
initiative-package intake boundary only. It is not an approval, graph-mutation,
or implementation-authorisation contract.

## Purpose

Kentaro submits a self-contained, proposed business initiative package to
Maysano. The package may describe business objectives, use cases, data
products, AI products, and their proposed relationships.

Maysano decides whether to inspect, enrich, deduplicate, reject, route, approve,
or turn the proposal into governed company-graph work. Kentaro does not retrieve
the current company graph, calculate graph operations, or claim that Maysano
has accepted or persisted any object.

The submission ZIP is a `KentaroInitiativePackage`. Its internal manifest and
standard-family artefacts are the authoritative description of the initiative.
The request metadata is a small transport envelope for identity, correlation,
and integrity verification. It must not become a competing business definition.

## Boundary and non-goals

This endpoint does **not**:

- create, update, retire, or otherwise mutate a company-graph object;
- accept a current graph fragment, graph revision, graph diff, or graph action;
- accept authority, approval, tenant, workspace permission, or receipt facts
  asserted by Kentaro;
- treat a local Kentaro review confirmation as a Maysano approval; or
- require Maysano to adopt ODPH for the initial intake request.

If Maysano later creates governed graph work, it owns the authority, graph
context, change contract, validation, persistence, and audit process.

## Endpoint

```http
POST /api/external/v1/initiative-submissions
Content-Type: multipart/form-data
Idempotency-Key: <client-generated opaque key>
Authorization: <Maysano-defined authenticated caller>
```

The endpoint accepts exactly two required multipart parts:

| Part | Media type | Meaning |
| --- | --- | --- |
| `metadata` | `application/json` | The request envelope defined below. |
| `package` | `application/zip` | One complete `KentaroInitiativePackage` ZIP. |

`Idempotency-Key` is required. Maysano defines its accepted character set,
retention period, and response behaviour for a repeated key. A repeated key
with different submitted bytes or package digest must be rejected.

The caller's authenticated identity determines its tenant and accessible
workspaces. Maysano must derive these values from authentication and
authorisation rather than accept them as fields supplied by Kentaro.

## Request metadata

```json
{
  "schema": "https://maysano.com/api/external/v1/schema/initiative-submission.json",
  "version": "1.0",
  "initiative": {
    "id": "customer-risk-assessment-improvement",
    "title": "Customer Risk Assessment Improvement",
    "status": "proposed"
  },
  "package": {
    "profile": "KentaroInitiativePackage",
    "profile_version": "1.0",
    "filename": "customer-risk-assessment.zip",
    "sha256": "7c6a4bb25db5e93c2a3dc5b0ec8e92ecb8d9dd4ca74d5ae189640fab9b08c0d2"
  },
  "source": {
    "system": "kentaro",
    "system_version": "0.2.9",
    "portfolio_id": "customer-risk-assessment-improvement",
    "portfolio_revision": "draft-v1",
    "portfolio_hash": "40a9acbdd6350ed2bea7b7bc594a8e0a536f1135ecec7ec1d887edbc8d45a2d6"
  }
}
```

### JSON Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://maysano.com/api/external/v1/schema/initiative-submission.json",
  "title": "Maysano initiative submission",
  "type": "object",
  "additionalProperties": false,
  "required": ["schema", "version", "initiative", "package", "source"],
  "properties": {
    "schema": {
      "const": "https://maysano.com/api/external/v1/schema/initiative-submission.json"
    },
    "version": { "const": "1.0" },
    "initiative": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "title", "status"],
      "properties": {
        "id": {
          "type": "string",
          "pattern": "^[a-z0-9][a-z0-9-]{2,127}$"
        },
        "title": { "type": "string", "minLength": 1, "maxLength": 256 },
        "status": { "const": "proposed" }
      }
    },
    "package": {
      "type": "object",
      "additionalProperties": false,
      "required": ["profile", "profile_version", "filename", "sha256"],
      "properties": {
        "profile": { "const": "KentaroInitiativePackage" },
        "profile_version": { "const": "1.0" },
        "filename": {
          "type": "string",
          "pattern": "^[^/\\\\]+\\.zip$"
        },
        "sha256": { "type": "string", "pattern": "^[a-f0-9]{64}$" }
      }
    },
    "source": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "system",
        "system_version",
        "portfolio_id",
        "portfolio_revision",
        "portfolio_hash"
      ],
      "properties": {
        "system": { "const": "kentaro" },
        "system_version": { "type": "string", "minLength": 1 },
        "portfolio_id": { "type": "string", "minLength": 1 },
        "portfolio_revision": { "type": "string", "minLength": 1 },
        "portfolio_hash": { "type": "string", "pattern": "^[a-f0-9]{64}$" }
      }
    }
  }
}
```

## Package consistency rules

Before recording a submission, Maysano must:

1. Authenticate and authorise the caller for the receiving tenant and
   workspace.
2. Enforce Maysano-owned size, compression, archive-entry-count, and safe-path
   limits before extracting the ZIP.
3. Calculate the SHA-256 digest of the uploaded ZIP and compare it with
   `metadata.package.sha256`.
4. Read and validate the package manifest and profile version.
5. Require these request-to-package values to match exactly:
   `initiative.id`, `package.profile`, `package.profile_version`,
   `source.portfolio_id`, `source.portfolio_revision`, and
   `source.portfolio_hash`.
6. Verify every internal manifest digest before treating any artefact as
   available for Maysano evaluation.
7. Reject path traversal, duplicate archive entries, unsupported profiles,
   malformed standard artefacts, and unreadable or missing required files.

Maysano must record the received bytes, calculated digest, authenticated actor,
tenant/workspace context, and receipt time in its own audit trail. A Kentaro
manifest is supplementary provenance, not the authoritative Maysano audit
record.

## Accepted response

The endpoint returns `202 Accepted` only when the request and package pass
transport, integrity, profile, and caller-authorisation checks. `202 Accepted`
means **received for Maysano evaluation**. It does not mean that Maysano has
approved the initiative or created company-graph records.

```http
HTTP/1.1 202 Accepted
Content-Type: application/json
Location: /api/external/v1/initiative-submissions/msub_01j...
```

```json
{
  "submission_id": "msub_01j...",
  "status": "received",
  "received_at": "2026-11-01T12:00:00Z",
  "package_sha256": "7c6a4bb25db5e93c2a3dc5b0ec8e92ecb8d9dd4ca74d5ae189640fab9b08c0d2",
  "status_url": "/api/external/v1/initiative-submissions/msub_01j..."
}
```

`submission_id`, `received_at`, and the submission state are assigned by
Maysano. Kentaro must not generate or infer them.

## Initial rejection responses

| Status | When to use it |
| --- | --- |
| `400 Bad Request` | Multipart structure, JSON, schema, required part, or ZIP format is invalid. |
| `401 Unauthorized` | The caller is not authenticated. |
| `403 Forbidden` | The caller is authenticated but cannot submit to the derived tenant/workspace context. |
| `409 Conflict` | The idempotency key has already been used with different submitted bytes or metadata. |
| `413 Content Too Large` | Maysano-owned package or extraction limits are exceeded. |
| `415 Unsupported Media Type` | Required part media types or ZIP profile are unsupported. |
| `422 Unprocessable Content` | Package hash, internal manifest hash, metadata consistency, or package-profile validation fails. |
| `429 Too Many Requests` | Maysano rate limiting applies. |

Errors must contain a safe machine-readable code and correlation ID. They must
not disclose credentials, inaccessible company-graph content, or tenant data.

## Status resource

```http
GET /api/external/v1/initiative-submissions/{submission_id}
```

The resource must at least distinguish `received`, `evaluating`, and a terminal
Maysano-defined disposition. It must not claim a graph mutation unless a
separate Maysano workflow and receipt prove one.

When Maysano materialises any submitted initiative content in its company graph,
the terminal result must expose the Maysano mutation receipt, canonical object
references, and resulting graph revision. Kentaro uses those identifiers to
re-read the authorised projection and verify the result. Name matching is not
sufficient confirmation because another initiative can use a similar title or
object name.

## Maysano decisions after intake

After accepting a package, Maysano may:

- request enrichment or clarification;
- identify duplication, overlap, or conflict with company context;
- reject the proposed initiative;
- create a Maysano-owned review or approval workflow; or
- create separately governed company-graph work, using Maysano-selected context
  and contracts.

Those decisions are intentionally outside this upload contract.

## Kentaro implementation dependencies

Kentaro can implement this contract after the following are ratified by the
Maysano maintainer:

1. The exact external base URL and authentication scheme.
2. Tenant/workspace routing semantics, if a submission target must be selected.
3. Idempotency-key format, retention, and retry behaviour.
4. Upload, decompression, archive-entry, and timeout limits.
5. `KentaroInitiativePackage` v1 file layout and internal manifest schema.
6. The status-resource retention, access, and terminal-state model.

Until then, this document is a proposed boundary and must not be represented as
an implemented Maysano API.
