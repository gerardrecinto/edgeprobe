from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from edgeprobe.classifier import classify
from edgeprobe.parsers import load_snapshot
from edgeprobe.reporters import json_report, terminal_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="edgeprobe",
        description="Analyze Linux edge host snapshots for readiness risks.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    analyze = subcommands.add_parser("analyze", help="Analyze a captured host snapshot directory.")
    analyze.add_argument("snapshot", type=Path, help="Path to snapshot fixture or collector output.")
    analyze.add_argument(
        "--output",
        choices=("terminal", "json"),
        default="terminal",
        help="Report format.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "analyze":
            snapshot = load_snapshot(args.snapshot)
            report = classify(snapshot)
            rendered = json_report(report) if args.output == "json" else terminal_report(report)
            print(rendered)
            return 2 if report.status == "ACTION REQUIRED" else 0
    except (FileNotFoundError, NotADirectoryError, PermissionError, UnicodeDecodeError) as error:
        print(f"edgeprobe: {error}", file=sys.stderr)
        return 1

    parser.error(f"unknown command: {args.command}")
    return 1

