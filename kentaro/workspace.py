"""Local workspace helpers for the safe, configuration-free Kentaro experience."""
from __future__ import annotations

from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from importlib.resources import files
from pathlib import Path
from sysconfig import get_path
from typing import Any
from urllib.parse import urlsplit


DEFAULT_MAYSANO_BASE_URL = "https://app.maysano.com/api/external/v1"
SKILL_NAMES = (
    "kentaro-ai-product-design",
    "kentaro-create-data-product",
    "kentaro-data-product-design",
    "kentaro-list-data-products",
    "kentaro-list-objectives",
    "kentaro-list-use-cases",
    "kentaro-masterclass",
    "kentaro-objective-design",
    "kentaro-portfolio-analysis",
    "kentaro-portfolio-brief",
    "kentaro-portfolio-dashboard",
    "kentaro-portfolio-readiness",
    "kentaro-use-case-design",
)
MANAGED_INSTRUCTIONS_START = "<!-- kentaro-setup: managed instructions start -->"
MANAGED_INSTRUCTIONS_END = "<!-- kentaro-setup: managed instructions end -->"


def workspace_path(cwd: Path | None = None) -> Path:
    """Create and return the ignored local workspace for the current project."""
    workspace = (cwd or Path.cwd()) / ".kentaro" / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace


def _development_skills_root() -> Path:
    """Return source skills only while running directly from a checkout.

    Installed distributions use the wheel's platform data directory.  This fallback
    keeps source-tree tests usable without making a published installation depend
    on a checkout.
    """
    return Path(__file__).resolve().parents[1] / ".agents" / "skills"


def packaged_skills_root() -> Path:
    """Locate skills installed with Kentaro, without relying on a repository path."""
    source_root = _development_skills_root()
    if source_root.is_dir():
        return source_root
    installed_root = Path(get_path("data")) / "share" / "kentaro" / "skills"
    if installed_root.is_dir():
        return installed_root
    raise FileNotFoundError(
        "Kentaro's packaged skills are unavailable. Reinstall with "
        '`python -m pip install --upgrade "kentaro==0.2.1"`.'
    )


def _managed_instruction_block() -> str:
    template = files("kentaro.resources").joinpath("codex-workspace-AGENTS.md").read_text(encoding="utf-8").strip()
    return f"{MANAGED_INSTRUCTIONS_START}\n{template}\n{MANAGED_INSTRUCTIONS_END}\n"


def _write_managed_instructions(target: Path, *, replace: bool) -> str:
    if target.is_symlink():
        raise ValueError("AGENTS.md is a symbolic link and will not be changed")
    expected = _managed_instruction_block()
    if not target.exists():
        target.write_text(expected, encoding="utf-8")
        return "installed"

    existing = target.read_text(encoding="utf-8")
    start = existing.find(MANAGED_INSTRUCTIONS_START)
    end = existing.find(MANAGED_INSTRUCTIONS_END)
    if start >= 0 and end >= start:
        end += len(MANAGED_INSTRUCTIONS_END)
        managed = existing[start:end]
        if managed == expected.rstrip("\n"):
            return "reused"
        if not replace:
            return "preserved_modified"
        target.write_text(existing[:start] + expected + existing[end:].lstrip("\n"), encoding="utf-8")
        return "replaced_modified"

    # A user-owned AGENTS.md is never replaced implicitly.  Add one bounded block
    # so existing instructions stay authoritative alongside Kentaro's guidance.
    separator = "" if existing.endswith("\n\n") else "\n\n"
    target.write_text(existing + separator + expected, encoding="utf-8")
    return "appended_to_user_instructions"


def _copy_skill_tree(source: Path, destination: Path, *, replace: bool) -> dict[str, int]:
    if source.is_symlink() or destination.is_symlink():
        raise ValueError(f"Refusing to use symbolic links for skill '{source.name}'")
    destination.mkdir(parents=True, exist_ok=True)
    results = {"installed": 0, "reused": 0, "preserved_modified": 0, "replaced_modified": 0}
    for source_file in sorted(path for path in source.rglob("*") if path.is_file()):
        relative = source_file.relative_to(source)
        destination_file = destination / relative
        if destination_file.exists() and destination_file.is_symlink():
            raise ValueError(f"Refusing to replace symbolic link '{destination_file}'")
        expected = source_file.read_bytes()
        if destination_file.exists():
            if destination_file.read_bytes() == expected:
                results["reused"] += 1
            elif replace:
                destination_file.write_bytes(expected)
                results["replaced_modified"] += 1
            else:
                results["preserved_modified"] += 1
        else:
            destination_file.parent.mkdir(parents=True, exist_ok=True)
            destination_file.write_bytes(expected)
            results["installed"] += 1
    return results


def install_codex_workspace(directory: Path | None = None, *, replace: bool = False) -> dict[str, Any]:
    """Safely install the complete Kentaro Codex experience into one workspace."""
    directory = (directory or Path.cwd()).resolve()
    workspace = workspace_path(directory)
    (workspace / "design").mkdir(parents=True, exist_ok=True)
    agents = directory / ".agents"
    skills_directory = agents / "skills"
    if agents.is_symlink() or skills_directory.is_symlink():
        raise ValueError(".agents or .agents/skills is a symbolic link and will not be changed")
    instructions = directory / "AGENTS.md"
    instruction_status = _write_managed_instructions(instructions, replace=replace)
    source_root = packaged_skills_root()
    skill_results: dict[str, dict[str, int]] = {}
    for skill in SKILL_NAMES:
        source = source_root / skill
        if not (source / "SKILL.md").is_file():
            raise FileNotFoundError(f"Kentaro package is missing required skill '{skill}'")
        skill_results[skill] = _copy_skill_tree(source, skills_directory / skill, replace=replace)
    return {
        "codex_instructions": str(instructions),
        "skills_directory": str(skills_directory),
        "instruction_status": instruction_status,
        "skills": skill_results,
        "design_directory": str(workspace / "design"),
        "replaced": replace,
    }


def write_codex_workspace_instructions(directory: Path | None = None, *, replace: bool = False) -> Path:
    """Compatibility helper that installs Codex instructions and skills."""
    return Path(install_codex_workspace(directory, replace=replace)["codex_instructions"])


def codex_workspace_doctor(directory: Path | None = None) -> dict[str, Any]:
    """Report whether this workspace has the self-contained learner setup."""
    directory = (directory or Path.cwd()).resolve()
    checks: list[dict[str, Any]] = []

    try:
        installed_version = version("kentaro")
        checks.append({"name": "kentaro_version", "status": "ok", "detail": installed_version})
    except PackageNotFoundError:
        checks.append({"name": "kentaro_version", "status": "failed", "detail": "Kentaro is not installed", "fix": 'Run `python -m pip install "kentaro==0.2.1"`.'})

    workspace = directory / ".kentaro" / "workspace"
    checks.append({
        "name": "local_workspace",
        "status": "ok" if workspace.is_dir() else "failed",
        "detail": str(workspace),
        **({} if workspace.is_dir() else {"fix": "Run `kentaro setup codex` from this workspace."}),
    })

    instructions = directory / "AGENTS.md"
    instructions_ready = instructions.is_file() and MANAGED_INSTRUCTIONS_START in instructions.read_text(encoding="utf-8")
    checks.append({
        "name": "codex_instructions",
        "status": "ok" if instructions_ready else "failed",
        "detail": str(instructions),
        **({} if instructions_ready else {"fix": "Run `kentaro setup codex` from this workspace."}),
    })

    skills_directory = directory / ".agents" / "skills"
    missing_skills = [skill for skill in SKILL_NAMES if not (skills_directory / skill / "SKILL.md").is_file()]
    checks.append({
        "name": "kentaro_skills",
        "status": "ok" if not missing_skills else "failed",
        "detail": f"{len(SKILL_NAMES) - len(missing_skills)}/{len(SKILL_NAMES)} installed",
        "missing": missing_skills,
        **({} if not missing_skills else {"fix": "Run `kentaro setup codex` from this workspace."}),
    })

    portfolios = [path for path in (workspace / "design").glob("*.json") if path.name != "engagement-state.json"] if workspace.is_dir() else []
    if not portfolios:
        checks.append({
            "name": "design_portfolio",
            "status": "not_started",
            "detail": "No DesignPortfolio has been created yet; this is normal for a new workspace.",
            "fix": "Open this folder in Codex and describe the business problem to start a design.",
        })
    else:
        from kentaro.design.portfolio import load_portfolio, validate_portfolio

        invalid = [str(path) for path in portfolios if not validate_portfolio(load_portfolio(path))["valid"]]
        checks.append({
            "name": "design_portfolio",
            "status": "ok" if not invalid else "failed",
            "detail": f"{len(portfolios) - len(invalid)}/{len(portfolios)} saved DesignPortfolio files validate",
            "invalid": invalid,
            **({} if not invalid else {"fix": "Ask Codex to inspect and repair the listed local DesignPortfolio."}),
        })

    try:
        from kentaro.design.portfolio import create_design_portfolio
        from kentaro.design.render import render_canvas

        canvas = render_canvas(create_design_portfolio("Kentaro doctor", "kentaro-doctor"))
        checks.append({
            "name": "visual_canvas",
            "status": "ok" if "<html" in canvas.lower() else "failed",
            "detail": "Kentaro can render the local read-only DesignPortfolio canvas.",
            **({} if "<html" in canvas.lower() else {"fix": 'Run `python -m pip install --upgrade "kentaro==0.2.1"`.'}),
        })
    except (ImportError, ValueError) as error:
        checks.append({"name": "visual_canvas", "status": "failed", "detail": str(error), "fix": 'Run `python -m pip install --upgrade "kentaro==0.2.1"`.'})

    try:
        from kentaro.design.reports import validate_odps
        from kentaro.scenarios.udemy_masterclass import odps_fixture

        result = validate_odps(odps_fixture())
        odps_ready = bool(result.get("valid"))
        checks.append({
            "name": "odps_validation",
            "status": "ok" if odps_ready else "failed",
            "detail": result if odps_ready else result.get("errors", result),
            **({} if odps_ready else {"fix": 'Run `python -m pip install --upgrade "kentaro==0.2.1"`.'}),
        })
    except (ImportError, ValueError) as error:
        checks.append({"name": "odps_validation", "status": "failed", "detail": str(error), "fix": 'Run `python -m pip install --upgrade "kentaro==0.2.1"`.'})

    failed = [check for check in checks if check["status"] == "failed"]
    return {"valid": not failed, "workspace": str(directory), "checks": checks, "fixes": [check["fix"] for check in failed if "fix" in check]}


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
