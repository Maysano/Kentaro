import argparse
import sys
from kentaro.config.loader import load_config
from kentaro.api.demo import DemoClient
from kentaro.reports.brief import render_brief


def main(argv=None):
    parser = argparse.ArgumentParser(description="Kentaro read-only demo harness")
    parser.add_argument("--config", required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("validate-config")
    portfolio = commands.add_parser("portfolio")
    portfolio.add_subparsers(dest="workflow", required=True).add_parser("brief")
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        if args.command == "validate-config":
            print("Valid demo configuration; read-only enabled; cache and model execution disabled.")
        else:
            context = DemoClient(config["fixture"], config["scope"]).read_portfolio()
            print(render_brief(context, config["model"]["mode"]), end="")
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(f"kentaro: {error}", file=sys.stderr)
        return 2
    return 0
