"""Kentaro's product-facing CLI; default commands are local and synthetic."""
from __future__ import annotations

import argparse
import getpass
import json
import sys
from pathlib import Path

from kentaro.api.demo import DemoClient, read_packaged_demo
from kentaro.api.live import LiveClient, load_live_environment
from kentaro.config.loader import load_config
from kentaro.data_products import create_local_draft, validate_local_artifact
from kentaro.dashboard.render import render_dashboard
from kentaro.governance import (
    append_evidence_event,
    build_evidence_event,
    evaluate_execution_request,
    load_bundle,
    validate_bundle,
    verify_evidence_log,
)
from kentaro.reports.brief import render_brief
from kentaro.workspace import (
    DEFAULT_MAYSANO_BASE_URL,
    maysano_config_path,
    maysano_environment_path,
    timestamped_output,
    workspace_path,
    write_maysano_setup,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Kentaro read-only Agentic Maysano Harness")
    parser.add_argument("--config", help="Advanced TOML profile override; ordinary local commands use the packaged demo")
    parser.add_argument("--env-file", help="Advanced live-source credential file used with --config")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("demo", help="Run the packaged synthetic demonstration with no network access")
    commands.add_parser("validate-config", help="Validate the default local profile or an advanced --config profile")

    dashboard = commands.add_parser("dashboard", help="Write a sourced portfolio dashboard")
    dashboard.add_argument("--source", choices=("demo", "maysano"), help="Use the packaged demo or configured read-only Maysano source")
    dashboard.add_argument("--output", help="Advanced explicit output path; otherwise a safe timestamped local path is used")
    dashboard.add_argument("--inline", action="store_true", help="Render a conversation HTML fragment")

    portfolio = commands.add_parser("portfolio", help="Retrieve a sourced portfolio view")
    portfolio_commands = portfolio.add_subparsers(dest="workflow", required=True)
    brief = portfolio_commands.add_parser("brief", help="Render a sourced portfolio briefing")
    brief.add_argument("--source", choices=("demo", "maysano"), help="Use the packaged demo or configured read-only Maysano source")

    configure = commands.add_parser("configure", help="Set up an explicit local source")
    configure_commands = configure.add_subparsers(dest="configure_command", required=True)
    maysano = configure_commands.add_parser("maysano", help="Interactively configure the read-only Maysano source")
    maysano.add_argument("--api-base-url", help="Advanced API endpoint override")
    maysano.add_argument("--scope", help="Advanced portfolio scope override")
    maysano.add_argument("--replace", action="store_true", help="Explicitly replace existing local Maysano setup")

    for artifact_type, command_name, plural_name in (
        ("data-product", "data-product", "data-product"),
        ("use-case", "use-case", "use-case"),
        ("objective", "objective", "objective"),
    ):
        artifact = commands.add_parser(command_name, help=f"Create or validate an optional local {plural_name} draft")
        artifact.set_defaults(artifact_type=artifact_type)
        artifact_commands = artifact.add_subparsers(dest="artifact_command", required=True)
        draft = artifact_commands.add_parser("draft", help=f"Generate a proposed {plural_name} draft from Markdown or text")
        draft.add_argument("source", help="Markdown or text business-context source")
        draft.add_argument("--provider", default="ollama", help="ODPS provider; ollama is local, other providers require acknowledgement")
        draft.add_argument("--model", help="Optional provider model override")
        draft.add_argument("--config", dest="generation_config", help="Provider generation configuration required for hosted generation")
        draft.add_argument("--ollama-url", help="Optional local Ollama base URL")
        if artifact_type == "data-product":
            draft.add_argument("--profile", choices=("minimal", "complete-draft"), default="minimal", help="minimal is evidence-only; complete-draft proposes operational fields")
        draft.add_argument("--allow-hosted-content", action="store_true", help="Acknowledge that hosted generation may send source content to the configured provider")
        validate = artifact_commands.add_parser("validate", help=f"Validate one local {plural_name} YAML artifact")
        validate.add_argument("artifact", help="Local YAML artifact to validate")

    objects = commands.add_parser("object", help="Validate advanced local governance-object bundles")
    object_commands = objects.add_subparsers(dest="object_command", required=True)
    object_validate = object_commands.add_parser("validate")
    object_validate.add_argument("--input", required=True, help="Local versioned-object JSON bundle")

    policy = commands.add_parser("policy", help="Evaluate an advanced local proposed request")
    policy_commands = policy.add_subparsers(dest="policy_command", required=True)
    policy_evaluate = policy_commands.add_parser("evaluate")
    policy_evaluate.add_argument("--input", required=True, help="Local versioned-object JSON bundle")
    policy_evaluate.add_argument("--request-id", required=True)
    policy_evaluate.add_argument("--request-version", type=int)
    policy_evaluate.add_argument("--evaluated-at", help="ISO 8601 timestamp for reproducible evaluation")

    evidence = commands.add_parser("evidence", help="Export or verify advanced local evidence logs")
    evidence_commands = evidence.add_subparsers(dest="evidence_command", required=True)
    evidence_export = evidence_commands.add_parser("export")
    evidence_export.add_argument("--input", required=True, help="Local versioned-object JSON bundle")
    evidence_export.add_argument("--request-id", required=True)
    evidence_export.add_argument("--request-version", type=int)
    evidence_export.add_argument("--output", required=True, help="Local JSONL evidence log")
    evidence_export.add_argument("--actor", required=True)
    evidence_export.add_argument("--hash-chain", action="store_true")
    evidence_export.add_argument("--evaluated-at", help="ISO 8601 timestamp for reproducible evaluation")
    evidence_verify = evidence_commands.add_parser("verify")
    evidence_verify.add_argument("--input", required=True, help="Local JSONL evidence log")
    return parser


def _source_context(args: argparse.Namespace, workspace: Path) -> tuple[dict, str]:
    """Resolve an explicit advanced source or the zero-configuration packaged demo."""
    requested_source = getattr(args, "source", None)
    advanced_config = load_config(args.config) if args.config else None
    if advanced_config:
        configured_source = "demo" if advanced_config["profile"] == "demo" else "maysano"
        if requested_source and requested_source != configured_source:
            raise ValueError("--source conflicts with the advanced --config profile")
        requested_source = configured_source
    source = requested_source or "demo"
    if source == "demo":
        if advanced_config:
            return DemoClient(advanced_config["fixture"], advanced_config["scope"]).read_portfolio(), advanced_config["model"]["mode"]
        return read_packaged_demo(), "local"

    config = advanced_config
    environment_file = Path(args.env_file) if args.env_file else None
    if config is None:
        config_path = maysano_config_path(workspace)
        environment_file = maysano_environment_path(workspace)
        if not config_path.exists() or not environment_file.exists():
            raise ValueError("Maysano is not configured. Run `kentaro configure maysano` before using `--source maysano`.")
        config = load_config(config_path)
    if config["profile"] != "live":
        raise ValueError("Maysano source requires a live read-only profile")
    if environment_file is None:
        raise ValueError("Advanced live profiles require --env-file; or run `kentaro configure maysano` for local setup.")
    return LiveClient(environment_file, config["scope"]).read_portfolio(), config["model"]["mode"]


def _write_dashboard(context: dict, workspace: Path, *, output: str | None, inline: bool) -> Path:
    rendered = render_dashboard(context, inline=inline)
    if output:
        destination = Path(output).expanduser().resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("x", encoding="utf-8") as stream:
            stream.write(rendered)
        return destination
    while True:
        destination = timestamped_output(workspace, "portfolio-dashboard", ".html")
        try:
            with destination.open("x", encoding="utf-8") as stream:
                stream.write(rendered)
        except FileExistsError:
            continue
        return destination


def _run_demo(workspace: Path) -> None:
    context = read_packaged_demo()
    print("Kentaro synthetic demo — local, sourced, and read-only.")
    print()
    print(render_brief(context, "local"), end="")
    dashboard = _write_dashboard(context, workspace, output=None, inline=False)
    print(f"Dashboard: {dashboard}")


def _configure_maysano(args: argparse.Namespace, workspace: Path) -> None:
    api_base_url = args.api_base_url or input(f"Maysano API base URL [{DEFAULT_MAYSANO_BASE_URL}]: ").strip() or DEFAULT_MAYSANO_BASE_URL
    scope = args.scope or input("Portfolio scope [organization-bound]: ").strip() or "organization-bound"
    api_key = getpass.getpass("Maysano API key (stored locally and never displayed): ").strip()
    if not api_key:
        raise ValueError("Maysano API key is required")
    config, environment = write_maysano_setup(
        workspace,
        api_base_url=api_base_url,
        api_key=api_key,
        scope=scope,
        replace=args.replace,
    )
    load_config(config)
    load_live_environment(environment)
    print("Read-only Maysano source configured locally. Use `kentaro portfolio brief --source maysano`.")


def main(argv=None):
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        workspace = workspace_path()
        if args.command == "demo":
            _run_demo(workspace)
        elif args.command == "validate-config":
            if args.config:
                config = load_config(args.config)
                print(f"Valid {config['profile']} configuration; read-only enabled; cache and model execution disabled.")
            else:
                print("Valid built-in demo profile; read-only enabled; cache and model execution disabled.")
        elif args.command == "configure":
            _configure_maysano(args, workspace)
        elif args.command in {"data-product", "use-case", "objective"}:
            if args.artifact_command == "draft":
                record = create_local_draft(
                    args.artifact_type,
                    args.source,
                    workspace,
                    provider=args.provider,
                    model=args.model,
                    config=args.generation_config,
                    ollama_url=args.ollama_url,
                    profile=getattr(args, "profile", "minimal"),
                    allow_hosted_content=args.allow_hosted_content,
                )
                print(json.dumps({
                    "artifact_type": record["artifact_type"],
                    "source": record["source"],
                    "provider": record["generation"]["provider"],
                    "provider_mode": record["generation"]["provider_mode"],
                    "content_egress": record["generation"]["content_egress"],
                    "output": record["output"],
                    "limitations": record["limitations"],
                }, sort_keys=True))
            else:
                result = validate_local_artifact(args.artifact, workspace, artifact_type=args.artifact_type)
                print(json.dumps(result, sort_keys=True))
                if not result["artifact"]["valid"]:
                    return 2
        elif args.command == "object":
            result = validate_bundle(load_bundle(args.input))
            print(json.dumps(result, sort_keys=True))
            if not result["valid"]:
                return 2
        elif args.command == "policy":
            result = evaluate_execution_request(
                load_bundle(args.input),
                args.request_id,
                request_version=args.request_version,
                evaluated_at=args.evaluated_at,
            )
            print(json.dumps(result, sort_keys=True))
        elif args.command == "evidence":
            if args.evidence_command == "verify":
                result = verify_evidence_log(args.input)
                print(json.dumps(result, sort_keys=True))
                if not result["valid"]:
                    return 2
            else:
                bundle = load_bundle(args.input)
                evaluation = evaluate_execution_request(
                    bundle,
                    args.request_id,
                    request_version=args.request_version,
                    evaluated_at=args.evaluated_at,
                )
                event = build_evidence_event(bundle, evaluation, actor=args.actor)
                stored = append_evidence_event(args.output, event, hash_chain=args.hash_chain)
                print(json.dumps({"path": str(Path(args.output).resolve()), "event_id": stored["id"], "record_hash": stored.get("record_hash")}, sort_keys=True))
        else:
            context, model_policy = _source_context(args, workspace)
            if args.command == "dashboard":
                output = _write_dashboard(context, workspace, output=args.output, inline=args.inline)
                print(output)
            else:
                print(render_brief(context, model_policy), end="")
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(f"kentaro: {error}", file=sys.stderr)
        return 2
    return 0
