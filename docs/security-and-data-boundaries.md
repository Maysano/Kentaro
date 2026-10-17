# Data boundaries

Kentaro v0.1 reads a synthetic local fixture or the documented Maysano pilot API.
The live adapter uses HTTPS GET only, bearer authentication from the ignored local
workspace file, verified TLS, and no response cache. The request guards reject
mutation methods. Scope filtering applies to records and relationship endpoints,
but local filtering is not an authorisation mechanism: Maysano must enforce live
retrieval permissions.

Kentaro v0.1 has no business-tool execution, approval processing, platform mutation,
or graph-write capability. Its local policy evaluator is pure and deterministic;
`allowed` means structurally in scope, not permission to act.

The optional `kentaro data-product draft`, `kentaro use-case draft`, and `kentaro
objective draft` commands create local ODPS proposals only. Their default Ollama
provider is local. Any other provider is treated as hosted and requires both an
explicit provider configuration and `--allow-hosted-content`, because the selected
source document may leave the machine. These commands never grant Maysano write
authority or permission to perform a business action.

The local evidence feature writes append-oriented, redacted JSON Lines logs. Optional
hash chaining indicates a changed sequence but does not provide immutable storage,
retention enforcement, compliance, or a platform audit trail. Evidence exports must
not contain bearer keys, secrets, passwords, credentials, or sensitive payloads.

Only public synthetic data is used by the demo. Customer retention, encryption,
cache exclusions, and cloud classification policy remain platform-owner decisions
before customer data is introduced. Reports distinguish retrieval time from record
timestamps and do not claim live status beyond their sourced snapshot.

The guided setup keeps the live raw key only in
`.kentaro/workspace/maysano.env` as `API_KEY`, with `API_BASE_URL` alongside it.
The adapter sends the key only as an HTTPS
`Authorization: Bearer` header. These values must never appear in TOML, fixture
data, Git history, reports, logs, or evidence exports.
