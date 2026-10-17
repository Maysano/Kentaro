"""Strict configuration for read-only Kentaro profiles; no model calls are implemented."""
from pathlib import Path
import tomllib


def load_config(path):
    path = Path(path).resolve()
    with path.open("rb") as stream:
        config = tomllib.load(stream)
    profile = config.get("profile")
    expected = {"schema_version", "profile", "read_only", "scope", "cache", "model"}
    if profile == "demo":
        expected.add("fixture")
    if set(config) != expected:
        raise ValueError("Configuration contains missing or unsupported fields")
    if type(config["schema_version"]) is not int or config["schema_version"] != 1:
        raise ValueError("Unsupported configuration schema")
    if config["read_only"] is not True:
        raise ValueError("Kentaro v0.1 requires read_only = true")
    if profile not in {"demo", "live"}:
        raise ValueError("Profile must be demo or live")
    if not isinstance(config["scope"], str) or not config["scope"].strip():
        raise ValueError("A nonempty portfolio scope is required")
    cache = config["cache"]
    if set(cache) != {"enabled", "ttl_seconds", "classification"}:
        raise ValueError("Unsupported cache fields")
    if cache["enabled"] is not False:
        raise ValueError("Kentaro profiles require cache.enabled = false")
    classifications = {"public-synthetic"} if profile == "demo" else {"confidential"}
    if cache["classification"] not in classifications:
        raise ValueError("Invalid cache classification for profile")
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
    if profile == "demo":
        if not isinstance(config["fixture"], str) or not config["fixture"]:
            raise ValueError("Fixture path is required")
        config["fixture"] = (path.parent / config["fixture"]).resolve()
    return config
