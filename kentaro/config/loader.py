"""Strict configuration for the controlled demo; no model calls are implemented."""
from pathlib import Path
import tomllib


def load_config(path):
    path = Path(path).resolve()
    with path.open("rb") as stream:
        config = tomllib.load(stream)
    expected = {"schema_version", "profile", "read_only", "scope", "fixture", "cache", "model"}
    if set(config) != expected:
        raise ValueError("Configuration contains missing or unsupported fields")
    if type(config["schema_version"]) is not int or config["schema_version"] != 1:
        raise ValueError("Unsupported configuration schema")
    if config["read_only"] is not True:
        raise ValueError("Kentaro v0.1 requires read_only = true")
    if config["profile"] != "demo":
        raise ValueError("Only the controlled demo profile is implemented")
    if not isinstance(config["scope"], str) or not config["scope"].strip():
        raise ValueError("A nonempty portfolio scope is required")
    cache = config["cache"]
    if set(cache) != {"enabled", "ttl_seconds", "classification"}:
        raise ValueError("Unsupported cache fields")
    if cache["enabled"] is not False or cache["classification"] != "public-synthetic":
        raise ValueError("Demo supports uncached public-synthetic data only")
    if type(cache["ttl_seconds"]) is not int or cache["ttl_seconds"] <= 0:
        raise ValueError("Cache TTL must be a positive integer")
    model = config["model"]
    if set(model) != {"mode", "enabled", "permitted_providers", "cloud_task_classes", "no_send_classifications"}:
        raise ValueError("Unsupported model policy fields")
    if model["mode"] not in {"local", "cloud", "hybrid"}:
        raise ValueError("Invalid model mode")
    if model["enabled"] is not False:
        raise ValueError("SDK model execution is not implemented")
    for key in ("permitted_providers", "cloud_task_classes", "no_send_classifications"):
        if not isinstance(model[key], list) or any(not isinstance(v, str) for v in model[key]):
            raise ValueError("Model policy lists must contain strings")
    if not isinstance(config["fixture"], str) or not config["fixture"]:
        raise ValueError("Fixture path is required")
    config["fixture"] = (path.parent / config["fixture"]).resolve()
    return config
