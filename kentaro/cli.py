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
from kentaro.design.portfolio import (
    KINDS as DESIGN_KINDS,
    RELATIONSHIPS as DESIGN_RELATIONSHIPS,
    add_object,
    add_relationship,
    create_design_portfolio,
    load_portfolio,
    make_claim,
    migrate_portfolio,
    save_portfolio,
    set_claim,
    validate_portfolio,
)
from kentaro.design.render import render_canvas
from kentaro.design.reports import analysis as design_analysis
from kentaro.design.reports import executive_summary, manifest, readiness, stale_outputs, unresolved_decisions, validate_odps
from kentaro.design.handover import export_handover, handover_status, inspect_handover, prepare_handover_review, validate_handover
from kentaro.design.engagement import load_engagement_state, state_path, update_engagement_state
from kentaro.design.proposal import propose_design
from kentaro.scenarios.udemy_masterclass import odps_fixture, starting_portfolio
from kentaro.workspace import (
    DEFAULT_MAYSANO_BASE_URL,
    maysano_config_path,
    maysano_environment_path,
    timestamped_output,
    workspace_path,
    write_codex_workspace_instructions,
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

    setup = commands.add_parser("setup", help="Prepare a local learner workspace")
    setup_commands = setup.add_subparsers(dest="setup_command", required=True)
    codex_setup = setup_commands.add_parser("codex", help="Write non-overwriting Codex instructions to this workspace")
    codex_setup.add_argument("--replace", action="store_true", help="Explicitly replace an existing workspace AGENTS.md")

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
    masterclass = commands.add_parser("masterclass", help="Run the deterministic local Masterclass Companion")
    masterclass_commands = masterclass.add_subparsers(dest="masterclass_command", required=True)
    initialise = masterclass_commands.add_parser("init", help="Write the synthetic Customer Risk Intelligence starting portfolio")
    initialise.add_argument("--output", help="Local portfolio JSON path; defaults to the ignored workspace")
    validate_masterclass = masterclass_commands.add_parser("validate", help="Validate a local DesignPortfolio through the course adapter")
    validate_masterclass.add_argument("--input", required=True)
    render_masterclass = masterclass_commands.add_parser("render", help="Render a local DesignPortfolio HTML canvas through the course adapter")
    render_masterclass.add_argument("--input", required=True)
    render_masterclass.add_argument("--output", required=True)
    report_masterclass = masterclass_commands.add_parser("report", help="Write deterministic readiness and executive reports")
    report_masterclass.add_argument("--input", required=True)
    report_masterclass.add_argument("--output-dir", required=True)
    validate_odps_masterclass = masterclass_commands.add_parser("validate-odps", help="Validate an ODPS fixture with the pinned SDK")
    validate_odps_masterclass.add_argument("--artifact", help="Optional local ODPS artifact; defaults to the packaged Customer Profile course fixture")
    status_masterclass = masterclass_commands.add_parser("status", help="Check a generated manifest for stale outputs")
    status_masterclass.add_argument("--input", required=True)
    status_masterclass.add_argument("--manifest", required=True)
    design = commands.add_parser("design", help="Create and assess reusable local DesignPortfolio artefacts")
    design_commands = design.add_subparsers(dest="design_command", required=True)
    design_init = design_commands.add_parser("init", help="Create a blank local DesignPortfolio or explicitly selected scenario")
    design_init.add_argument("--title", help="Required for a blank portfolio")
    design_init.add_argument("--portfolio-id", help="Required for a blank portfolio")
    design_init.add_argument("--scenario", choices=("udemy-masterclass",), help="Explicit scenario starter; generic design never defaults to one")
    design_init.add_argument("--assessment-stage", default="discovery", choices=("discovery", "design", "implementation", "operation"), help="Recorded lifecycle stage; new designs default to discovery")
    design_init.add_argument("--output", required=True)
    design_propose = design_commands.add_parser("propose", help="Create a bounded, source-labelled initial local design from minimal business input")
    design_propose.add_argument("--business-input", required=True, help="The business owner's initial problem statement")
    design_propose.add_argument("--output", required=True, help="Local DesignPortfolio path under .kentaro/workspace/")
    design_propose.add_argument("--output-dir", help="Optional local directory for the canvas and reports")
    design_add_object = design_commands.add_parser("add-object", help="Add a structured objective, use case, AI product, or data product")
    design_add_object.add_argument("--input", required=True)
    design_add_object.add_argument("--id", required=True)
    design_add_object.add_argument("--kind", required=True, choices=sorted(DESIGN_KINDS))
    design_add_object.add_argument("--name", required=True)
    design_add_object.add_argument("--purpose", required=True)
    design_add_object.add_argument("--owner", required=True)
    design_add_object.add_argument("--lifecycle-status", required=True)
    design_add_object.add_argument("--ai-involvement", help="Optional use-case Claim value, such as none or proposed")
    design_add_object.add_argument("--status", default="proposed", choices=("case_fact", "user_confirmed", "proposed", "assumed", "unknown"))
    design_add_object.add_argument("--source-id", default="local:user")
    design_add_object.add_argument("--source-revision", default="local-v1")
    design_add_object.add_argument("--derivation-input-hash", default="local-user-input")
    design_add_relationship = design_commands.add_parser("add-relationship", help="Add a typed semantic relationship")
    design_add_relationship.add_argument("--input", required=True)
    design_add_relationship.add_argument("--id", required=True)
    design_add_relationship.add_argument("--from-id", required=True)
    design_add_relationship.add_argument("--to-id", required=True)
    design_add_relationship.add_argument("--kind", required=True, choices=sorted(DESIGN_RELATIONSHIPS))
    design_add_relationship.add_argument("--status", default="proposed", choices=("case_fact", "user_confirmed", "proposed", "assumed", "unknown"), help="Evidence status for the declared relationship")
    design_add_relationship.add_argument("--source-id", default="local:user")
    design_add_relationship.add_argument("--source-revision", default="local-v1")
    design_add_relationship.add_argument("--derivation-input-hash", default="local-user-input")
    design_set_claim = design_commands.add_parser("set-claim", help="Set one canonical Claim on the portfolio or a design object")
    design_set_claim.add_argument("--input", required=True)
    design_set_claim.add_argument("--field", required=True)
    design_set_claim.add_argument("--value", required=True)
    design_set_claim.add_argument("--object-id")
    design_set_claim.add_argument("--status", required=True, choices=("case_fact", "user_confirmed", "proposed", "assumed", "unknown"))
    design_set_claim.add_argument("--source-id", required=True)
    design_set_claim.add_argument("--source-revision", required=True)
    design_set_claim.add_argument("--derivation-input-hash", required=True)
    design_set_stage = design_commands.add_parser("set-assessment-stage", help="Record the lifecycle stage for subsequent local assessment")
    design_set_stage.add_argument("--input", required=True)
    design_set_stage.add_argument("--assessment-stage", required=True, choices=("discovery", "design", "implementation", "operation"))
    design_validate = design_commands.add_parser("validate", help="Validate a local DesignPortfolio")
    design_validate.add_argument("--input", required=True)
    design_analyze = design_commands.add_parser("analyze", help="Analyze links, reuse opportunities, and readiness")
    design_analyze.add_argument("--input", required=True)
    design_analyze.add_argument("--assessment-stage", choices=("discovery", "design", "implementation", "operation"), help="Override the recorded assessment stage for this analysis only")
    design_render = design_commands.add_parser("render", help="Render a local DesignPortfolio HTML canvas")
    design_render.add_argument("--input", required=True)
    design_render.add_argument("--output", required=True)
    design_render.add_argument("--assessment-stage", choices=("discovery", "design", "implementation", "operation"), help="Override the recorded assessment stage for this canvas only")
    design_report = design_commands.add_parser("report", help="Write deterministic readiness and executive reports")
    design_report.add_argument("--input", required=True)
    design_report.add_argument("--output-dir", required=True)
    design_report.add_argument("--assessment-stage", choices=("discovery", "design", "implementation", "operation"), help="Override the recorded assessment stage for this report only")
    design_status = design_commands.add_parser("status", help="Check a generated manifest for stale outputs")
    design_status.add_argument("--input", required=True)
    design_status.add_argument("--manifest", required=True)
    design_engagement = design_commands.add_parser("engagement", help="Read or refresh the persistent engagement state derived from a DesignPortfolio")
    engagement_commands = design_engagement.add_subparsers(dest="engagement_command", required=True)
    engagement_status = engagement_commands.add_parser("status", help="Show the current delivery requirements, missing information, and next question")
    engagement_status.add_argument("--input", required=True)
    engagement_refresh = engagement_commands.add_parser("refresh", help="Execute the complete portfolio evaluation and rebuild persistent state")
    engagement_refresh.add_argument("--input", required=True)
    engagement_evaluate = engagement_commands.add_parser("evaluate", help="Alias for refresh; evaluate the complete portfolio after a user interaction")
    engagement_evaluate.add_argument("--input", required=True)
    design_migrate = design_commands.add_parser("migrate", help="Migrate a v0.2 LearningPortfolio to DesignPortfolio")
    design_migrate.add_argument("--input", required=True)
    design_migrate.add_argument("--output", required=True)
    design_odps = design_commands.add_parser("validate-odps", help="Validate a local ODPS artifact with the pinned SDK")
    design_odps.add_argument("--artifact", required=True)
    design_handover = design_commands.add_parser("handover", help="Generate and inspect a deterministic local Decision Context handover package")
    handover_commands = design_handover.add_subparsers(dest="handover_command", required=True)
    handover_prepare = handover_commands.add_parser("prepare-review", help="Prepare local review material; it is not the final handover")
    handover_prepare.add_argument("--input", required=True, help="Local DesignPortfolio path under .kentaro/workspace/")
    handover_prepare.add_argument("--output", required=True, help="New local review directory under .kentaro/workspace/")
    handover_prepare.add_argument("--assessment-stage", choices=("discovery", "design", "implementation", "operation"), help="Override the recorded assessment stage for this review only")
    handover_generate = handover_commands.add_parser("generate", help="Generate the final ZIP after explicit user review confirmation")
    handover_generate.add_argument("--input", required=True, help="Local DesignPortfolio path under .kentaro/workspace/")
    handover_generate.add_argument("--output", required=True, help="New final .zip path under .kentaro/workspace/")
    handover_generate.add_argument("--reviewer", required=True, help="Name of the user who explicitly confirmed this handover")
    handover_generate.add_argument("--confirmation", required=True, help="The user's recorded confirmation statement")
    handover_generate.add_argument("--acknowledge-open-decisions", action="store_true", help="Record that the confirming user reviewed every unresolved decision")
    handover_generate.add_argument("--assessment-stage", choices=("discovery", "design", "implementation", "operation"), help="Override the recorded assessment stage for this package only")
    handover_validate = handover_commands.add_parser("validate", help="Validate handover package artifact integrity")
    handover_validate.add_argument("--package", required=True, help="Local handover package directory under .kentaro/workspace/")
    handover_inspect = handover_commands.add_parser("inspect", help="Inspect the handover manifest and integrity findings")
    handover_inspect.add_argument("--package", required=True, help="Local handover package directory under .kentaro/workspace/")
    handover_status = handover_commands.add_parser("status", help="Check whether a handover package is stale against a local DesignPortfolio")
    handover_status.add_argument("--input", required=True, help="Local DesignPortfolio path under .kentaro/workspace/")
    handover_status.add_argument("--package", required=True, help="Local handover package directory under .kentaro/workspace/")
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


def _workspace_output(path: str | Path, workspace: Path) -> Path:
    """Keep local DesignPortfolio artefacts within the ignored Kentaro workspace."""
    target = Path(path).expanduser().resolve()
    try:
        target.relative_to(workspace.resolve())
    except ValueError as error:
        raise ValueError("DesignPortfolio artefacts must be under .kentaro/workspace/") from error
    return target


def _write_design_reports(portfolio: dict, destination: Path, *, assessment_stage: str | None = None) -> dict:
    result = readiness(portfolio, assessment_stage=assessment_stage)
    if not result["valid"]:
        raise ValueError("DesignPortfolio is invalid")
    destination.mkdir(parents=True, exist_ok=True)
    readiness_path = destination / "readiness-report.json"
    summary_path = destination / "executive-summary.md"
    decisions_path = destination / "unresolved-decisions.md"
    canvas_path = destination / "canvas.html"
    readiness_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary_path.write_text(executive_summary(portfolio, result), encoding="utf-8")
    decisions_path.write_text(unresolved_decisions(portfolio, result), encoding="utf-8")
    canvas_path.write_text(render_canvas(portfolio, assessment_stage=assessment_stage), encoding="utf-8")
    manifest_path = destination / "manifest.json"
    outputs = {"readiness": readiness_path, "summary": summary_path, "unresolved_decisions": decisions_path, "canvas": canvas_path}
    manifest_path.write_text(json.dumps(manifest(portfolio, outputs), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def _refresh_engagement(portfolio_path: Path, *, delivery: dict | None = None) -> tuple[Path, dict]:
    """Keep the generated progress index aligned with the saved DesignPortfolio."""
    return update_engagement_state(load_portfolio(portfolio_path), portfolio_path, delivery=delivery)


def _stage_masterclass_fixtures(portfolio_path: Path) -> None:
    """Make the two course ODPS exercises available beside a learner's local portfolio."""
    for repair in (False, True):
        source = odps_fixture(repair)
        destination = portfolio_path.parent / source.name
        if not destination.exists():
            destination.write_bytes(source.read_bytes())


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
        elif args.command == "setup":
            instructions = write_codex_workspace_instructions(replace=args.replace)
            print(json.dumps({"codex_instructions": str(instructions), "workspace": str(workspace), "replaced": args.replace}, sort_keys=True))
        elif args.command == "masterclass":
            if args.masterclass_command == "init":
                output = _workspace_output(args.output, workspace) if args.output else workspace / "masterclass" / "customer-risk-intelligence" / "portfolio.json"
                saved = save_portfolio(starting_portfolio(), output)
                state, _ = _refresh_engagement(saved)
                _stage_masterclass_fixtures(saved)
                print(json.dumps({"portfolio": str(saved), "engagement_state": str(state), "local_only": True, "maysano_connection": False}, sort_keys=True))
            elif args.masterclass_command == "validate":
                result = validate_portfolio(load_portfolio(_workspace_output(args.input, workspace))); print(json.dumps({key: value for key, value in result.items() if key != "portfolio"}, sort_keys=True));
                if not result["valid"]: return 2
            elif args.masterclass_command == "render":
                html = render_canvas(load_portfolio(_workspace_output(args.input, workspace))); output = _workspace_output(args.output, workspace); output.parent.mkdir(parents=True, exist_ok=True); output.write_text(html, encoding="utf-8"); print(output)
            elif args.masterclass_command == "report":
                portfolio = load_portfolio(_workspace_output(args.input, workspace)); result = readiness(portfolio)
                if not result["valid"]: print(json.dumps(result, sort_keys=True)); return 2
                destination = _workspace_output(args.output_dir, workspace); result = _write_design_reports(portfolio, destination)
                print(json.dumps({"output_dir": str(destination), "blockers": result["summary"]["blockers"], "warnings": result["summary"]["warnings"]}, sort_keys=True))
            elif args.masterclass_command == "validate-odps":
                result = validate_odps(args.artifact or odps_fixture()); print(json.dumps(result, sort_keys=True));
                if not result.get("valid"): return 2
            else:
                portfolio = load_portfolio(_workspace_output(args.input, workspace)); manifest_data = json.loads(_workspace_output(args.manifest, workspace).read_text(encoding="utf-8")); print(json.dumps({"artifacts": stale_outputs(portfolio, manifest_data)}, sort_keys=True))
        elif args.command == "design":
            if args.design_command == "init":
                output = _workspace_output(args.output, workspace)
                if args.scenario:
                    portfolio = starting_portfolio()
                else:
                    if not args.title or not args.portfolio_id:
                        raise ValueError("Generic design init requires --title and --portfolio-id; scenarios require explicit --scenario")
                    portfolio = create_design_portfolio(args.title, args.portfolio_id)
                portfolio["assessment_stage"] = args.assessment_stage
                saved = save_portfolio(portfolio, output)
                state, _ = _refresh_engagement(saved)
                print(json.dumps({"portfolio": str(saved), "engagement_state": str(state), "model": "DesignPortfolio", "scenario": args.scenario, "local_only": True}, sort_keys=True))
            elif args.design_command == "propose":
                output = _workspace_output(args.output, workspace)
                proposal = propose_design(args.business_input)
                saved = save_portfolio(proposal["portfolio"], output)
                state, _ = _refresh_engagement(saved)
                destination = _workspace_output(args.output_dir, workspace) if args.output_dir else output.parent / "proposal"
                _write_design_reports(proposal["portfolio"], destination)
                print(json.dumps({
                    "portfolio": str(saved),
                    "engagement_state": str(state),
                    "output_dir": str(destination),
                    "frame": proposal["frame"],
                    "clarification_questions": proposal["clarification_questions"],
                    "measurement": proposal["measurement"],
                    "local_only": True,
                }, sort_keys=True))
            elif args.design_command == "add-object":
                portfolio = load_portfolio(_workspace_output(args.input, workspace))
                source = (args.source_id, args.source_revision, args.derivation_input_hash)
                claims = {field: make_claim(value, args.status, *source) for field, value in {"name": args.name, "purpose": args.purpose, "owner": args.owner, "lifecycle_status": args.lifecycle_status}.items()}
                if args.ai_involvement is not None:
                    claims["ai_involvement"] = make_claim(args.ai_involvement, args.status, *source)
                saved = save_portfolio(add_object(portfolio, args.id, args.kind, claims), _workspace_output(args.input, workspace))
                state, _ = _refresh_engagement(saved); print(json.dumps({"portfolio": str(saved), "engagement_state": str(state)}, sort_keys=True))
            elif args.design_command == "add-relationship":
                portfolio = load_portfolio(_workspace_output(args.input, workspace))
                provenance = make_claim("declared relationship", args.status, args.source_id, args.source_revision, args.derivation_input_hash)
                saved = save_portfolio(add_relationship(portfolio, args.id, args.from_id, args.to_id, args.kind, provenance=provenance), _workspace_output(args.input, workspace))
                state, _ = _refresh_engagement(saved); print(json.dumps({"portfolio": str(saved), "engagement_state": str(state)}, sort_keys=True))
            elif args.design_command == "set-claim":
                portfolio = load_portfolio(_workspace_output(args.input, workspace))
                claim = make_claim(args.value, args.status, args.source_id, args.source_revision, args.derivation_input_hash)
                saved = save_portfolio(set_claim(portfolio, args.field, claim, object_id=args.object_id), _workspace_output(args.input, workspace))
                state, _ = _refresh_engagement(saved); print(json.dumps({"portfolio": str(saved), "engagement_state": str(state)}, sort_keys=True))
            elif args.design_command == "set-assessment-stage":
                portfolio = load_portfolio(_workspace_output(args.input, workspace))
                portfolio["assessment_stage"] = args.assessment_stage
                saved = save_portfolio(portfolio, _workspace_output(args.input, workspace))
                state, _ = _refresh_engagement(saved); print(json.dumps({"portfolio": str(saved), "engagement_state": str(state)}, sort_keys=True))
            elif args.design_command == "validate":
                result = validate_portfolio(load_portfolio(_workspace_output(args.input, workspace))); print(json.dumps({key: value for key, value in result.items() if key != "portfolio"}, sort_keys=True));
                if not result["valid"]: return 2
            elif args.design_command == "analyze":
                result = design_analysis(load_portfolio(_workspace_output(args.input, workspace)), assessment_stage=args.assessment_stage); print(json.dumps(result, sort_keys=True));
                if not result["valid"]: return 2
            elif args.design_command == "render":
                output = _workspace_output(args.output, workspace); output.parent.mkdir(parents=True, exist_ok=True); output.write_text(render_canvas(load_portfolio(_workspace_output(args.input, workspace)), assessment_stage=args.assessment_stage), encoding="utf-8"); print(output)
            elif args.design_command == "report":
                portfolio = load_portfolio(_workspace_output(args.input, workspace)); destination = _workspace_output(args.output_dir, workspace); result = _write_design_reports(portfolio, destination, assessment_stage=args.assessment_stage)
                print(json.dumps({"output_dir": str(destination), "assessment_stage": result["assessment_stage"], "findings": result["summary"]["by_category"]}, sort_keys=True))
            elif args.design_command == "status":
                portfolio = load_portfolio(_workspace_output(args.input, workspace)); manifest_data = json.loads(_workspace_output(args.manifest, workspace).read_text(encoding="utf-8")); print(json.dumps({"artifacts": stale_outputs(portfolio, manifest_data)}, sort_keys=True))
            elif args.design_command == "engagement":
                portfolio_path = _workspace_output(args.input, workspace)
                if args.engagement_command in {"refresh", "evaluate"}:
                    state, result = _refresh_engagement(portfolio_path)
                else:
                    state = state_path(portfolio_path)
                    result = load_engagement_state(state) if state.exists() else _refresh_engagement(portfolio_path)[1]
                print(json.dumps({"engagement_state": str(state), "state": result}, sort_keys=True))
            elif args.design_command == "migrate":
                output = _workspace_output(args.output, workspace); saved = save_portfolio(migrate_portfolio(json.loads(_workspace_output(args.input, workspace).read_text(encoding="utf-8"))), output); state, _ = _refresh_engagement(saved); print(json.dumps({"portfolio": str(saved), "engagement_state": str(state)}, sort_keys=True))
            elif args.design_command == "validate-odps":
                result = validate_odps(args.artifact); print(json.dumps(result, sort_keys=True));
                if not result.get("valid"): return 2
            elif args.design_command == "handover":
                package = _workspace_output(args.output, workspace) if args.handover_command in {"prepare-review", "generate"} else _workspace_output(args.package, workspace)
                if args.handover_command == "prepare-review":
                    portfolio = load_portfolio(_workspace_output(args.input, workspace))
                    result = prepare_handover_review(portfolio, package, assessment_stage=args.assessment_stage)
                    _refresh_engagement(_workspace_output(args.input, workspace), delivery={"status": "review_material_prepared", "source_hash": result["manifest"]["source"]["portfolio_hash"], "package": str(package), "specifications_generated": False})
                    print(json.dumps({"review_material": str(result["package"]), "status": result["manifest"]["status"], "source": result["manifest"]["source"]}, sort_keys=True))
                elif args.handover_command == "generate":
                    portfolio = load_portfolio(_workspace_output(args.input, workspace))
                    result = export_handover(portfolio, package, reviewer=args.reviewer, confirmation=args.confirmation, acknowledge_all_open_decisions=args.acknowledge_open_decisions, assessment_stage=args.assessment_stage)
                    _refresh_engagement(_workspace_output(args.input, workspace), delivery={"status": "generated", "source_hash": result["manifest"]["source"]["portfolio_hash"], "package": str(result["package"]), "specifications_generated": bool(result["manifest"]["specification_status"]) and all(item.get("status") == "validated" for item in result["manifest"]["specification_status"])})
                    print(json.dumps({"handover_zip": str(result["package"]), "status": result["manifest"]["status"], "source": result["manifest"]["source"], "specification_status": result["manifest"]["specification_status"]}, sort_keys=True))
                elif args.handover_command == "validate":
                    result = validate_handover(package)
                    print(json.dumps(result, sort_keys=True))
                    if not result["valid"]: return 2
                elif args.handover_command == "inspect":
                    result = inspect_handover(package)
                    print(json.dumps(result, sort_keys=True))
                    if not result["valid"]: return 2
                else:
                    portfolio = load_portfolio(_workspace_output(args.input, workspace))
                    result = handover_status(portfolio, package)
                    print(json.dumps(result, sort_keys=True))
                    if not result["valid"]: return 2
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
