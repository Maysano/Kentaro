import argparse
import json
import sys
from pathlib import Path
from kentaro.dashboard.render import render_dashboard
from kentaro.config.loader import load_config
from kentaro.api.demo import DemoClient
from kentaro.api.live import LiveClient
from kentaro.governance import (
    append_evidence_event,
    build_evidence_event,
    evaluate_execution_request,
    load_bundle,
    validate_bundle,
    verify_evidence_log,
)
from kentaro.reports.brief import render_brief


def main(argv=None):
    parser = argparse.ArgumentParser(description="Kentaro read-only Agentic Maysano Harness")
    parser.add_argument("--config", required=True)
    parser.add_argument("--env-file", help="Ignored local live API environment file")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("validate-config")
    dashboard = commands.add_parser("dashboard")
    dashboard.add_argument("--output", required=True)
    dashboard.add_argument("--inline", action="store_true", help="Render a conversation HTML fragment")
    portfolio = commands.add_parser("portfolio")
    portfolio.add_subparsers(dest="workflow", required=True).add_parser("brief")
    objects = commands.add_parser("object")
    object_commands = objects.add_subparsers(dest="object_command", required=True)
    object_validate = object_commands.add_parser("validate")
    object_validate.add_argument("--input", required=True, help="Local versioned-object JSON bundle")
    policy = commands.add_parser("policy")
    policy_commands = policy.add_subparsers(dest="policy_command", required=True)
    policy_evaluate = policy_commands.add_parser("evaluate")
    policy_evaluate.add_argument("--input", required=True, help="Local versioned-object JSON bundle")
    policy_evaluate.add_argument("--request-id", required=True)
    policy_evaluate.add_argument("--request-version", type=int)
    policy_evaluate.add_argument("--evaluated-at", help="ISO 8601 timestamp for reproducible evaluation")
    evidence = commands.add_parser("evidence")
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
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        if args.command == "validate-config":
            print(f"Valid {config['profile']} configuration; read-only enabled; cache and model execution disabled.")
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
            if config["profile"] == "demo":
                context = DemoClient(config["fixture"], config["scope"]).read_portfolio()
            else:
                if not args.env_file:
                    raise ValueError("Live profile requires --env-file pointing to an ignored local file")
                context = LiveClient(args.env_file, config["scope"]).read_portfolio()
            if args.command == "dashboard":
                output = Path(args.output).resolve()
                output.parent.mkdir(parents=True, exist_ok=True)
                with output.open("x", encoding="utf-8") as stream:
                    stream.write(render_dashboard(context, inline=args.inline))
                print(output)
            else:
                print(render_brief(context, config["model"]["mode"]), end="")
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(f"kentaro: {error}", file=sys.stderr)
        return 2
    return 0
