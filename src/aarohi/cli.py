"""Command-line entry point for Aarohi."""

import argparse
from collections.abc import Sequence


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="aarohi", description="Aarohi AI agent")
    parser.add_argument("command", choices=["about"], nargs="?", default="about")
    args = parser.parse_args(argv)
    if args.command == "about":
        print("Aarohi - modular personal AI agent (foundation scaffold)")
