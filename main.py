"""
main.py - CLI entry point (unchanged from original)
"""
from __future__ import annotations
import argparse, json, logging, subprocess, sys
from pathlib import Path
from agents.graph import get_app
from agents.state import initial_state

def _setup_logging(verbose):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s [%(levelname)-8s] %(name)s - %(message)s",
                        datefmt="%H:%M:%S", handlers=[logging.StreamHandler(sys.stdout)])

def build_parser():
    p = argparse.ArgumentParser(prog="sales-dashboard-agent")
    p.add_argument("--source", "-s", default="datasets/sales.csv")
    p.add_argument("--verbose", "-v", action="store_true")
    p.add_argument("--open", action="store_true")
    p.add_argument("--output-json", metavar="FILE")
    return p

def main():
    args = build_parser().parse_args()
    _setup_logging(args.verbose)
    if not Path(args.source).exists():
        print(f"[ERROR] File not found: {args.source}", file=sys.stderr)
        return 1
    app = get_app()
    final = app.invoke(initial_state(args.source))
    print(f"\n{'='*60}")
    if final.get("error"):
        print(f"  [FAILED] {final['error']}")
    else:
        print(f"  [OK] Dashboards generated")
        for k in ("dashboard_combined_path",):
            if final.get(k):
                print(f"  → {final[k]}")
    print()
    return 0 if not final.get("error") else 1

if __name__ == "__main__":
    sys.exit(main())
