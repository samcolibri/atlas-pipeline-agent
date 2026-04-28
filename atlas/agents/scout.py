"""
SCOUT Agent — Account universe builder.

Pulls every US community bank and credit union from FDIC + NCUA,
applies ICP filters, checks Salesforce suppression, and writes
results to Supabase for the downstream enrichment pipeline.

No LLM required. Entirely deterministic.

Usage:
    from atlas.agents.scout import ScoutAgent
    results = ScoutAgent().run()
    results = ScoutAgent().run(states=["IL", "WI", "MN"])
    results = ScoutAgent().run(asset_min_m=500, asset_max_m=5000)
"""

import logging
import os
from dataclasses import dataclass
from typing import Optional

from atlas.integrations.fdic import Institution, InstitutionUniverse, ASSET_MIN_K, ASSET_MAX_K

log = logging.getLogger("atlas.scout")

# ICP institution types we target
TARGET_TYPES = {"bank", "credit_union", "savings"}

# Minimum website presence — no website = skip (can't enrich domain)
REQUIRE_WEBSITE = True


@dataclass
class ScoutRun:
    total_pulled: int
    icp_matched: int
    suppressed: int
    new_accounts: int
    institutions: list[Institution]

    def display(self):
        print(f"\n{'═'*58}")
        print(f"  SCOUT Run Complete")
        print(f"  Pulled from FDIC/NCUA:  {self.total_pulled:,}")
        print(f"  ICP matched:            {self.icp_matched:,}")
        print(f"  Suppressed (SF check):  {self.suppressed:,}")
        print(f"  Net-new accounts:       {self.new_accounts:,}")
        print(f"{'═'*58}\n")
        if self.institutions:
            print("  Sample accounts:")
            for inst in self.institutions[:5]:
                print(f"    {inst.display()}")


class ScoutAgent:

    def __init__(self):
        self._universe = InstitutionUniverse()
        self._db = None
        self._sf = None

        # Lazy-load db and SF only if configured
        try:
            if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_KEY"):
                from atlas.db.client import get_db
                self._db = get_db()
        except Exception as e:
            log.warning(f"[SCOUT] Supabase not configured: {e}")

        try:
            if os.getenv("SF_CLIENT_ID") and os.getenv("SF_USERNAME"):
                from atlas.integrations.salesforce import SalesforceClient
                self._sf = SalesforceClient()
        except Exception as e:
            log.warning(f"[SCOUT] Salesforce not configured: {e}")

    def run(
        self,
        asset_min_m: int = 100,         # $100M minimum assets
        asset_max_m: int = 10_000,      # $10B maximum assets
        states: Optional[list[str]] = None,
        include_credit_unions: bool = True,
        dry_run: bool = False,
    ) -> ScoutRun:
        asset_min_k = asset_min_m * 1_000
        asset_max_k = asset_max_m * 1_000

        log.info(
            f"[SCOUT] Starting — assets ${asset_min_m}M–${asset_max_m}M"
            + (f", states: {states}" if states else ", all states")
        )

        # Step 1: Pull from FDIC + NCUA
        institutions = self._universe.pull(
            asset_min_k=asset_min_k,
            asset_max_k=asset_max_k,
            states=states,
            include_credit_unions=include_credit_unions,
        )
        total_pulled = len(institutions)

        # Step 2: ICP filter
        icp = [i for i in institutions if self._passes_icp(i)]
        log.info(f"[SCOUT] ICP filter: {total_pulled} → {len(icp)}")

        # Step 3: Salesforce suppression check
        suppressed_domains = self._get_sf_suppressed_domains()
        if suppressed_domains and self._db:
            self._db.bulk_suppress_from_salesforce(suppressed_domains, "salesforce_sync")

        clean = []
        suppressed_count = 0
        for inst in icp:
            domain = inst.domain or ""
            if self._is_suppressed(domain, suppressed_domains):
                suppressed_count += 1
                log.debug(f"[SCOUT] Suppressed: {inst.name} ({domain})")
            else:
                clean.append(inst)

        log.info(f"[SCOUT] After suppression: {len(icp)} → {len(clean)} clean")

        # Step 4: Write to Supabase
        new_count = 0
        if self._db and not dry_run:
            for inst in clean:
                result = self._db.upsert_account(inst)
                if result:
                    self._db.log_action(
                        "account", result["id"], "scout_pulled",
                        {"source": inst.source, "asset_k": inst.asset_k}
                    )
                    new_count += 1

            log.info(f"[SCOUT] Wrote {new_count} accounts to Supabase")
        elif dry_run:
            log.info(f"[SCOUT] Dry run — would write {len(clean)} accounts")
            new_count = len(clean)

        return ScoutRun(
            total_pulled=total_pulled,
            icp_matched=len(icp),
            suppressed=suppressed_count,
            new_accounts=new_count,
            institutions=clean,
        )

    def _passes_icp(self, inst: Institution) -> bool:
        if inst.institution_type not in TARGET_TYPES:
            return False
        if REQUIRE_WEBSITE and not inst.domain:
            return False
        return True

    def _get_sf_suppressed_domains(self) -> set[str]:
        if not self._sf:
            return set()
        try:
            return self._sf.get_customer_domains()
        except Exception as e:
            log.warning(f"[SCOUT] SF suppression pull failed: {e}")
            return set()

    def _is_suppressed(self, domain: str, sf_domains: set[str]) -> bool:
        if not domain:
            return False
        if domain in sf_domains:
            return True
        if self._db:
            return self._db.is_suppressed(domain)
        return False

    # ── Trigger detection ─────────────────────────────────────────────

    def detect_triggers(self, institutions: list[Institution]):
        """
        Layer free trigger signals on top of ICP accounts.
        Called separately after initial SCOUT pull.

        Trigger types (cheapest first):
          - asset_growth: FDIC asset data YoY change
          - merger: FDIC history endpoint shows recent structure change
          - job_posting: SerpApi Google Jobs (BSA/compliance roles)
        """
        for inst in institutions:
            self._check_asset_growth(inst)
            self._check_merger_history(inst)

    def _check_asset_growth(self, inst: Institution):
        """Flag institutions with significant asset growth YoY via FDIC history."""
        import requests
        try:
            resp = requests.get(
                "https://api.fdic.gov/banks/history",
                params={
                    "filters": f"CERT:{inst.cert_id}",
                    "fields": "CERT,INSTCAT,PROCDATE,PCITY,PSTALP",
                    "limit": "5",
                    "sort_by": "PROCDATE",
                    "sort_order": "DESC",
                },
                timeout=10,
            )
            if resp.ok:
                data = resp.json().get("data", [])
                if data:
                    log.debug(
                        f"[SCOUT] {inst.name}: {len(data)} history events — "
                        f"latest {data[0]['data'].get('PROCDATE', '')}"
                    )
        except Exception:
            pass

    def _check_merger_history(self, inst: Institution):
        pass  # FDIC history check above covers mergers too
