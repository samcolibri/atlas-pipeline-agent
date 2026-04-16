"""
ATLAS — Autonomous Territory & Lead Acceleration System
Entry point for Railway deployment.

Runs a lightweight Flask health server + scheduled agent loop.
"""

import os
import threading
import logging
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, jsonify
import schedule
import time

load_dotenv()

# ── Logging ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("atlas")

# ── Flask health server (Railway needs this) ─────────────
app = Flask(__name__)

agent_status = {
    "status": "starting",
    "last_run": None,
    "last_run_result": None,
    "accounts_processed": 0,
    "emails_generated": 0,
    "replies_detected": 0,
    "errors": [],
}


@app.route("/health")
def health():
    return jsonify({"status": "healthy", "agent": agent_status}), 200


@app.route("/status")
def status():
    return jsonify(agent_status), 200


@app.route("/")
def index():
    return jsonify({
        "name": "ATLAS — Autonomous Territory & Lead Acceleration System",
        "version": "1.0.0",
        "status": agent_status["status"],
        "last_run": agent_status["last_run"],
        "docs": "https://github.com/samcolibri/atlas-pipeline-agent",
    }), 200


# ── Agent Core Loop ──────────────────────────────────────
def run_agent_cycle():
    """Main agent cycle — runs on schedule."""
    log.info("=" * 60)
    log.info("ATLAS DAILY CYCLE STARTING")
    log.info("=" * 60)

    agent_status["status"] = "running"
    agent_status["last_run"] = datetime.utcnow().isoformat()

    try:
        # Step 1: SCOUT — Pull intent signals
        log.info("[SCOUT] Pulling 6sense intent signals...")
        scout_results = run_scout()

        # Step 2: SENTINEL — Data quality checks
        log.info("[SENTINEL] Running data quality checks...")
        clean_accounts = run_sentinel(scout_results)

        # Step 3: RECON — Research each account
        log.info("[RECON] Generating research briefs...")
        briefs = run_recon(clean_accounts)

        # Step 4: FORGE — Generate personalized outreach
        log.info("[FORGE] Generating outreach sequences...")
        emails = run_forge(briefs)

        # Step 5: VITALS — Check pipeline health (stale leads only)
        log.info("[VITALS] Scanning for stale leads...")
        run_vitals()

        # Step 6: COMMAND — Report results
        log.info("[COMMAND] Generating daily summary...")
        run_command(emails)

        agent_status["status"] = "idle"
        agent_status["last_run_result"] = "success"
        agent_status["accounts_processed"] = len(clean_accounts) if clean_accounts else 0
        agent_status["emails_generated"] = len(emails) if emails else 0

        log.info("=" * 60)
        log.info("ATLAS DAILY CYCLE COMPLETE")
        log.info("=" * 60)

    except Exception as e:
        log.error(f"ATLAS CYCLE FAILED: {e}", exc_info=True)
        agent_status["status"] = "error"
        agent_status["last_run_result"] = f"error: {str(e)}"
        agent_status["errors"].append({
            "time": datetime.utcnow().isoformat(),
            "error": str(e),
        })
        # Keep only last 10 errors
        agent_status["errors"] = agent_status["errors"][-10:]
        send_teams_alert(f"⚠️ ATLAS agent cycle failed: {e}")


# ── Agent Modules (stubs — filled in when APIs are connected) ──

def run_scout():
    """SCOUT: Pull 6sense intent signals + Salesforce cross-reference."""
    sixsense_key = os.getenv("SIXSENSE_API_KEY")
    if not sixsense_key:
        log.warning("[SCOUT] 6sense API key not configured — skipping intent pull")
        return []

    # TODO: Implement when 6sense API key is provided
    # 1. Pull top intent accounts from 6sense
    # 2. Cross-reference against Salesforce (exclude customers, active opps)
    # 3. Return list of net new target accounts
    log.info("[SCOUT] Would pull intent signals here — awaiting API credentials")
    return []


def run_sentinel(accounts):
    """SENTINEL: Dedup, exclusion filters, data quality."""
    if not accounts:
        return []

    # TODO: Implement when Salesforce API is connected
    # 1. Check for duplicates (email + company + phone matching)
    # 2. Apply hard exclusions (current customers, active opps, unsubscribed)
    # 3. Flag soft exclusions (low confidence persona, bounced emails)
    # 4. Return clean account list
    log.info("[SENTINEL] Would run data quality checks — awaiting API credentials")
    return accounts


def run_recon(accounts):
    """RECON: Generate AI research briefs via Claude."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        log.warning("[RECON] Claude API key not configured — skipping research")
        return []

    if not accounts:
        return []

    # TODO: Implement research brief generation
    # 1. For each account, build context from 6sense + Salesforce data
    # 2. Call Claude to generate research brief (<60 seconds per account)
    # 3. Match buyer persona (compliance / HR-L&D / operations)
    # 4. Return briefs with persona classification
    log.info("[RECON] Would generate research briefs — awaiting full API setup")
    return []


def run_forge(briefs):
    """FORGE: Generate personalized outreach sequences via Claude."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        log.warning("[FORGE] Claude API key not configured — skipping outreach gen")
        return []

    if not briefs:
        return []

    mode = os.getenv("ATLAS_MODE", "review")

    # TODO: Implement email generation + Outreach enrollment
    # 1. For each brief, generate persona-matched email (2 A/B variants)
    # 2. Score quality (personalization, spam risk, tone, factual accuracy)
    # 3. If mode == "review": queue for human approval via Teams
    # 4. If mode == "auto" and confidence > threshold: auto-send via Outreach
    # 5. Log all activity to Salesforce
    log.info(f"[FORGE] Would generate outreach (mode={mode}) — awaiting full API setup")
    return []


def run_vitals():
    """VITALS: Detect stale leads (NOT stale opps — human-owned)."""
    sf_username = os.getenv("SF_USERNAME")
    if not sf_username:
        log.warning("[VITALS] Salesforce not configured — skipping pipeline health")
        return

    # TODO: Implement when Salesforce API is connected
    # 1. Query leads with no activity in 8+ days
    # 2. Alert assigned rep + manager via Teams
    # 3. Route post-sequence "No Reply" leads to nurture
    # 4. NOTE: Do NOT touch opportunities — human relationships close deals
    log.info("[VITALS] Would scan for stale leads — awaiting Salesforce API")


def run_command(emails):
    """COMMAND: Daily summary + reporting."""
    # TODO: Implement daily digest
    # 1. Compile today's actions (accounts processed, emails generated, replies)
    # 2. Send daily summary to Teams
    # 3. Weekly digest to leadership (Molly, Scott, Nathan) on Fridays
    log.info("[COMMAND] Would send daily summary — awaiting Teams webhook")


# ── Reply Monitor (runs every 30 min) ────────────────────

def check_replies():
    """Monitor Outreach for new replies. Classify and alert."""
    outreach_token = os.getenv("OUTREACH_ACCESS_TOKEN")
    if not outreach_token:
        return

    # TODO: Implement when Outreach API is connected
    # 1. Pull new replies from Outreach API
    # 2. Classify via Claude (positive / objection / neutral / unsubscribe / OOO)
    # 3. If positive: alert rep immediately via Teams
    # 4. Update Salesforce lead status
    # 5. Pause sequence (don't send next step if they already replied)
    # 6. Log to learning engine


# ── Teams Alerts ─────────────────────────────────────────

def send_teams_alert(message):
    """Send an alert to Microsoft Teams channel."""
    import requests
    webhook_url = os.getenv("TEAMS_WEBHOOK_URL")
    if not webhook_url:
        log.warning(f"[TEAMS] No webhook configured. Alert: {message}")
        return

    try:
        requests.post(webhook_url, json={
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "summary": "ATLAS Alert",
            "sections": [{
                "activityTitle": "ATLAS Pipeline Agent",
                "text": message,
            }],
        }, timeout=10)
    except Exception as e:
        log.error(f"[TEAMS] Failed to send alert: {e}")


# ── Scheduler ────────────────────────────────────────────

def run_scheduler():
    """Background scheduler for agent cycles."""
    # Daily agent run at 6:00 AM ET (11:00 UTC)
    schedule.every().day.at("11:00").do(run_agent_cycle)

    # Check for replies every 30 minutes
    schedule.every(30).minutes.do(check_replies)

    log.info("Scheduler started. Daily run at 11:00 UTC (6:00 AM ET). Reply check every 30 min.")

    # Run once on startup (useful for testing)
    if os.getenv("ATLAS_RUN_ON_START", "false").lower() == "true":
        log.info("ATLAS_RUN_ON_START=true — running initial cycle...")
        run_agent_cycle()

    while True:
        schedule.run_pending()
        time.sleep(60)


# ── Main ─────────────────────────────────────────────────

def main():
    log.info("=" * 60)
    log.info("ATLAS — Autonomous Territory & Lead Acceleration System")
    log.info("=" * 60)

    # Check which APIs are configured
    apis = {
        "Salesforce": bool(os.getenv("SF_CLIENT_ID")),
        "Outreach": bool(os.getenv("OUTREACH_ACCESS_TOKEN")),
        "6sense": bool(os.getenv("SIXSENSE_API_KEY")),
        "Claude": bool(os.getenv("ANTHROPIC_API_KEY")),
        "Teams": bool(os.getenv("TEAMS_WEBHOOK_URL")),
    }

    for name, configured in apis.items():
        status = "✅ configured" if configured else "⬚  awaiting credentials"
        log.info(f"  {name}: {status}")

    configured_count = sum(apis.values())
    log.info(f"\n  {configured_count}/5 APIs configured")

    if configured_count == 0:
        log.warning("No APIs configured. Agent will start but skip all operations.")
        log.warning("Set environment variables and restart to activate.")

    agent_status["status"] = "idle"

    # Start scheduler in background thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

    # Start Flask health server (Railway needs this)
    port = int(os.getenv("PORT", 8080))
    log.info(f"Health server starting on port {port}")
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
