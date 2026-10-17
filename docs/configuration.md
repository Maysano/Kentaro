# Configuration

Use TOML with Python's standard-library parser. Run:

```powershell
python -m kentaro --config examples/configs/demo.toml validate-config
python -m kentaro --config examples/configs/demo.toml portfolio brief
```

The version 1 demo configuration requires read_only=true, a nonempty scope, a fixture path
relative to the configuration file, disabled cache, and public-synthetic classification.
Cache TTL must be positive, but no cache exists yet. Model mode accepts local/cloud/hybrid
as policy declarations only: execution must remain disabled. Provider, task-class and no-send
lists are validated string arrays; no SDK or provider requests are made.
Unknown top-level fields are rejected. Credentials have no configuration field.
The demo and live read-only profiles are implemented; configuration validation does
not test platform connectivity.

## Local bearer credential

The synthetic demo does not make HTTP requests and does not read a credential.
The live read-only profile reads the raw bearer token only from the ignored user
workspace, never from TOML or a tracked file:

```powershell
New-Item -ItemType Directory -Force .kentaro/workspace
Copy-Item .env.example .kentaro/workspace/.env
```

Set `API_KEY` in `.kentaro/workspace/.env` to the raw key, without the `Bearer `
prefix. `API_BASE_URL` is pre-filled with the documented pilot URL; replace it
only when Maysano supplies a different environment URL. `.kentaro/` and `.env`
files are ignored by Git, so their values must never be staged, committed,
pushed, printed, or included in reports. The live read adapter sends the key
only in `Authorization: Bearer <API_KEY>` over HTTPS.

The live profile reads these settings only when `--env-file` is explicitly
provided. It uses HTTPS GET requests only, keeps TLS verification enabled, and
does not cache API responses or write to the platform.

## SDK generation configuration

Keep the SDK and Maysano configuration planes separate:

- `examples/configs/*.toml` are tracked Kentaro read-profile examples. Their
  strict schema must not contain SDK provider settings.
- `config/generation.example.yaml` is the small, tracked SDK template.
- `.kentaro/workspace/config/generation.yaml` is the single active, ignored
  generation configuration. It selects one provider and model.
- `.kentaro/workspace/.env` holds only `API_BASE_URL` and `API_KEY` for the
  Maysano read API. Its strict parser rejects unrelated variables.
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
Action-to-model routing is intentionally not configured yet; it will be added
only when Kentaro implements it.
