"""
ATLAS end-to-end: RECON → FORGE
Usage:
    python3 test_atlas.py                        # 4 demo accounts
    python3 test_atlas.py heartlandbank.com
    python3 test_atlas.py bank1.com bank2.com
"""

import sys
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.WARNING)  # suppress info noise

from atlas.agents.recon import ReconAgent
from atlas.agents.forge import ForgeAgent


DEMO_ACCOUNTS = [
    "independentbank.com",
    "heartlandbank.com",
    "nbkc.com",
    "pinnaclebank.com",
]


def main():
    recon = ReconAgent()
    forge = ForgeAgent()

    domains = sys.argv[1:] if len(sys.argv) > 1 else DEMO_ACCOUNTS

    icp_count = 0
    for domain in domains:
        print(f"\n{'═'*58}")

        brief = recon.run(domain)
        if not brief:
            print(f"  ❌ {domain}: no 6sense data")
            continue

        email = forge.run(brief)
        if not email:
            continue

        icp_flag = "✅ FS ICP" if brief.is_fs_target else "⚠️  not ICP"
        print(f"  {brief.name} ({domain}) | {brief.employee_count} emp | {brief.revenue_range} | {icp_flag}")
        print(f"  {brief.city}, {brief.state} | {brief.phone}")
        print()
        print(email.display())

        if brief.is_fs_target:
            icp_count += 1

    print(f"\n{'═'*58}")
    print(f"  {len(domains)} accounts | {icp_count} FS ICP | {len(domains)} emails ready")


if __name__ == "__main__":
    main()
