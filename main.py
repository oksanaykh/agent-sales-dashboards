"""
main.py

CLI entry point for the Sales Dashboard Agent.

Usage:
  python main.py --source datasets/sales.csv
  python main.py --source datasets/sales.csv --verbose
  python main.py --source datasets/sales.csv --open
  python main.py --source datasets/sales.csv --output-json state.json
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from pathlib import Path

from agents.graph import get_app
from agents.state import initial_state


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)-8s] %(name)s - %(message)s",
        datefmt="%H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    if not verbose:
        for noisy in ("httpx", "httpcore", "anthropic", "urllib3"):
            logging.getLogger(noisy).setLevel(logging.WARNING)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sales-dashboard-agent",
        description="Sales Dashboard Agent — builds HTML dashboards for 3 audiences from a CSV.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python main.py --source datasets/sales.csv
  python main.py --source datasets/sales.csv --verbose --open
  python main.py --source datasets/sales.csv --output-json state.json
""",
    )
    parser.add_argument(
        "--source", "-s",
        type=str,
        default="datasets/sales.csv",
        help="Path to CSV file (default: datasets/sales.csv)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable DEBUG logging",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open the combined dashboard in the default browser after generation",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        metavar="FILE",
        help="Save final agent state as JSON to this file",
    )
    return parser


def _print_summary(final_state: dict) -> None:
    messages = final_state.get("messages", [])
    error    = final_state.get("error")

    print("\n" + "=" * 64)
    if error:
        print(f"  [FAILED]  Agent failed: {error}")
    else:
        print(f"  [OK]  Dashboards generated successfully")
    print("=" * 64)

    print(f"\n  Agent log ({len(messages)} steps):")
    for msg in messages:
        print(f"    {msg}")

    if not error:
        print(f"\n  Output files:")
        labels = {
            "dashboard_exec_path":      "  Executive    ",
            "dashboard_product_path":   "  Product Team ",
            "dashboard_marketing_path": "  Marketing    ",
            "dashboard_combined_path":  "  * Combined   ",
        }
        for key, label in labels.items():
            path = final_state.get(key, "")
            if path:
                print(f"    {label} -> {path}")

    print()


def main() -> int:
    parser = build_parser()
    args   = parser.parse_args()

    _setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    if not Path(args.source).exists():
        print(f"[ERROR] Source file not found: {args.source}", file=sys.stderr)
        return 1

    logger.info("Starting Sales Dashboard Agent")
    logger.info("Source: %s", args.source)

    app   = get_app()
    state = initial_state(args.source)

    try:
        final_state = app.invoke(state)
    except Exception as exc:
        logger.exception("Agent crashed: %s", exc)
        return 2

    if args.output_json:
        out = Path(args.output_json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(final_state, indent=2, default=str, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("State saved -> %s", out)

    _print_summary(final_state)

    if args.open and not final_state.get("error"):
        combined = final_state.get("dashboard_combined_path", "")
        if combined and Path(combined).exists():
            try:
                if sys.platform == "darwin":
                    subprocess.run(["open", combined])
                elif sys.platform.startswith("linux"):
                    subprocess.run(["xdg-open", combined])
                elif sys.platform == "win32":
                    subprocess.run(["start", combined], shell=True)
            except Exception as e:
                logger.warning("Could not open browser: %s", e)

    return 0 if not final_state.get("error") else 1


if __name__ == "__main__":
    sys.exit(main())
