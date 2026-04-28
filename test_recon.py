"""
Test RECON agent — pure 6sense, no Claude.
Usage:
    python3 test_recon.py                        # runs 4 demo accounts
    python3 test_recon.py independentbank.com    # single domain
    python3 test_recon.py domain1.com domain2.com
"""

import sys
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(message)s")

from atlas.agents.recon import ReconAgent

DEMO_ACCOUNTS = [
    "independentbank.com",
    "heartlandbank.com",
    "nbkc.com",
    "pinnaclebank.com",
]


def main():
    agent = ReconAgent()
    domains = sys.argv[1:] if len(sys.argv) > 1 else DEMO_ACCOUNTS

    fs_hits = 0
    for domain in domains:
        print(f"\n{'─'*50}")
        brief = agent.run(domain)
        if brief:
            print(brief.summary())
            if brief.is_fs_target:
                fs_hits += 1
        else:
            print(f"  ❌ {domain}: no 6sense data")

    print(f"\n{'─'*50}")
    print(f"  {len(domains)} accounts scanned | {fs_hits} FS ICP matches")


if __name__ == "__main__":
    main()
