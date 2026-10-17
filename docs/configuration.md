# Advanced configuration

The default local experience does not use TOML. After installation, `kentaro demo`,
`kentaro portfolio brief`, and `kentaro dashboard` use synthetic context packaged in
the distribution and make no HTTP request.

Use TOML only for advanced team configuration: named environments, custom API
endpoints, custom workspace paths, model declarations, organisation policies, or
other non-default profiles. `--config` is an override, never a requirement for the
normal local workflow.

## Guided read-only Maysano setup

For an explicitly authorised live read, run:

```shell
kentaro configure maysano
kentaro portfolio brief --source maysano
```

The guided command prompts for the approved endpoint, scope, and Maysano-issued API
key. It creates ignored local configuration and credential files in
`.kentaro/workspace/`; it never prints the key. The live adapter makes HTTPS GET
requests only, with TLS verification enabled. It does not cache responses, create
external records, write to Maysano, or mutate the platform.

## Advanced TOML profiles

Use TOML with Python's standard-library parser only where an organisation needs an
explicit non-default profile. For example, a checked-out development copy can validate
a named profile with:

```shell
kentaro --config path/to/profile.toml validate-config
kentaro --config path/to/profile.toml portfolio brief
```

The version 1 demo configuration requires read_only=true, a nonempty scope, a fixture path
relative to the configuration file, disabled cache, and public-synthetic classification.
Cache TTL must be positive, but no cache exists yet. Model mode accepts local/cloud/hybrid
as policy declarations only: execution must remain disabled. Provider, task-class and no-send
lists are validated string arrays; no SDK or provider requests are made.
Unknown top-level fields are rejected. Credentials have no configuration field.
The demo and live read-only profiles are implemented; configuration validation does
not test platform connectivity.

## Credential handling

The synthetic demo does not make HTTP requests and does not read a credential. The
guided setup stores the raw API key only in an ignored local workspace file, never in
TOML or a tracked file. The key is sent only as `Authorization: Bearer <API_KEY>` to
the configured HTTPS read endpoint. Do not stage, commit, print, or include a key in
reports. Advanced external credential files may be supplied with `--env-file` when
using an advanced live profile.

## SDK generation configuration

Keep the SDK and Maysano configuration planes separate:

- `examples/configs/*.toml` are tracked Kentaro read-profile examples. Their
  strict schema must not contain SDK provider settings.
- `config/generation.example.yaml` is the small, tracked SDK template.
- `.kentaro/workspace/config/generation.yaml` is the single active, ignored
  generation configuration. It selects one provider and model.
- `.kentaro/workspace/maysano.env` is created by `kentaro configure maysano` and
  holds only `API_BASE_URL` and `API_KEY` for the Maysano read API. Its strict parser
  rejects unrelated variables.
- `.kentaro/workspace/llm.env` holds an online provider key named by the
  selected provider's `apiKeyEnv`. It is ignored by Git. Make that variable
  available to the SDK process without printing or committing it.

Create the active file once:

```powershell
Copy-Item config/generation.example.yaml .kentaro/workspace/config/generation.yaml
```

To use a local model, replace the one `openai` provider entry in that file with
the commented Ollama example. Local models need no API key. To use an online
model, keep one provider entry and set only the named environment variable.
Then invoke hosted drafting only with an explicit egress acknowledgement:

```shell
kentaro objective draft ./business-context.md \
  --provider openai \
  --config .kentaro/workspace/config/generation.yaml \
  --allow-hosted-content
```

The default draft commands use local Ollama and do not read this configuration. See
[local draft artifacts](data-product-drafts.md) for the complete boundary and
provenance behaviour.
