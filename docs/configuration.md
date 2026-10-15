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
Only the demo profile is implemented; validation does not test platform connectivity.
