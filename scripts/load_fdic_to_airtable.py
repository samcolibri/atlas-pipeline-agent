"""
Load FDIC + NCUA institutions into Airtable Accounts table.

This populates ATLAS's data memory with the full ICP account universe
so agents can query context BEFORE calling any LLM.

Usage:
    python3 scripts/load_fdic_to_airtable.py                   # FDIC only, dry-run peek
    python3 scripts/load_fdic_to_airtable.py --write           # Write to Airtable
    python3 scripts/load_fdic_to_airtable.py --write --ncua    # Include credit unions
    python3 scripts/load_fdic_to_airtable.py --states IL WI    # Filter by state
    python3 scripts/load_fdic_to_airtable.py --peek            # Show table schema
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Load .env before any other imports (explicit path avoids heredoc stack issues)
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger("load_fdic")

# Pull from env (or use hardcoded defaults for this base)
AIRTABLE_TOKEN = os.getenv("AIRTABLE_TOKEN")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID", "appwlGCHBaRef70gO")
ACCOUNTS_TABLE = os.getenv("AIRTABLE_ACCOUNTS_TABLE", "Accounts")


def institution_to_airtable(inst) -> dict:
    """Map Institution dataclass → Airtable Accounts field names."""
    record = {
        "Name":             inst.name,
        "City":             inst.city,
        "State":            inst.state,
        "Zip":              inst.zip_code or "",
        "Address":          inst.address or "",
        "Asset_M":          inst.asset_usd_m,
        "Domain":           inst.domain or "",
        "Phone":            inst.phone or "",
        "Established":      inst.established or "",
        "Institution_Type": inst.institution_type,
        "Source":           inst.source,
        "Cert_ID":          inst.cert_id,
        "Employee_Estimate": inst.employee_estimate,
        "Pipeline_Status":  "new",
        "Suppressed":       False,
        "Has_Trigger":      False,
    }
    # Only include non-empty strings to avoid API type errors on phoneNumber fields
    if not record["Phone"]:
        del record["Phone"]
    return record


def main():
    parser = argparse.ArgumentParser(description="Load FDIC banks into Airtable")
    parser.add_argument("--write",  action="store_true", help="Actually write to Airtable")
    parser.add_argument("--ncua",   action="store_true", help="Also pull NCUA credit unions")
    parser.add_argument("--peek",   action="store_true", help="Show Airtable table schema")
    parser.add_argument("--states", nargs="+",           help="Filter by state codes")
    parser.add_argument("--min",    type=int, default=100,    help="Min assets $M")
    parser.add_argument("--max",    type=int, default=10_000, help="Max assets $M")
    parser.add_argument("--limit",  type=int, default=0,      help="Cap records (0=all)")
    args = parser.parse_args()

    sys.path.insert(0, str(Path(__file__).parent.parent))

    from atlas.integrations.airtable_client import AirtableClient
    from atlas.integrations.fdic import FDICClient, NCUAClient, ASSET_MIN_K, ASSET_MAX_K

    at = AirtableClient(token=AIRTABLE_TOKEN, base_id=AIRTABLE_BASE_ID)

    # ── Schema peek ────────────────────────────────────────────────────
    if args.peek:
        print(f"\n── Airtable Accounts Schema ──────────────────────────")
        fields = at.table_fields(ACCOUNTS_TABLE)
        if fields:
            for f in fields:
                print(f"  {f}")
        else:
            print("  (no records yet — table appears empty)")
        print()
        return

    asset_min_k = args.min * 1_000
    asset_max_k = args.max * 1_000

    # ── Pull FDIC ──────────────────────────────────────────────────────
    print(f"\n── Pulling FDIC banks ────────────────────────────────")
    fdic = FDICClient()
    institutions = fdic.get_institutions(
        asset_min_k=asset_min_k,
        asset_max_k=asset_max_k,
        states=args.states,
    )
    print(f"  FDIC banks: {len(institutions):,}")

    # ── Pull NCUA (optional) ───────────────────────────────────────────
    if args.ncua:
        print(f"\n── Pulling NCUA credit unions ───────────────────────")
        ncua = NCUAClient()
        cus = ncua.get_institutions(asset_min_k=asset_min_k, asset_max_k=asset_max_k)
        print(f"  NCUA credit unions: {len(cus):,}")
        institutions.extend(cus)

    # Filter to ICP only (must have website)
    icp = [i for i in institutions if i.domain]
    no_site = len(institutions) - len(icp)
    print(f"\n  Total: {len(institutions):,}")
    print(f"  Has website (ICP): {len(icp):,}")
    print(f"  No website (skip): {no_site:,}")

    # Cap if requested
    if args.limit:
        icp = icp[: args.limit]
        print(f"  Capped to: {len(icp):,}")

    # Show sample
    print(f"\n  Sample (first 5):")
    for inst in icp[:5]:
        print(f"    {inst.display()}")

    if not args.write:
        print(f"\n  (Dry run — use --write to load into Airtable)")
        print(f"  Would insert: {len(icp):,} records")
        print(f"  Estimated time: ~{len(icp) * 0.25 / 10 / 60:.1f} minutes\n")
        return

    # ── Write to Airtable ──────────────────────────────────────────────
    print(f"\n── Writing {len(icp):,} records to Airtable ─────────────")
    records = [institution_to_airtable(i) for i in icp]

    # Use upsert on [Cert_ID, Source] to handle re-runs cleanly
    result = at.upsert(
        table=ACCOUNTS_TABLE,
        records=records,
        match_fields=["Cert_ID", "Source"],
        show_progress=True,
    )

    print(f"\n  Created: {result['created']:,}")
    print(f"  Updated: {result['updated']:,}")
    print(f"  Total:   {result['created'] + result['updated']:,}\n")


if __name__ == "__main__":
    main()
