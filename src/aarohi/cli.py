"""Command-line entry point for Aarohi."""

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(prog="aarohi", description="Aarohi AI agent")
    parser.add_argument("command", choices=["about"], nargs="?", default="about")
    args = parser.parse_args()
    if args.command == "about":
        print("Aarohi — modular personal AI agent (foundation scaffold)")
