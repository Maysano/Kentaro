import argparse
import sys
from pathlib import Path
from kentaro.dashboard.render import render_dashboard
from kentaro.config.loader import load_config
from kentaro.api.demo import DemoClient
from kentaro.reports.brief import render_brief


def main(argv=None):
    parser = argparse.ArgumentParser(description="Kentaro read-only demo harness")
    parser.add_argument("--config", required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("validate-config")
    dashboard = commands.add_parser("dashboard")
    dashboard.add_argument("--output", required=True)
    dashboard.add_argument("--inline", action="store_true", help="Render a conversation HTML fragment")
    portfolio = commands.add_parser("portfolio")
    portfolio.add_subparsers(dest="workflow", required=True).add_parser("brief")
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        if args.command == "validate-config":
            print("Valid demo configuration; read-only enabled; cache and model execution disabled.")
        else:
            context = DemoClient(config["fixture"], config["scope"]).read_portfolio()
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
