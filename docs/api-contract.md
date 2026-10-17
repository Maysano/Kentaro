# Read API capability matrix

Status: the external pilot API contract below was extracted from the Maysano
Platform API Client Integration Guide v1. Kentaro implements the documented
read-only pilot transport; the synthetic local fixture remains available for
explicit demo requests.

| Capability | Demo implementation | Documented pilot API |
| --- | --- | --- |
| Base URL and authentication | Fixed local fixture; no token | `https://app.maysano.com/api/external/v1`; HTTPS `Authorization: Bearer <API_KEY>` |
| Allowed methods / response format | Local reads only | GET only / JSON |
| Products / objectives / use cases | 3 / 1 / 2 synthetic records | `/products`, `/business-objectives`, `/business-use-cases`; permission-scoped |
| Governance metadata | One synthetic record each | Six `/governance/*` resources, covered by `governance:read` |
| List pagination | Not implemented | `limit` 1-100 and `offset` 0-100000 only; response includes `data` and `pagination` |
| Detail and relationships | Fixture relationships | `GET /resource/{id}`; detail links are IDs only and may be truncated at 100 |
| Customer-data handling | Public synthetic only | Returned organization metadata may include draft/private records; treat as confidential |
| Writes and approval actions | Rejected | Not supported by this GET-only API |

## Integration constraints

The key is organization-scoped and permissions are independent: `products:read`,
`objectives:read`, and `use-cases:read` do not imply one another; `governance:read`
covers the documented governance resources. List requests support no search,
filter, sort, organization, or date parameters. Omitted relationship collections
can indicate a missing target permission rather than no relationship.

The API returns `Cache-Control: no-store`. It permits 60 authenticated attempts
per fixed one-minute window; failures count. On HTTP 429, honor `Retry-After`.
Use bounded, jittered retries only for transient network failures or HTTP 503;
do not automatically retry 400, 401, 403, 404, or 405. Do not log the key or
sensitive response bodies.

Before implementation, confirm the supplied key's environment, organization,
permissions, and expiry; then use permitted list and detail requests in a test
environment. Live reads must preserve the response provenance and report where
permissions or truncated links make relationship coverage unknown.
