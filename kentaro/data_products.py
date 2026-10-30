"""Local-only ODPS draft generation and validation through Kentaro's pinned SDK."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urlsplit

from kentaro.workspace import timestamped_output


LOCAL_PROVIDERS = {"ollama"}
DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
DRAFT_TYPES = {
    "data-product": {"sdk_kind": "odps-product", "workspace_directory": "products", "label": "data-product"},
    "use-case": {"sdk_kind": "use-case", "workspace_directory": "use-cases", "label": "use-case"},
    "objective": {"sdk_kind": "objective", "workspace_directory": "objectives", "label": "objective"},
}


def _slug(value: str) -> str:
    """Return a predictable local-directory name without trusting source metadata."""
    candidate = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return candidate or "data-product"


def _require_sdk() -> None:
    if importlib.util.find_spec("open_data_products") is None:
        raise ValueError('Local drafting and validation require the standard Kentaro dependency. Install with `python -m pip install --upgrade "kentaro==0.2.2"`.')


def _source_file(source: str | Path) -> Path:
    resolved = Path(source).expanduser().resolve()
    if not resolved.is_file():
        raise ValueError("Draft source must be an existing Markdown or text file")
    if resolved.suffix.lower() not in {".md", ".markdown", ".txt"}:
        raise ValueError("Local drafting currently accepts Markdown or text sources only")
    return resolved


def _draft_directory(workspace: Path, source: Path, artifact_type: str) -> Path:
    root = workspace / DRAFT_TYPES[artifact_type]["workspace_directory"] / _slug(source.stem)
    root.mkdir(parents=True, exist_ok=True)
    while True:
        candidate = timestamped_output(root, "draft", "")
        try:
            candidate.mkdir()
        except FileExistsError:
            continue
        return candidate


def _provider_mode(provider: str) -> str:
    return "local" if provider.lower() in LOCAL_PROVIDERS else "hosted"


def _local_ollama_url(value: str | None) -> str:
    url = value or DEFAULT_OLLAMA_URL
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("The Ollama URL must be a local loopback endpoint. Use a hosted provider with --allow-hosted-content for remote generation.")
    return url


def _activity_log(workspace: Path) -> Path:
    directory = workspace / "sdk"
    directory.mkdir(parents=True, exist_ok=True)
    return directory / "activity.log"


def _run(command: list[str], *, environment: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=environment, check=False)


def create_local_draft(
    artifact_type: str,
    source: str | Path,
    workspace: Path,
    *,
    provider: str = "ollama",
    model: str | None = None,
    config: str | None = None,
    ollama_url: str | None = None,
    profile: str = "minimal",
    allow_hosted_content: bool = False,
) -> dict:
    """Generate and validate a proposed local artifact without touching Maysano.

    A non-local provider is an explicit content-egress choice. This function never
    receives provider credentials and records no source text in Kentaro's evidence.
    """
    if artifact_type not in DRAFT_TYPES:
        raise ValueError("Draft type must be data-product, use-case, or objective")
    _require_sdk()
    source_path = _source_file(source)
    if artifact_type != "data-product" and profile != "minimal":
        raise ValueError("Only data-product drafts support a complete-draft profile")
    if profile not in {"minimal", "complete-draft"}:
        raise ValueError("Data-product draft profile must be minimal or complete-draft")
    mode = _provider_mode(provider)
    if mode == "hosted" and not allow_hosted_content:
        raise ValueError("Hosted generation can send source content outside this machine. Re-run with --allow-hosted-content after review.")
    if mode == "hosted" and not config:
        raise ValueError("Hosted generation requires an explicit provider configuration file")
    if mode == "hosted" and ollama_url:
        raise ValueError("--ollama-url is only valid with the local Ollama provider")
    local_ollama_url = _local_ollama_url(ollama_url) if mode == "local" else None

    output = _draft_directory(workspace, source_path, artifact_type)
    activity_log = _activity_log(workspace)
    command = [
        sys.executable,
        "-m",
        "open_data_products.cli",
        "generate",
        str(source_path),
        "--kind",
        DRAFT_TYPES[artifact_type]["sdk_kind"],
        "--output",
        str(output),
        "--provider",
        provider,
        "--json",
    ]
    if artifact_type == "data-product":
        command.extend(("--profile", profile))
    if config:
        command.extend(("--config", str(Path(config).expanduser().resolve())))
    if model:
        command.extend(("--model", model))
    if local_ollama_url:
        command.extend(("--ollama-url", local_ollama_url))

    environment = dict(os.environ, OPEN_DATA_PRODUCTS_ACTIVITY_LOG_PATH=str(activity_log))
    generated = _run(command, environment=environment)
    if generated.returncode != 0:
        raise ValueError(f"{DRAFT_TYPES[artifact_type]['label'].title()} draft generation failed. Review the configured provider and local SDK activity log.")

    artifacts = sorted((*output.rglob("*.yaml"), *output.rglob("*.yml")))
    if not artifacts:
        raise ValueError(f"{DRAFT_TYPES[artifact_type]['label'].title()} generation completed without producing a YAML draft")
    validations = _validate_artifacts(artifacts, environment)
    if not all(validation["valid"] for validation in validations):
        raise ValueError(f"{DRAFT_TYPES[artifact_type]['label'].title()} draft validation failed. Review the generated draft and validation result.")

    record = {
        "schema_version": 1,
        "kind": f"local_{artifact_type.replace('-', '_')}_draft",
        "artifact_type": artifact_type,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "path": str(source_path),
            "sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        },
        "generation": {
            "provider": provider,
            "provider_mode": mode,
            "content_egress": mode == "hosted",
            "profile": profile,
            "model": model or "not supplied",
            "config_reference": str(Path(config).expanduser().resolve()) if config else "not supplied",
        },
        "output": {
            "directory": str(output),
            "artifacts": validations,
        },
        "limitations": [
            "Local draft only; no Maysano record was created or updated.",
            "Schema validity does not establish ownership, approval, data availability, legal clearance, or production readiness.",
        ],
    }
    _append_generation_record(workspace, record)
    return record


def create_data_product_draft(source: str | Path, workspace: Path, **kwargs) -> dict:
    """Backward-compatible convenience wrapper for the first local draft type."""
    return create_local_draft("data-product", source, workspace, **kwargs)


def validate_local_artifact(artifact: str | Path, workspace: Path, *, artifact_type: str) -> dict:
    """Validate a local ODPS artifact without generating or mutating anything."""
    if artifact_type not in DRAFT_TYPES:
        raise ValueError("Artifact type must be data-product, use-case, or objective")
    _require_sdk()
    path = Path(artifact).expanduser().resolve()
    if not path.is_file() or path.suffix.lower() not in {".yaml", ".yml"}:
        raise ValueError("Artifact validation requires an existing YAML file")
    validations = _validate_artifacts([path], dict(os.environ, OPEN_DATA_PRODUCTS_ACTIVITY_LOG_PATH=str(_activity_log(workspace))))
    result = {
        "schema_version": 1,
        "kind": f"local_{artifact_type.replace('-', '_')}_validation",
        "artifact_type": artifact_type,
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "artifact": validations[0],
        "limitations": [
            "Local validation only; no Maysano record was created or updated.",
            "Schema validity does not establish ownership, approval, data availability, legal clearance, or production readiness.",
        ],
    }
    _append_generation_record(workspace, result)
    return result


def _validate_artifacts(artifacts: list[Path], environment: dict[str, str]) -> list[dict]:
    validations = []
    for artifact in artifacts:
        validation = _run(
            [sys.executable, "-m", "open_data_products.cli", "validate", str(artifact), "--json"],
            environment=environment,
        )
        validations.append({"path": str(artifact), "valid": validation.returncode == 0})
    return validations


def _append_generation_record(workspace: Path, record: dict) -> None:
    artifact_type = record.get("artifact_type", "data-product")
    path = workspace / "evidence" / f"{artifact_type}-drafts.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, sort_keys=True) + "\n")
