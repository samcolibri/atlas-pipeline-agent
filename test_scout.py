"""
SCOUT test — pulls FDIC + NCUA account universe.

Usage:
    python3 test_scout.py                    # all US, dry run
    python3 test_scout.py --states IL WI MN  # specific states
    python3 test_scout.py --write            # write to Supabase
    python3 test_scout.py --min 500          # $500M+ assets only
"""

import sys
import logging
import argparse
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

from atlas.agents.scout import ScoutAgent
from atlas.integrations.fdic import FDICClient


def main():
    parser = argparse.ArgumentParser(description="ATLAS SCOUT — FDIC/NCUA account pull")
    parser.add_argument("--states", nargs="+", help="State codes to filter (e.g. IL WI MN)")
    parser.add_argument("--min",    type=int, default=100,    help="Min assets in $M (default: 100)")
    parser.add_argument("--max",    type=int, default=10_000, help="Max assets in $M (default: 10000)")
    parser.add_argument("--write",  action="store_true",       help="Write results to Supabase")
    parser.add_argument("--no-cu",  action="store_true",       help="Skip credit unions")
    parser.add_argument("--fdic-only", action="store_true",    help="Quick FDIC-only test (no NCUA)")
    args = parser.parse_args()

    if args.fdic_only:
        # Quick FDIC sanity check
        print("\n── FDIC Quick Test ──────────────────────────────")
        client = FDICClient()
        results = client.get_institutions(
            asset_min_k=args.min * 1_000,
            asset_max_k=args.max * 1_000,
            states=args.states,
        )
        print(f"  Total FDIC banks in range: {len(results):,}")
        print(f"\n  Sample (top 10 by assets):")
        for inst in results[:10]:
            print(f"    {inst.display()}")
        return

    # Full SCOUT run
    scout = ScoutAgent()
    result = scout.run(
        asset_min_m=args.min,
        asset_max_m=args.max,
        states=args.states,
        include_credit_unions=not args.no_cu,
        dry_run=not args.write,
    )
    result.display()

    if not args.write:
        print("  (Dry run — use --write to persist to Supabase)\n")

    # Show breakdown by type
    from collections import Counter
    types = Counter(i.institution_type for i in result.institutions)
    states = Counter(i.state for i in result.institutions)
    print(f"  By type:  {dict(types)}")
    print(f"  Top states: {dict(states.most_common(5))}")
    print()


if __name__ == "__main__":
    main()
