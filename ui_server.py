#!/usr/bin/env python3
"""
ATLAS Command Center — email review UI on :5001
Run: python3 ui_server.py
"""

import csv
import io
import json
import logging
import os
import queue
import sys
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request, stream_with_context

PROJECT_DIR = Path(__file__).parent
ENV_FILE = PROJECT_DIR / ".env"
load_dotenv(ENV_FILE)
sys.path.insert(0, str(PROJECT_DIR))

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

# ── State ─────────────────────────────────────────────────────────────────────

QUEUE_FILE = PROJECT_DIR / "email_queue.json"

_email_queue: list[dict] = []          # [{id, draft, status, account, created_at}]
_email_lock  = threading.Lock()
_log_q: queue.Queue = queue.Queue(maxsize=2000)
_gen_thread: Optional[threading.Thread] = None
_cycle_thread: Optional[threading.Thread] = None


def _load_queue():
    """Load persisted email queue from disk on startup."""
    global _email_queue
    if QUEUE_FILE.exists():
        try:
            data = json.loads(QUEUE_FILE.read_text())
            _email_queue = data if isinstance(data, list) else []
            return len(_email_queue)
        except Exception:
            _email_queue = []
    return 0


def _save_queue():
    """Persist the email queue to disk after every mutation."""
    try:
        QUEUE_FILE.write_text(json.dumps(_email_queue, indent=2))
    except Exception as exc:
        _log("warning", f"Queue save failed: {exc}")

_agent_state = {
    "status":       "idle",
    "mode":         os.getenv("ATLAS_MODE", "shadow"),
    "daily_limit":  int(os.getenv("ATLAS_DAILY_LIMIT", "25")),
    "last_run":     None,
    "last_result":  None,
    "errors":       [],
    "current_step": None,
}


# ── Logging ───────────────────────────────────────────────────────────────────

def _log(level: str, msg: str):
    entry = {"time": datetime.utcnow().strftime("%H:%M:%S"), "level": level, "message": msg}
    try:
        _log_q.put_nowait(entry)
    except queue.Full:
        try: _log_q.get_nowait()
        except queue.Empty: pass
        _log_q.put_nowait(entry)


class _UIHandler(logging.Handler):
    _MAP = {"DEBUG": "debug", "INFO": "info", "WARNING": "warning", "ERROR": "error"}
    def emit(self, record):
        _log(self._MAP.get(record.levelname, "info"), self.format(record))

_h = _UIHandler()
_h.setFormatter(logging.Formatter("%(name)s: %(message)s"))
for logger_name in ("atlas", "atlas.ui", "atlas.forge", "atlas.recon", "atlas.scout",
                     "atlas.sentinel", "atlas.cortex", "atlas.airtable"):
    logging.getLogger(logger_name).addHandler(_h)
    logging.getLogger(logger_name).setLevel(logging.DEBUG)

log = logging.getLogger("atlas.ui")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _integration_status() -> dict:
    load_dotenv(ENV_FILE, override=True)
    return {
        "airtable":   bool(os.getenv("AIRTABLE_TOKEN") and os.getenv("AIRTABLE_BASE_ID")),
        "claude":     bool(os.getenv("ANTHROPIC_API_KEY")),
        "salesforce": bool(os.getenv("SF_CLIENT_ID") and os.getenv("SF_USERNAME")),
        "outreach":   bool(os.getenv("OUTREACH_ACCESS_TOKEN")),
        "sixsense":   bool(os.getenv("SIXSENSE_API_KEY")),
        "teams":      bool(os.getenv("TEAMS_WEBHOOK_URL")),
        "instantly":  bool(os.getenv("INSTANTLY_API_KEY")),
        "supabase":   bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_KEY")),
        "zerobounce": bool(os.getenv("ZEROBOUNCE_API_KEY")),
    }


def _patch_env(key: str, value: str):
    lines, found = [], False
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            if line.startswith(f"{key}="):
                lines.append(f"{key}={value}")
                found = True
            else:
                lines.append(line)
    if not found:
        lines.append(f"{key}={value}")
    ENV_FILE.write_text("\n".join(lines) + "\n")
    os.environ[key] = str(value)


# ── Email generation from Airtable ────────────────────────────────────────────

def _pick_angle(inst_type: str, asset_m: int) -> str:
    inst_type = (inst_type or "bank").lower()
    if inst_type == "credit_union":
        return "credit_union_community_mission"
    if inst_type == "savings":
        return "savings_institution_compliance"
    if asset_m >= 5000:
        return "enterprise_bank_scale"
    if asset_m >= 1000:
        return "mid_market_bank_grc"
    if asset_m < 500:
        return "community_bank_relationship"
    return "general_fs_compliance"


def _build_brief_from_account(account: dict):
    """Build a ReconBrief from Airtable account fields (no 6sense required)."""
    from atlas.agents.recon import ReconBrief

    name      = account.get("Name", "").strip()
    domain    = account.get("Domain", "").strip()
    city      = account.get("City", "")
    state     = account.get("State", "")
    asset_m   = int(account.get("Asset_M", 0))
    inst_type = account.get("Institution_Type", "bank")
    emp       = account.get("Employee_Estimate", f"{asset_m // 5 or '?'}-employees")

    if not name or not domain:
        return None

    sic_map = {"bank": "6021", "credit_union": "6061", "savings": "6035"}
    sic_desc = {
        "6021": "National commercial banks",
        "6061": "Federal credit unions",
        "6035": "Savings institutions — federally chartered",
    }
    sic = sic_map.get(inst_type, "6021")

    return ReconBrief(
        domain=domain,
        name=name,
        industry="Financial Services",
        employee_count=emp,
        revenue_range=f"${asset_m:,}M assets",
        annual_revenue_usd=str(asset_m * 1_000_000),
        city=city,
        state=state,
        phone=account.get("Phone", ""),
        sic_code=sic,
        sic_description=sic_desc.get(sic, "Commercial bank"),
        naics_description="Finance and Insurance",
        is_fs_target=True,
        pitch_angle=_pick_angle(inst_type, asset_m),
        raw=None,
    )


def _generate_emails_thread(limit: int, state_filter: Optional[str]):
    global _gen_thread
    _log("info", f"{'─'*50}")
    _log("info", f"Generating emails — limit={limit}" + (f", state={state_filter}" if state_filter else ""))

    try:
        token   = os.getenv("AIRTABLE_TOKEN")
        base_id = os.getenv("AIRTABLE_BASE_ID", "appwlGCHBaRef70gO")

        if not token:
            _log("error", "AIRTABLE_TOKEN not set — cannot pull accounts")
            return

        from atlas.integrations.airtable_client import AirtableClient
        from atlas.agents.forge import ForgeAgent

        at = AirtableClient(token=token, base_id=base_id)
        forge = ForgeAgent()

        _log("info", "Pulling accounts from Airtable…")
        table = os.getenv("AIRTABLE_ACCOUNTS_TABLE", "Accounts")

        # Pull filtered or all
        if state_filter:
            records = at.search(table, State=state_filter)
        else:
            records = at.all(table)

        accounts = [r.get("fields", {}) for r in records]
        # Filter: needs domain, not suppressed
        accounts = [a for a in accounts if a.get("Domain") and not a.get("Suppressed")]
        _log("info", f"Found {len(accounts):,} eligible accounts")

        if not accounts:
            _log("warning", "No eligible accounts found — check Airtable or filters")
            return

        # Skip already-queued domains
        with _email_lock:
            queued_domains = {e["draft"]["domain"] for e in _email_queue}

        fresh = [a for a in accounts if a.get("Domain") not in queued_domains]
        _log("info", f"{len(fresh):,} new (not yet queued)")

        # Sort by Asset_M desc (bigger banks first)
        fresh.sort(key=lambda a: int(a.get("Asset_M", 0)), reverse=True)
        batch = fresh[:limit]

        generated = 0
        for account in batch:
            brief = _build_brief_from_account(account)
            if not brief:
                continue
            draft = forge.run(brief)
            if not draft:
                continue

            entry = {
                "id":         str(uuid.uuid4()),
                "draft":      draft.to_dict(),
                "status":     "pending",
                "account":    {
                    "Asset_M":          int(account.get("Asset_M", 0)),
                    "Institution_Type": account.get("Institution_Type", "bank"),
                    "State":            account.get("State", ""),
                    "City":             account.get("City", ""),
                    "Employee_Estimate": account.get("Employee_Estimate", ""),
                    "Cert_ID":          account.get("Cert_ID", ""),
                },
                "created_at": datetime.utcnow().isoformat(),
            }
            with _email_lock:
                _email_queue.append(entry)
            generated += 1
            _log("info", f"  ✓ {draft.company_name} ({draft.pitch_angle})")

        _save_queue()
        _log("info", f"{'─'*50}")
        _log("info", f"Done — {generated} emails ready for review")

    except Exception as exc:
        import traceback
        _log("error", f"Generation failed: {exc}")
        for line in traceback.format_exc().splitlines():
            _log("debug", line)
    finally:
        _gen_thread = None


# ── FDIC live generation ──────────────────────────────────────────────────────

FDIC_API = "https://api.fdic.gov/banks/institutions"


def _clean_domain(webaddr: str) -> Optional[str]:
    if not webaddr:
        return None
    w = webaddr.lower().strip().rstrip("/")
    for prefix in ("https://", "http://", "www."):
        if w.startswith(prefix):
            w = w[len(prefix):]
    domain = w.split("/")[0].strip()
    return domain if domain and "." in domain else None


def _emp_from_assets(asset_m: int) -> str:
    if asset_m < 200:   return "50–200"
    if asset_m < 500:   return "100–400"
    if asset_m < 1000:  return "200–700"
    if asset_m < 2000:  return "400–1,200"
    if asset_m < 5000:  return "800–2,500"
    return "1,500–5,000"


def _build_brief_from_fdic_record(inst: dict):
    from atlas.agents.recon import ReconBrief
    name    = inst["name"]
    domain  = inst["domain"]
    city    = inst.get("city", "")
    state   = inst.get("state", "")
    asset_m = inst["asset_m"]
    emp     = _emp_from_assets(asset_m)
    angle   = _pick_angle(inst.get("inst_type", "bank"), asset_m)
    sic     = "6021"
    return ReconBrief(
        domain=domain, name=name, industry="Financial Services",
        employee_count=emp, revenue_range=f"${asset_m:,}M assets",
        annual_revenue_usd=str(asset_m * 1_000_000),
        city=city, state=state, phone=inst.get("phone", ""),
        sic_code=sic, sic_description="National commercial banks",
        naics_description="Finance and Insurance",
        is_fs_target=True, pitch_angle=angle, raw=None,
    )


def _generate_from_fdic_thread(limit: int, state_filter: Optional[str],
                                asset_min_m: int, asset_max_m: int):
    global _gen_thread
    asset_min_k = asset_min_m * 1_000
    asset_max_k = asset_max_m * 1_000

    _log("info", "─" * 52)
    _log("info", f"FDIC LIVE  limit={limit}  assets=${asset_min_m}M–${asset_max_m}M"
         + (f"  state={state_filter}" if state_filter else ""))

    try:
        import requests as _req

        fdic_filter = f"ACTIVE:1 AND ASSET:[{asset_min_k} TO {asset_max_k}]"
        if state_filter:
            fdic_filter += f" AND STALP:{state_filter}"

        params = {
            "filters":    fdic_filter,
            "fields":     "NAME,CITY,STALP,ASSET,CERT,WEBADDR",
            "limit":      10000,
            "sort_by":    "ASSET",
            "sort_order": "DESC",
        }

        _log("info", "Fetching from api.fdic.gov…")
        resp = _req.get(FDIC_API, params=params, timeout=30)
        resp.raise_for_status()
        raw = resp.json()

        total_fdic = raw.get("meta", {}).get("total", 0)
        _log("info", f"FDIC returned {total_fdic:,} banks in ICP range")

        institutions = []
        for item in raw.get("data", []):
            d      = item.get("data", {})
            domain = _clean_domain(d.get("WEBADDR", ""))
            if not domain:
                continue
            asset_k = int(d.get("ASSET", 0))
            institutions.append({
                "name":     d.get("NAME", "").strip(),
                "city":     d.get("CITY", "").strip(),
                "state":    d.get("STALP", "").strip(),
                "asset_m":  asset_k // 1_000,
                "domain":   domain,
                "cert_id":  str(d.get("CERT", "")),
                "inst_type": "bank",
            })

        _log("info", f"{len(institutions):,} have websites — ready to generate")

        with _email_lock:
            queued_domains = {e["draft"]["domain"] for e in _email_queue}

        fresh = [i for i in institutions if i["domain"] not in queued_domains]
        _log("info", f"{len(fresh):,} not yet queued")

        batch = fresh[:limit]

        from atlas.agents.forge import ForgeAgent
        forge = ForgeAgent()

        generated = 0
        for inst in batch:
            brief = _build_brief_from_fdic_record(inst)
            if not brief:
                continue
            draft = forge.run(brief)
            if not draft:
                continue

            entry = {
                "id":         str(uuid.uuid4()),
                "draft":      draft.to_dict(),
                "status":     "pending",
                "account": {
                    "Asset_M":           inst["asset_m"],
                    "Institution_Type":  inst["inst_type"],
                    "State":             inst["state"],
                    "City":              inst["city"],
                    "Employee_Estimate": _emp_from_assets(inst["asset_m"]),
                    "Cert_ID":           inst["cert_id"],
                },
                "created_at": datetime.utcnow().isoformat(),
                "source":     "fdic_live",
            }
            with _email_lock:
                _email_queue.append(entry)
            generated += 1
            _log("info", f"  ✓ {draft.company_name} ({inst['state']}, ${inst['asset_m']:,}M)")

        _save_queue()
        _log("info", "─" * 52)
        _log("info", f"Done — {generated} emails ready for review")

    except Exception as exc:
        import traceback
        _log("error", f"FDIC generation failed: {exc}")
        for line in traceback.format_exc().splitlines():
            _log("debug", line)
    finally:
        _gen_thread = None


# ── Routes — API ──────────────────────────────────────────────────────────────

@app.route("/api/status")
def api_status():
    with _email_lock:
        counts = {
            "total":    len(_email_queue),
            "pending":  sum(1 for e in _email_queue if e["status"] == "pending"),
            "approved": sum(1 for e in _email_queue if e["status"] == "approved"),
            "skipped":  sum(1 for e in _email_queue if e["status"] == "skipped"),
        }
    return jsonify({
        **_agent_state,
        "generating": _gen_thread is not None and _gen_thread.is_alive(),
        "integrations": _integration_status(),
        "queue": counts,
    })


@app.route("/api/emails")
def api_emails():
    status_filter = request.args.get("status", "all")
    state_filter  = request.args.get("state")
    angle_filter  = request.args.get("angle")
    limit         = int(request.args.get("limit", 200))

    with _email_lock:
        result = list(_email_queue)

    if status_filter != "all":
        result = [e for e in result if e["status"] == status_filter]
    if state_filter:
        result = [e for e in result if e["account"].get("State") == state_filter]
    if angle_filter:
        result = [e for e in result if e["draft"].get("pitch_angle") == angle_filter]

    return jsonify(result[:limit])


@app.route("/api/emails/generate", methods=["POST"])
def api_generate():
    global _gen_thread
    if _gen_thread and _gen_thread.is_alive():
        return jsonify({"error": "Generation already running"}), 409

    data         = request.get_json(silent=True) or {}
    source       = data.get("source", "airtable")   # "airtable" | "fdic"
    limit        = min(int(data.get("limit", 25)), 500)
    state_filter = data.get("state") or None
    asset_min_m  = int(data.get("asset_min_m", 100))
    asset_max_m  = int(data.get("asset_max_m", 10000))

    if source == "fdic":
        _gen_thread = threading.Thread(
            target=_generate_from_fdic_thread,
            args=(limit, state_filter, asset_min_m, asset_max_m),
            daemon=True,
        )
    else:
        _gen_thread = threading.Thread(
            target=_generate_emails_thread,
            args=(limit, state_filter),
            daemon=True,
        )

    _gen_thread.start()
    return jsonify({"started": True, "source": source, "limit": limit})


@app.route("/api/emails/<email_id>/status", methods=["POST"])
def api_email_status(email_id):
    data   = request.get_json(silent=True) or {}
    status = data.get("status")
    if status not in ("pending", "approved", "skipped"):
        return jsonify({"error": "Invalid status"}), 400

    with _email_lock:
        for entry in _email_queue:
            if entry["id"] == email_id:
                entry["status"] = status
                _log("info", f"Email {entry['draft']['company_name']} → {status}")
                _save_queue()
                return jsonify({"ok": True, "status": status})

    return jsonify({"error": "Email not found"}), 404


@app.route("/api/emails/<email_id>/edit", methods=["POST"])
def api_email_edit(email_id):
    data = request.get_json(silent=True) or {}
    with _email_lock:
        for entry in _email_queue:
            if entry["id"] == email_id:
                if "subject" in data:
                    entry["draft"]["subject"] = data["subject"]
                if "body" in data:
                    entry["draft"]["body"] = data["body"]
                entry["edited"] = True
                _save_queue()
                return jsonify({"ok": True})
    return jsonify({"error": "Email not found"}), 404


@app.route("/api/emails/clear", methods=["POST"])
def api_emails_clear():
    data = request.get_json(silent=True) or {}
    target = data.get("status", "skipped")
    with _email_lock:
        before = len(_email_queue)
        _email_queue[:] = [e for e in _email_queue if e["status"] != target]
        after = len(_email_queue)
    _save_queue()
    _log("info", f"Cleared {before - after} {target} emails")
    return jsonify({"cleared": before - after})


@app.route("/api/emails/export.csv")
def api_export_csv():
    with _email_lock:
        approved = [e for e in _email_queue if e["status"] == "approved"]

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Company", "Domain", "State", "Asset_M", "Institution_Type",
                "Employee_Estimate", "Subject", "Body", "Pitch_Angle", "Case_Study",
                "Target_Titles"])
    for e in approved:
        d = e["draft"]
        a = e["account"]
        w.writerow([
            d.get("company_name", ""),
            d.get("domain", ""),
            a.get("State", ""),
            a.get("Asset_M", ""),
            a.get("Institution_Type", ""),
            a.get("Employee_Estimate", ""),
            d.get("subject", ""),
            d.get("body", "").replace("\n", "\\n"),
            d.get("pitch_angle", ""),
            d.get("case_study_used", ""),
            ", ".join(d.get("target_titles", [])),
        ])

    buf.seek(0)
    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=atlas_approved_emails.csv"},
    )


@app.route("/api/mode", methods=["POST"])
def api_mode():
    data = request.get_json(silent=True) or {}
    m = data.get("mode")
    if m not in ("shadow", "review", "auto", "paused"):
        return jsonify({"error": "Invalid mode"}), 400
    _agent_state["mode"] = m
    _patch_env("ATLAS_MODE", m)
    _log("info", f"Mode → {m}")
    return jsonify({"mode": m})


@app.route("/api/stream")
def api_stream():
    def gen():
        yield "data: {}\n\n"
        while True:
            try:
                entry = _log_q.get(timeout=25)
                yield f"data: {json.dumps(entry)}\n\n"
            except queue.Empty:
                yield ": keepalive\n\n"
    return Response(
        stream_with_context(gen()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── Dashboard HTML ────────────────────────────────────────────────────────────

@app.route("/")
def dashboard():
    return DASHBOARD_HTML


DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ATLAS — Email Review</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#080c14;--surf:#0d1117;--surf2:#161b22;--surf3:#1c2333;
  --bdr:#21262d;--text:#c9d1d9;--muted:#6e7681;--head:#e6edf3;
  --green:#00e676;--gdim:#00e67618;--gdark:#1a3d2b;
  --orange:#ffa040;--odim:#ffa04018;
  --red:#ff4566;--rdim:#ff456618;
  --blue:#58a6ff;--bdim:#58a6ff18;
  --purple:#c084fc;--pdim:#c084fc18;
}
body{font-family:'SF Mono','Fira Code',ui-monospace,monospace;
  background:var(--bg);color:var(--text);font-size:13px;min-height:100vh}

/* ── Header ── */
.hdr{background:var(--surf);border-bottom:1px solid var(--bdr);padding:12px 20px;
  display:flex;align-items:center;justify-content:space-between;
  position:sticky;top:0;z-index:200}
.hdr-l{display:flex;align-items:center;gap:12px}
.pill{background:var(--green);color:#050a0e;font-size:10px;font-weight:800;
  padding:3px 9px;border-radius:3px;letter-spacing:2px}
.hdr h1{font-size:15px;color:var(--head);font-weight:600;letter-spacing:.3px}
.hdr-r{display:flex;align-items:center;gap:10px}

/* ── Tabs ── */
.tabs{display:flex;background:var(--surf);border-bottom:1px solid var(--bdr);padding:0 20px}
.tab{padding:10px 16px;font-size:12px;font-weight:600;color:var(--muted);
  cursor:pointer;border-bottom:2px solid transparent;transition:all .15s;
  letter-spacing:.5px;text-transform:uppercase}
.tab:hover{color:var(--text)}
.tab.active{color:var(--green);border-bottom-color:var(--green)}

/* ── Panel ── */
.panel{display:none;padding:16px 20px;max-width:1400px;margin:0 auto}
.panel.active{display:block}

/* ── Topbar ── */
.topbar{display:flex;align-items:center;gap:10px;margin-bottom:14px;flex-wrap:wrap}
.stat-chip{background:var(--surf2);border:1px solid var(--bdr);border-radius:6px;
  padding:8px 14px;font-size:12px;display:flex;align-items:center;gap:7px}
.stat-chip .val{font-size:18px;font-weight:700;color:var(--head);line-height:1}
.stat-chip.g .val{color:var(--green)}
.stat-chip.o .val{color:var(--orange)}
.spacer{flex:1}
.btn{display:inline-flex;align-items:center;gap:6px;padding:8px 16px;border-radius:6px;
  font-family:inherit;font-size:12px;font-weight:700;cursor:pointer;border:none;
  transition:all .15s;letter-spacing:.4px;white-space:nowrap}
.btn:disabled{opacity:.4;cursor:not-allowed}
.btn-gen{background:var(--green);color:#050a0e}
.btn-gen:hover:not(:disabled){background:#00c853}
.btn-exp{background:var(--surf2);color:var(--blue);border:1px solid var(--blue)}
.btn-exp:hover:not(:disabled){background:var(--bdim)}
.btn-ghost{background:var(--surf2);color:var(--muted);border:1px solid var(--bdr)}
.btn-ghost:hover{color:var(--text);background:var(--surf3)}
.btn-danger{background:var(--surf2);color:var(--red);border:1px solid var(--red)}
.btn-danger:hover:not(:disabled){background:var(--rdim)}

/* ── Filter bar ── */
.filters{display:flex;align-items:center;gap:8px;margin-bottom:14px;flex-wrap:wrap}
select.flt{background:var(--surf2);color:var(--text);border:1px solid var(--bdr);
  padding:7px 11px;border-radius:5px;font-family:inherit;font-size:12px;cursor:pointer}
select.flt:focus{outline:1px solid var(--green)}
.flt-label{font-size:11px;color:var(--muted)}
.gen-opts{display:flex;align-items:center;gap:6px;margin-left:auto}
.gen-n{background:var(--surf2);color:var(--text);border:1px solid var(--bdr);
  padding:7px 10px;border-radius:5px;font-family:inherit;font-size:12px;width:70px}
.gen-n:focus{outline:1px solid var(--green)}

/* ── Email cards ── */
.email-list{display:flex;flex-direction:column;gap:10px}
.card{background:var(--surf);border:1px solid var(--bdr);border-radius:8px;overflow:hidden;
  transition:border-color .15s}
.card:hover{border-color:#30363d}
.card.approved{border-left:3px solid var(--green)}
.card.skipped{opacity:.55}

.card-head{padding:14px 16px 10px;display:flex;align-items:flex-start;gap:12px;cursor:pointer}
.card-co{display:flex;flex-direction:column;gap:3px;flex:1;min-width:0}
.co-name{font-size:14px;font-weight:700;color:var(--head);white-space:nowrap;
  overflow:hidden;text-overflow:ellipsis}
.co-meta{display:flex;align-items:center;gap:6px;flex-wrap:wrap}
.badge{font-size:10px;padding:2px 7px;border-radius:3px;font-weight:700;letter-spacing:.5px;
  white-space:nowrap}
.badge-loc{background:var(--surf3);color:var(--muted)}
.badge-bank{background:var(--bdim);color:var(--blue)}
.badge-cu{background:var(--pdim);color:var(--purple)}
.badge-sav{background:var(--odim);color:var(--orange)}
.badge-angle{background:var(--surf3);color:var(--muted);font-size:9px;letter-spacing:.3px}
.badge-assets{background:var(--gdim);color:var(--green)}
.card-status{display:flex;align-items:center;gap:5px;flex-shrink:0}
.status-dot{width:7px;height:7px;border-radius:50%;background:var(--bdr)}
.status-dot.approved{background:var(--green)}
.status-dot.skipped{background:var(--red)}
.status-dot.pending{background:var(--orange)}

.card-body{padding:0 16px 14px;border-top:1px solid var(--bdr)}
.subject-row{padding:10px 0 8px;display:flex;align-items:flex-start;gap:8px}
.subject-lbl{font-size:10px;color:var(--muted);letter-spacing:1px;text-transform:uppercase;
  white-space:nowrap;padding-top:1px}
.subject-val{color:var(--head);font-size:13px;font-weight:600;line-height:1.4;
  flex:1;min-width:0}
.subject-val[contenteditable="true"]{
  outline:1px solid var(--green);border-radius:3px;padding:2px 6px}

.email-body{background:var(--surf2);border-radius:6px;padding:14px;
  font-size:12px;line-height:1.9;color:var(--text);white-space:pre-wrap;
  max-height:220px;overflow:hidden;position:relative;transition:max-height .3s}
.email-body.expanded{max-height:2000px}
.email-body[contenteditable="true"]{
  outline:1px solid var(--green);max-height:600px;overflow-y:auto}
.body-fade{position:absolute;bottom:0;left:0;right:0;height:60px;
  background:linear-gradient(transparent,var(--surf2));pointer-events:none;
  transition:opacity .2s}
.body-fade.hidden{opacity:0}

.show-more{font-size:11px;color:var(--green);cursor:pointer;margin-top:6px;
  display:inline-block}
.show-more:hover{text-decoration:underline}

.targets-row{padding:8px 0;font-size:11px;color:var(--muted);display:flex;
  align-items:center;gap:6px;flex-wrap:wrap}
.target-pill{background:var(--surf3);padding:2px 8px;border-radius:3px;
  color:var(--text);font-size:10px}

.actions{display:flex;align-items:center;gap:7px;padding-top:8px;flex-wrap:wrap}
.btn-approve{background:var(--gdim);color:var(--green);border:1px solid var(--green);
  padding:6px 14px;border-radius:5px;font-family:inherit;font-size:11px;
  font-weight:700;cursor:pointer;letter-spacing:.5px;transition:all .15s}
.btn-approve:hover{background:var(--green);color:#050a0e}
.btn-skip{background:var(--rdim);color:var(--red);border:1px solid var(--red);
  padding:6px 14px;border-radius:5px;font-family:inherit;font-size:11px;
  font-weight:700;cursor:pointer;letter-spacing:.5px;transition:all .15s}
.btn-skip:hover{background:var(--red);color:#fff}
.btn-sm{background:var(--surf3);color:var(--muted);border:1px solid var(--bdr);
  padding:6px 12px;border-radius:5px;font-family:inherit;font-size:11px;
  cursor:pointer;transition:all .15s}
.btn-sm:hover{color:var(--text);border-color:#30363d}
.btn-sm.editing{color:var(--green);border-color:var(--green)}

/* ── Empty state ── */
.empty{text-align:center;padding:60px 20px;color:var(--muted)}
.empty-icon{font-size:40px;margin-bottom:14px}
.empty h2{font-size:16px;color:var(--text);margin-bottom:8px}
.empty p{font-size:13px;line-height:1.6;max-width:400px;margin:0 auto 20px}

/* ── Pipeline panel ── */
.grid2{display:grid;grid-template-columns:280px 1fr;gap:14px}
@media(max-width:800px){.grid2{grid-template-columns:1fr}}
.int-list{display:flex;flex-direction:column;gap:6px}
.int-row{display:flex;align-items:center;justify-content:space-between;
  padding:7px 11px;background:var(--surf2);border-radius:5px;border:1px solid var(--bdr)}
.ibadge{font-size:10px;font-weight:800;padding:2px 7px;border-radius:3px;letter-spacing:1px}
.ibadge-ok{background:var(--gdim);color:var(--green)}
.ibadge-miss{background:var(--rdim);color:var(--red)}
.ctrl-card{background:var(--surf);border:1px solid var(--bdr);border-radius:8px;padding:16px}
.ctrl-title{font-size:10px;color:var(--muted);letter-spacing:2px;text-transform:uppercase;
  margin-bottom:14px;display:flex;align-items:center;gap:7px}
.ctrl-title::before{content:'';display:inline-block;width:3px;height:11px;
  background:var(--green);border-radius:2px}
.ctrl-row{display:flex;align-items:center;gap:10px;margin-bottom:10px;flex-wrap:wrap}
select.ctrl-sel,input.ctrl-num{background:var(--surf2);color:var(--text);
  border:1px solid var(--bdr);padding:8px 11px;border-radius:5px;
  font-family:inherit;font-size:12px}
select.ctrl-sel:focus,input.ctrl-num:focus{outline:1px solid var(--green)}
input.ctrl-num{width:80px}
.pipeline-strip{display:flex;align-items:center;flex-wrap:wrap;gap:0;margin:12px 0}
.ps{padding:5px 12px;background:var(--surf2);border:1px solid var(--bdr);
  border-radius:3px;font-size:10px;font-weight:700;letter-spacing:1.5px;color:var(--muted)}
.ps.active{background:var(--gdim);border-color:var(--green);color:var(--green)}
.ps.done{background:var(--gdark);border-color:#2d6a47;color:#4ade80}
.parr{color:var(--bdr);padding:0 5px;font-size:12px}

/* ── Log ── */
.log-card{background:var(--surf);border:1px solid var(--bdr);border-radius:8px;overflow:hidden;margin-top:14px}
.log-hdr{padding:10px 16px;border-bottom:1px solid var(--bdr);display:flex;
  align-items:center;justify-content:space-between}
.log-live{display:flex;align-items:center;gap:5px;font-size:10px;color:var(--green);letter-spacing:1px}
.ldot{width:6px;height:6px;background:var(--green);border-radius:50%;animation:blink 1s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.2}}
.log-body{height:260px;overflow-y:auto;padding:12px 16px;background:#030508;font-size:11px;line-height:1.9}
.log-body::-webkit-scrollbar{width:4px}
.log-body::-webkit-scrollbar-thumb{background:var(--bdr);border-radius:2px}
.ll{display:flex;gap:10px}
.lt{color:#2d3748;min-width:60px}
.lm.info{color:var(--text)}.lm.warning{color:var(--orange)}.lm.error{color:#ff8888}.lm.debug{color:#2d3748}

/* ── Toast ── */
.toast{position:fixed;bottom:18px;right:18px;background:var(--surf2);
  border:1px solid var(--bdr);border-radius:7px;padding:10px 16px;font-size:12px;
  opacity:0;transform:translateY(8px);transition:all .25s;z-index:999;pointer-events:none}
.toast.show{opacity:1;transform:translateY(0)}
.toast.ok{border-color:var(--green);color:var(--green)}
.toast.fail{border-color:var(--red);color:var(--red)}

/* ── Modal ── */
.modal-overlay{position:fixed;inset:0;background:#000000bb;z-index:300;
  display:flex;align-items:center;justify-content:center;display:none}
.modal-overlay.open{display:flex}
.modal{background:var(--surf);border:1px solid var(--bdr);border-radius:10px;
  padding:24px;width:520px;max-width:95vw}
.modal h3{color:var(--head);margin-bottom:14px;font-size:15px}
.modal-row{display:flex;align-items:center;gap:10px;margin-bottom:10px;flex-wrap:wrap}
.modal label{font-size:11px;color:var(--muted);letter-spacing:1px;text-transform:uppercase}
.modal select{background:var(--surf2);color:var(--text);border:1px solid var(--bdr);
  padding:8px 12px;border-radius:5px;font-family:inherit;font-size:12px}
.modal input[type=number]{background:var(--surf2);color:var(--text);border:1px solid var(--bdr);
  padding:8px 12px;border-radius:5px;font-family:inherit;font-size:12px;width:80px}
.modal-btns{display:flex;gap:8px;justify-content:flex-end;margin-top:18px}

.divider{border:none;border-top:1px solid var(--bdr);margin:12px 0}
</style>
</head>
<body>

<!-- Header -->
<div class="hdr">
  <div class="hdr-l">
    <span class="pill">ATLAS</span>
    <h1>Email Review</h1>
  </div>
  <div class="hdr-r">
    <span id="hdr-pending" style="font-size:12px;color:var(--muted)">— pending</span>
    <span id="hdr-approved" style="font-size:12px;color:var(--green)">— approved</span>
  </div>
</div>

<!-- Tabs -->
<div class="tabs">
  <div class="tab active" onclick="switchTab('queue')">📬 Queue</div>
  <div class="tab" onclick="switchTab('approved')">✅ Approved</div>
  <div class="tab" onclick="switchTab('pipeline')">⚙️ Pipeline</div>
</div>

<!-- ══ QUEUE TAB ══════════════════════════════════════════════════════════════ -->
<div class="panel active" id="panel-queue">

  <div class="topbar">
    <div class="stat-chip o"><div class="val" id="s-pending">—</div><div style="font-size:10px;color:var(--muted)">PENDING</div></div>
    <div class="stat-chip g"><div class="val" id="s-approved">—</div><div style="font-size:10px;color:var(--muted)">APPROVED</div></div>
    <div class="stat-chip"><div class="val" id="s-total">—</div><div style="font-size:10px;color:var(--muted)">TOTAL</div></div>
    <div class="spacer"></div>
    <button class="btn btn-gen" id="btn-gen" onclick="openGenModal()">⚡ Generate Emails</button>
    <button class="btn btn-exp" onclick="exportCSV()" id="btn-exp">⬇ Export Approved</button>
  </div>

  <div class="filters">
    <span class="flt-label">Filter:</span>
    <select class="flt" id="flt-status" onchange="renderQueue()">
      <option value="pending">Pending</option>
      <option value="all">All</option>
      <option value="approved">Approved</option>
      <option value="skipped">Skipped</option>
    </select>
    <select class="flt" id="flt-state" onchange="renderQueue()">
      <option value="">All states</option>
    </select>
    <select class="flt" id="flt-angle" onchange="renderQueue()">
      <option value="">All angles</option>
      <option value="community_bank_relationship">community_bank_relationship</option>
      <option value="mid_market_bank_grc">mid_market_bank_grc</option>
      <option value="enterprise_bank_scale">enterprise_bank_scale</option>
      <option value="credit_union_community_mission">credit_union_community_mission</option>
      <option value="savings_institution_compliance">savings_institution_compliance</option>
      <option value="general_fs_compliance">general_fs_compliance</option>
    </select>
    <select class="flt" id="flt-type" onchange="renderQueue()">
      <option value="">All types</option>
      <option value="bank">bank</option>
      <option value="credit_union">credit_union</option>
      <option value="savings">savings</option>
    </select>
    <button class="btn btn-ghost" style="padding:7px 12px;font-size:11px" onclick="clearSkipped()">
      Clear skipped
    </button>
  </div>

  <div class="email-list" id="email-list">
    <div class="empty">
      <div class="empty-icon">📭</div>
      <h2>No emails yet</h2>
      <p>Click <strong>Generate Emails</strong> to pull from your 3,544 Airtable accounts and build personalized cold email drafts.</p>
      <button class="btn btn-gen" onclick="openGenModal()">⚡ Generate Emails</button>
    </div>
  </div>
</div>

<!-- ══ APPROVED TAB ═══════════════════════════════════════════════════════════ -->
<div class="panel" id="panel-approved">
  <div class="topbar">
    <div class="stat-chip g"><div class="val" id="s-approved2">—</div><div style="font-size:10px;color:var(--muted)">APPROVED</div></div>
    <div class="spacer"></div>
    <button class="btn btn-exp" onclick="exportCSV()">⬇ Download CSV</button>
    <button class="btn btn-danger" onclick="clearApproved()">✕ Clear Approved</button>
  </div>
  <div class="email-list" id="approved-list">
    <div class="empty"><div class="empty-icon">✅</div><h2>No approved emails yet</h2>
    <p>Approve emails in the Queue tab. Approved emails appear here ready for CSV export or sending.</p></div>
  </div>
</div>

<!-- ══ PIPELINE TAB ════════════════════════════════════════════════════════════ -->
<div class="panel" id="panel-pipeline">
  <div class="grid2">
    <div class="ctrl-card">
      <div class="ctrl-title">Integrations</div>
      <div class="int-list" id="int-list">Loading…</div>
    </div>
    <div>
      <div class="ctrl-card" style="margin-bottom:14px">
        <div class="ctrl-title">Agent Controls</div>
        <div class="ctrl-row">
          <label style="font-size:11px;color:var(--muted)">Mode</label>
          <select class="ctrl-sel" id="mode-sel" onchange="changeMode(this.value)">
            <option value="shadow">shadow</option>
            <option value="review">review</option>
            <option value="auto">auto</option>
            <option value="paused">paused</option>
          </select>
          <label style="font-size:11px;color:var(--muted)">Limit</label>
          <input class="ctrl-num" type="number" id="limit-n" value="25" min="1" max="500"
                 onchange="updateLimit(this.value)">
        </div>
        <div style="margin-top:8px">
          <div class="ctrl-title" style="margin-bottom:10px">Pipeline</div>
          <div class="pipeline-strip">
            <span class="ps" data-s="SCOUT">SCOUT</span><span class="parr">→</span>
            <span class="ps" data-s="SENTINEL">SENTINEL</span><span class="parr">→</span>
            <span class="ps" data-s="RECON">RECON</span><span class="parr">→</span>
            <span class="ps" data-s="FORGE">FORGE</span><span class="parr">→</span>
            <span class="ps" data-s="VITALS">VITALS</span><span class="parr">→</span>
            <span class="ps" data-s="COMMAND">COMMAND</span>
          </div>
        </div>
      </div>
      <div class="log-card">
        <div class="log-hdr">
          <div class="ctrl-title" style="margin-bottom:0">Live Log</div>
          <div style="display:flex;align-items:center;gap:12px">
            <div class="log-live"><div class="ldot"></div>LIVE</div>
            <button class="btn btn-ghost" style="padding:4px 10px;font-size:10px" onclick="clearLog()">CLEAR</button>
          </div>
        </div>
        <div class="log-body" id="log-body">
          <div class="ll"><span class="lt">—</span><span class="lm info">Connecting…</span></div>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- ══ GENERATE MODAL ══════════════════════════════════════════════════════════ -->
<div class="modal-overlay" id="gen-modal">
  <div class="modal">
    <h3>⚡ Generate Email Drafts</h3>

    <!-- Source tabs -->
    <div style="display:flex;gap:0;margin-bottom:16px;border:1px solid var(--bdr);border-radius:6px;overflow:hidden">
      <div class="src-tab active" id="src-fdic" onclick="setSource('fdic')"
           style="flex:1;padding:9px;text-align:center;cursor:pointer;font-size:12px;font-weight:700;
                  background:var(--gdim);color:var(--green);border-right:1px solid var(--bdr)">
        🏦 FDIC Live
        <div style="font-size:10px;font-weight:400;color:var(--muted);margin-top:2px">4,279 banks · real-time</div>
      </div>
      <div class="src-tab" id="src-airtable" onclick="setSource('airtable')"
           style="flex:1;padding:9px;text-align:center;cursor:pointer;font-size:12px;font-weight:700;
                  background:var(--surf2);color:var(--muted)">
        📊 Airtable
        <div style="font-size:10px;font-weight:400;color:var(--muted);margin-top:2px">3,544 loaded · cached</div>
      </div>
    </div>

    <div class="modal-row">
      <label>How many</label>
      <input type="number" id="gen-limit" value="50" min="1" max="500">
      <label>State</label>
      <select id="gen-state">
        <option value="">All states</option>
      </select>
    </div>

    <!-- FDIC-only: asset range -->
    <div id="fdic-opts" class="modal-row" style="margin-top:4px">
      <label>Min assets $M</label>
      <input type="number" id="gen-min" value="100" min="50" max="50000" style="width:90px">
      <label>Max assets $M</label>
      <input type="number" id="gen-max" value="10000" min="100" max="100000" style="width:90px">
    </div>

    <p id="fdic-note" style="color:var(--muted);font-size:11px;margin-top:8px;line-height:1.6">
      Pulls live from <code style="color:var(--green)">api.fdic.gov</code> — no API key needed.
      Filters active banks by asset range, then generates personalized emails via FORGE.
    </p>

    <div class="modal-btns">
      <button class="btn btn-ghost" onclick="closeGenModal()">Cancel</button>
      <button class="btn btn-gen" onclick="startGeneration()">Generate</button>
    </div>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
// ── State ────────────────────────────────────────────────────────────────────
let emails     = [];
let evtSrc     = null;
let _openCards = new Set();   // IDs of cards currently expanded
const STEPS = ['SCOUT','SENTINEL','RECON','FORGE','VITALS','COMMAND'];
const US_STATES = [
  'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA','KS',
  'KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ','NM','NY',
  'NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT','VA','WA','WV',
  'WI','WY'
];

// ── Boot ─────────────────────────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  populateStateDropdowns();
  poll();
  setInterval(poll, 4000);
  connectSSE();
});

function populateStateDropdowns() {
  const opts = US_STATES.map(s => `<option value="${s}">${s}</option>`).join('');
  document.getElementById('flt-state').innerHTML += opts;
  document.getElementById('gen-state').innerHTML += opts;
}

// ── Tabs ─────────────────────────────────────────────────────────────────────
function switchTab(name) {
  document.querySelectorAll('.tab').forEach((t,i) => {
    t.classList.toggle('active', ['queue','approved','pipeline'][i] === name);
  });
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.getElementById('panel-' + name).classList.add('active');
  if (name === 'approved') renderApproved();
}

// ── Polling ───────────────────────────────────────────────────────────────────
async function poll() {
  try {
    const [statusR, emailsR] = await Promise.all([
      fetch('/api/status'),
      fetch('/api/emails?limit=500'),
    ]);
    const status = await statusR.json();
    emails = await emailsR.json();
    applyStatus(status);
    renderQueue();
    renderApproved();
  } catch {}
}

function applyStatus(d) {
  const q = d.queue || {};
  document.getElementById('s-pending').textContent  = q.pending  ?? '—';
  document.getElementById('s-approved').textContent = q.approved ?? '—';
  document.getElementById('s-approved2').textContent= q.approved ?? '—';
  document.getElementById('s-total').textContent    = q.total    ?? '—';
  document.getElementById('hdr-pending').textContent  = `${q.pending ?? '—'} pending`;
  document.getElementById('hdr-approved').textContent = `${q.approved ?? '—'} approved`;

  if (d.mode) document.getElementById('mode-sel').value = d.mode;
  if (d.daily_limit) document.getElementById('limit-n').value = d.daily_limit;
  if (d.integrations) renderInts(d.integrations);

  const gen = document.getElementById('btn-gen');
  gen.disabled = d.generating;
  gen.textContent = d.generating ? '⏳ Generating…' : '⚡ Generate Emails';

  document.getElementById('btn-exp').disabled = !(q.approved > 0);
}

// ── Render email queue ────────────────────────────────────────────────────────
function renderQueue() {
  const statusF = document.getElementById('flt-status').value;
  const stateF  = document.getElementById('flt-state').value;
  const angleF  = document.getElementById('flt-angle').value;
  const typeF   = document.getElementById('flt-type').value;

  let list = emails;
  if (statusF !== 'all') list = list.filter(e => e.status === statusF);
  if (stateF)  list = list.filter(e => e.account?.State === stateF);
  if (angleF)  list = list.filter(e => e.draft?.pitch_angle === angleF);
  if (typeF)   list = list.filter(e => e.account?.Institution_Type === typeF);

  const el = document.getElementById('email-list');

  if (!list.length) {
    if (!emails.length) {
      el.innerHTML = `
        <div class="empty">
          <div class="empty-icon">📭</div>
          <h2>No emails yet</h2>
          <p>Click <strong>Generate Emails</strong> to pull from your 3,544 Airtable accounts and build personalized cold email drafts.</p>
          <button class="btn btn-gen" onclick="openGenModal()">⚡ Generate Emails</button>
        </div>`;
    } else {
      el.innerHTML = `<div class="empty"><div class="empty-icon">🔍</div><h2>No matches</h2><p>Try adjusting the filters.</p></div>`;
    }
    return;
  }

  el.innerHTML = list.map(e => buildCard(e)).join('');

  // Restore open cards after DOM rebuild
  _openCards.forEach(id => {
    const body = document.getElementById('body-' + id);
    if (body) body.style.display = 'block';
  });
}

function renderApproved() {
  const approved = emails.filter(e => e.status === 'approved');
  const el = document.getElementById('approved-list');
  if (!approved.length) {
    el.innerHTML = `<div class="empty"><div class="empty-icon">✅</div><h2>No approved emails yet</h2>
      <p>Approve emails in the Queue tab.</p></div>`;
    return;
  }
  el.innerHTML = approved.map(e => buildCard(e)).join('');
}

// ── Card builder ──────────────────────────────────────────────────────────────
function buildCard(e) {
  const d = e.draft;
  const a = e.account || {};
  const typeBadge = {
    bank: 'badge-bank', credit_union: 'badge-cu', savings: 'badge-sav'
  }[a.Institution_Type] || 'badge-bank';
  const typeLabel = (a.Institution_Type || 'bank').replace('_', ' ');

  const bodyLines = (d.body || '').split('\n');
  const preview   = bodyLines.slice(0, 5).join('\n');
  const isFull    = bodyLines.length <= 8;

  const titles = (d.target_titles || []).slice(0, 4)
    .map(t => `<span class="target-pill">${esc(t)}</span>`).join(' ');

  const approveLabel = e.status === 'approved' ? '✓ Approved' : '✓ Approve';
  const skipLabel    = e.status === 'skipped'  ? '✗ Skipped'  : '✗ Skip';

  return `
<div class="card ${e.status}" id="card-${e.id}" data-id="${e.id}">
  <div class="card-head" onclick="toggleCard('${e.id}')">
    <div class="card-co">
      <div class="co-name">${esc(d.company_name || '')}</div>
      <div class="co-meta">
        <span class="badge badge-loc">${esc(a.City || '')}${a.City && a.State ? ', ' : ''}${esc(a.State || '')}</span>
        ${a.Asset_M ? `<span class="badge badge-assets">$${fmtM(a.Asset_M)}M</span>` : ''}
        <span class="badge ${typeBadge}">${typeLabel}</span>
        <span class="badge badge-angle">${(d.pitch_angle || '').replace(/_/g,' ')}</span>
        ${d.case_study_used ? `<span class="badge badge-loc">via ${esc(d.case_study_used)}</span>` : ''}
      </div>
    </div>
    <div class="card-status">
      <div class="status-dot ${e.status}"></div>
      <span style="font-size:11px;color:var(--muted)">${e.status}</span>
    </div>
  </div>

  <div class="card-body" id="body-${e.id}" style="display:none">
    <div class="subject-row">
      <div class="subject-lbl">Subject</div>
      <div class="subject-val" id="subj-${e.id}">${esc(d.subject || '')}</div>
    </div>

    <div style="position:relative">
      <div class="email-body" id="email-body-${e.id}">${esc(d.body || '')}</div>
      ${!isFull ? `<div class="body-fade" id="fade-${e.id}"></div>` : ''}
    </div>
    ${!isFull ? `<span class="show-more" onclick="toggleBodyExpand('${e.id}')">Show full email ▾</span>` : ''}

    <div class="targets-row">Targets: ${titles}</div>

    <div class="actions" onclick="event.stopPropagation()">
      <button class="btn-approve" onclick="setStatus('${e.id}','approved')">${approveLabel}</button>
      <button class="btn-skip"    onclick="setStatus('${e.id}','skipped')">${skipLabel}</button>
      <button class="btn-sm" onclick="copyEmail('${e.id}')">⎘ Copy</button>
      <button class="btn-sm" id="edit-btn-${e.id}" onclick="toggleEdit('${e.id}')">✎ Edit</button>
    </div>
  </div>
</div>`;
}

// ── Card interactions ─────────────────────────────────────────────────────────
function toggleCard(id) {
  const body = document.getElementById('body-' + id);
  if (!body) return;
  const opening = body.style.display === 'none' || body.style.display === '';
  body.style.display = opening ? 'block' : 'none';
  opening ? _openCards.add(id) : _openCards.delete(id);
}

function toggleBodyExpand(id) {
  const body = document.getElementById('email-body-' + id);
  const fade = document.getElementById('fade-' + id);
  const btn  = body.nextElementSibling?.nextElementSibling;
  const expanded = body.classList.toggle('expanded');
  if (fade) fade.classList.toggle('hidden', expanded);
  if (btn && btn.classList.contains('show-more'))
    btn.textContent = expanded ? 'Show less ▴' : 'Show full email ▾';
}

function toggleEdit(id) {
  const subjEl = document.getElementById('subj-' + id);
  const bodyEl = document.getElementById('email-body-' + id);
  const btnEl  = document.getElementById('edit-btn-' + id);
  const editing = subjEl.contentEditable === 'true';

  if (editing) {
    // Save
    const newSubj = subjEl.textContent.trim();
    const newBody = bodyEl.textContent.trim();
    saveEdit(id, newSubj, newBody);
    subjEl.contentEditable = 'false';
    bodyEl.contentEditable = 'false';
    btnEl.textContent = '✎ Edit';
    btnEl.classList.remove('editing');
  } else {
    // Enter edit mode
    bodyEl.classList.add('expanded');
    const fade = document.getElementById('fade-' + id);
    if (fade) fade.classList.add('hidden');
    subjEl.contentEditable = 'true';
    bodyEl.contentEditable = 'true';
    subjEl.focus();
    btnEl.textContent = '✓ Save';
    btnEl.classList.add('editing');
  }
}

async function saveEdit(id, subject, body) {
  try {
    await fetch(`/api/emails/${id}/edit`, {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({subject, body}),
    });
    // Update local cache
    const e = emails.find(x => x.id === id);
    if (e) { e.draft.subject = subject; e.draft.body = body; }
    toast('Saved', 'ok');
  } catch { toast('Save failed', 'fail'); }
}

function copyEmail(id) {
  const e = emails.find(x => x.id === id);
  if (!e) return;
  const text = `Subject: ${e.draft.subject}\n\n${e.draft.body}`;
  navigator.clipboard.writeText(text).then(() => toast('Copied to clipboard', 'ok'));
}

async function setStatus(id, status) {
  try {
    await fetch(`/api/emails/${id}/status`, {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({status}),
    });
    const e = emails.find(x => x.id === id);
    if (e) e.status = status;
    renderQueue();
    renderApproved();
    updateStats();
    toast(status === 'approved' ? '✓ Approved' : '✗ Skipped', status === 'approved' ? 'ok' : '');
  } catch { toast('Failed', 'fail'); }
}

function updateStats() {
  const p = emails.filter(e => e.status === 'pending').length;
  const a = emails.filter(e => e.status === 'approved').length;
  document.getElementById('s-pending').textContent  = p;
  document.getElementById('s-approved').textContent = a;
  document.getElementById('s-approved2').textContent= a;
  document.getElementById('s-total').textContent    = emails.length;
  document.getElementById('hdr-pending').textContent  = `${p} pending`;
  document.getElementById('hdr-approved').textContent = `${a} approved`;
}

// ── Generate modal ────────────────────────────────────────────────────────────
let _genSource = 'fdic';

function openGenModal()  { document.getElementById('gen-modal').classList.add('open'); }
function closeGenModal() { document.getElementById('gen-modal').classList.remove('open'); }

function setSource(src) {
  _genSource = src;
  const fdicTab = document.getElementById('src-fdic');
  const atTab   = document.getElementById('src-airtable');
  const fdicOpts = document.getElementById('fdic-opts');
  const fdicNote = document.getElementById('fdic-note');

  if (src === 'fdic') {
    fdicTab.style.background = 'var(--gdim)'; fdicTab.style.color = 'var(--green)';
    atTab.style.background   = 'var(--surf2)'; atTab.style.color  = 'var(--muted)';
    fdicOpts.style.display = 'flex';
    fdicNote.style.display = 'block';
  } else {
    atTab.style.background   = 'var(--gdim)'; atTab.style.color   = 'var(--green)';
    fdicTab.style.background = 'var(--surf2)'; fdicTab.style.color = 'var(--muted)';
    fdicOpts.style.display = 'none';
    fdicNote.innerHTML = 'Pulls from your Airtable base (3,544 banks already loaded).';
    fdicNote.style.display = 'block';
  }
}

async function startGeneration() {
  closeGenModal();
  const limit     = parseInt(document.getElementById('gen-limit').value, 10) || 50;
  const state     = document.getElementById('gen-state').value || null;
  const assetMin  = parseInt(document.getElementById('gen-min').value, 10)  || 100;
  const assetMax  = parseInt(document.getElementById('gen-max').value, 10)  || 10000;

  const body = {source: _genSource, limit, state, asset_min_m: assetMin, asset_max_m: assetMax};
  try {
    const r = await fetch('/api/emails/generate', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify(body),
    });
    const d = await r.json();
    if (d.error) toast(d.error, 'fail');
    else toast(`Generating ${limit} emails from ${_genSource.toUpperCase()}…`, 'ok');
  } catch { toast('Failed to start generation', 'fail'); }
}

// ── Clear / export ────────────────────────────────────────────────────────────
async function clearSkipped() {
  await fetch('/api/emails/clear', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({status: 'skipped'}),
  });
  emails = emails.filter(e => e.status !== 'skipped');
  renderQueue();
  toast('Skipped cleared', 'ok');
}

async function clearApproved() {
  if (!confirm('Clear all approved emails?')) return;
  await fetch('/api/emails/clear', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({status: 'approved'}),
  });
  emails = emails.filter(e => e.status !== 'approved');
  renderApproved();
  updateStats();
  toast('Cleared', 'ok');
}

function exportCSV() {
  window.location = '/api/emails/export.csv';
}

// ── Integrations ──────────────────────────────────────────────────────────────
const INT_ORDER = ['airtable','claude','salesforce','outreach','sixsense',
                   'teams','instantly','supabase','zerobounce'];

function renderInts(ints) {
  document.getElementById('int-list').innerHTML = INT_ORDER.map(k =>
    `<div class="int-row">
      <span>${k}</span>
      <span class="ibadge ${ints[k] ? 'ibadge-ok' : 'ibadge-miss'}">${ints[k] ? 'LIVE' : 'MISSING'}</span>
    </div>`
  ).join('');
}

// ── Mode / config ─────────────────────────────────────────────────────────────
async function changeMode(m) {
  await fetch('/api/mode', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mode:m})});
  toast('Mode → ' + m, 'ok');
}
async function updateLimit(v) {
  await fetch('/api/config', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({daily_limit:parseInt(v)})});
  toast('Limit → ' + v, 'ok');
}

// ── SSE ───────────────────────────────────────────────────────────────────────
function connectSSE() {
  if (evtSrc) evtSrc.close();
  evtSrc = new EventSource('/api/stream');
  evtSrc.onmessage = e => {
    if (!e.data || e.data === '{}') return;
    try { appendLog(JSON.parse(e.data)); } catch {}
  };
  evtSrc.onerror = () => setTimeout(connectSSE, 3000);
}

function appendLog(entry) {
  const b = document.getElementById('log-body');
  if (!b) return;
  const d = document.createElement('div');
  d.className = 'll';
  d.innerHTML = `<span class="lt">${entry.time}</span><span class="lm ${entry.level}">${esc(entry.message)}</span>`;
  b.appendChild(d);
  b.scrollTop = b.scrollHeight;
  // Pipeline step detection
  for (const s of STEPS) {
    if (entry.message.includes('→ '+s)||entry.message.includes('[CORTEX → '+s+']')) {
      document.querySelectorAll('.ps').forEach(el => {
        const si = STEPS.indexOf(el.dataset.s);
        const ci = STEPS.indexOf(s);
        el.className = 'ps' + (si < ci ? ' done' : si === ci ? ' active' : '');
      });
      break;
    }
  }
  // Auto-refresh email list when new ones appear
  if (entry.message.includes('Done —') || entry.message.includes('emails ready')) {
    poll();
  }
}

function clearLog() { document.getElementById('log-body').innerHTML = ''; }

// ── Utils ─────────────────────────────────────────────────────────────────────
function esc(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
function fmtM(n) { return Number(n).toLocaleString(); }

function toast(msg, cls='') {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = 'toast ' + cls + ' show';
  setTimeout(() => el.className = 'toast', 2600);
}

// Close modal on overlay click
document.getElementById('gen-modal').addEventListener('click', e => {
  if (e.target === e.currentTarget) closeGenModal();
});
</script>
</body>
</html>"""


# ── API: legacy config endpoint ────────────────────────────────────────────────

@app.route("/api/config", methods=["POST"])
def api_config():
    data = request.get_json(silent=True) or {}
    if "daily_limit" in data:
        limit = max(1, min(500, int(data["daily_limit"])))
        _agent_state["daily_limit"] = limit
        _patch_env("ATLAS_DAILY_LIMIT", str(limit))
    return jsonify({"ok": True})


# ── Entry ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # ── Load persisted queue ───────────────────────────────────────────
    loaded = _load_queue()

    ints = _integration_status()
    live = sum(1 for v in ints.values() if v)

    port = int(os.getenv("UI_PORT", "5001"))
    print(f"\n  ┌────────────────────────────────────────┐")
    print(f"  │  ATLAS Command Center                  │")
    print(f"  │  → http://localhost:{port}                 │")
    print(f"  │  Queue: {loaded} emails loaded             │")
    print(f"  │  Integrations: {live}/{len(ints)} live              │")
    print(f"  └────────────────────────────────────────┘\n")

    _log("info", f"Loaded {loaded} emails from disk")

    # ── Auto-generate from FDIC if queue is empty ─────────────────────
    if loaded == 0:
        _log("info", "Queue empty — auto-generating 100 emails from FDIC…")
        _gen_thread = threading.Thread(
            target=_generate_from_fdic_thread,
            args=(100, None, 100, 10000),
            daemon=True,
        )
        _gen_thread.start()

    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
