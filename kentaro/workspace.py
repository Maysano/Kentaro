"""Local workspace helpers for the safe, configuration-free Kentaro experience."""
from __future__ import annotations

from datetime import datetime, timezone
from importlib.resources import files
from pathlib import Path
from urllib.parse import urlsplit


DEFAULT_MAYSANO_BASE_URL = "https://app.maysano.com/api/external/v1"


def workspace_path(cwd: Path | None = None) -> Path:
    """Create and return the ignored local workspace for the current project."""
    workspace = (cwd or Path.cwd()) / ".kentaro" / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace


def write_codex_workspace_instructions(directory: Path | None = None, *, replace: bool = False) -> Path:
    """Create a non-overwriting Codex instruction file in a learner workspace."""
    target = (directory or Path.cwd()).resolve() / "AGENTS.md"
    if target.is_symlink():
        raise ValueError("AGENTS.md is a symbolic link and will not be replaced")
    if target.exists() and not replace:
        raise ValueError("AGENTS.md already exists; re-run `kentaro setup codex --replace` only if you intend to replace it")
    template = files("kentaro.resources").joinpath("codex-workspace-AGENTS.md").read_text(encoding="utf-8")
    target.write_text(template, encoding="utf-8")
    return target


def timestamped_output(workspace: Path, stem: str, suffix: str) -> Path:
    """Return a unique local output path without ever selecting an existing file."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    candidate = workspace / f"{stem}-{timestamp}{suffix}"
    counter = 1
    while candidate.exists():
        candidate = workspace / f"{stem}-{timestamp}-{counter}{suffix}"
        counter += 1
    return candidate


def maysano_config_path(workspace: Path) -> Path:
    return workspace / "maysano.toml"


def maysano_environment_path(workspace: Path) -> Path:
    return workspace / "maysano.env"


def _validate_maysano_setup(*, api_base_url: str, api_key: str, scope: str) -> None:
    """Reject values that cannot be safely stored in local strict config files."""
    if not isinstance(api_key, str) or not api_key.strip() or "\n" in api_key or "\r" in api_key:
        raise ValueError("Maysano API key is required and must be a single line")
    if not isinstance(scope, str) or not scope.strip() or any(character in scope for character in ('\n', '\r', '"')):
        raise ValueError("Portfolio scope contains unsupported characters")
    if not isinstance(api_base_url, str) or "\n" in api_base_url or "\r" in api_base_url:
        raise ValueError("Maysano API base URL must be an HTTPS URL")
    parsed = urlsplit(api_base_url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("Maysano API base URL must be an HTTPS URL without credentials, query, or fragment")


def write_maysano_setup(workspace: Path, *, api_base_url: str, api_key: str, scope: str, replace: bool = False) -> tuple[Path, Path]:
    """Write ignored local setup files without ever displaying the credential."""
    _validate_maysano_setup(api_base_url=api_base_url, api_key=api_key, scope=scope)
    config = maysano_config_path(workspace)
    environment = maysano_environment_path(workspace)
    if not replace and (config.exists() or environment.exists()):
        raise ValueError("Maysano setup already exists. Re-run `kentaro configure maysano --replace` to replace it.")
    config.write_text(
        "\n".join((
            "schema_version = 1",
            'profile = "live"',
            "read_only = true",
            f'scope = "{scope}"',
            "",
            "[cache]",
            "enabled = false",
            "ttl_seconds = 300",
            'classification = "confidential"',
            "",
            "[model]",
            'mode = "local"',
            "enabled = false",
            "permitted_providers = []",
            "cloud_task_classes = []",
            'no_send_classifications = ["confidential", "restricted"]',
            "",
        )),
        encoding="utf-8",
    )
    environment.write_text(f"API_BASE_URL={api_base_url}\nAPI_KEY={api_key}\n", encoding="utf-8")
    environment.chmod(0o600)
    return config, environment
