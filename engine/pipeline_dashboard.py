"""
pipeline_dashboard.py — FORGE Visual Pipeline Dashboard

DEPRECATED (Phase 0): Local development tool only. Not for production.
Use the Flask admin portal (/admin) or TradeBuilt dashboard instead.
Set FORGE_DASHBOARD_ENABLED=false to disable entirely.

Run: python3 pipeline_dashboard.py
Open: http://127.0.0.1:5050 (localhost only)
"""

import csv
import json
import os
import sys
import datetime
import re
from flask import Flask, jsonify, request, Response
from dotenv import load_dotenv

from api_auth import validate_api_key, is_auth_enabled

load_dotenv()

if os.getenv("FORGE_DASHBOARD_ENABLED", "true").lower() == "false":
    print("FORGE pipeline dashboard is disabled (FORGE_DASHBOARD_ENABLED=false).")
    sys.exit(0)

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
LEADS_CSV   = os.path.join(SCRIPT_DIR, "leads.csv")
CALL_CSV    = os.path.join(SCRIPT_DIR, "call_list.csv")
LOG_CSV     = os.path.join(SCRIPT_DIR, "log.csv")
SEND_LOG    = os.path.join(SCRIPT_DIR, "send_log.json")
ENV_FILE    = os.path.join(SCRIPT_DIR, ".env")

app = Flask(__name__)


@app.before_request
def _require_dashboard_api_key():
    """Phase 0: all /api/* routes require X-FORGE-API-Key when auth is enabled."""
    if not request.path.startswith("/api/"):
        return None
    if not is_auth_enabled():
        return None
    if validate_api_key(
        request.headers.get("Authorization"),
        request.headers.get("X-FORGE-API-Key"),
    ):
        return None
    return jsonify({"error": "Unauthorized"}), 401


# ─── DATA HELPERS ─────────────────────────────────────────────────────────────

def read_leads():
    if not os.path.exists(LEADS_CSV):
        return []
    with open(LEADS_CSV, newline="") as f:
        return list(csv.DictReader(f))

def write_leads(rows, fieldnames):
    with open(LEADS_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

def ensure_approved_column():
    """Add 'approved' column to leads.csv if missing."""
    if not os.path.exists(LEADS_CSV):
        return
    rows = read_leads()
    if not rows:
        return
    if "approved" in (rows[0].keys()):
        return
    fieldnames = list(rows[0].keys()) + ["approved"]
    for r in rows:
        r.setdefault("approved", "")
    write_leads(rows, fieldnames)

def read_call_leads():
    if not os.path.exists(CALL_CSV):
        return []
    with open(CALL_CSV, newline="") as f:
        return list(csv.DictReader(f))

def emails_sent_today():
    if not os.path.exists(SEND_LOG):
        return 0
    try:
        with open(SEND_LOG) as f:
            data = json.load(f)
        today = datetime.date.today().isoformat()
        return data.get("count", 0) if data.get("date") == today else 0
    except Exception:
        return 0

def get_env():
    env = {}
    if not os.path.exists(ENV_FILE):
        return env
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env

def set_env_var(key, value):
    lines = []
    found = False
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE) as f:
            lines = f.readlines()
    new_lines = []
    for line in lines:
        if line.strip().startswith(f"{key}="):
            new_lines.append(f"{key}={value}\n")
            found = True
        else:
            new_lines.append(line)
    if not found:
        new_lines.append(f"{key}={value}\n")
    with open(ENV_FILE, "w") as f:
        f.writelines(new_lines)

def build_email_preview(lead):
    """Generate the email HTML/plain that would be sent to this lead."""
    try:
        from emailer import build_html_email
        demo_url = (lead.get("demo_site_path") or "#").strip()
        _, html, plain = build_html_email(lead, demo_url)
        return {"html": html, "plain": plain}
    except Exception as e:
        return {"html": f"<p>Preview error: {e}</p>", "plain": str(e)}


# ─── PIPELINE STATS ───────────────────────────────────────────────────────────

def pipeline_stats():
    leads      = read_leads()
    call_leads = read_call_leads()
    env        = get_env()
    test_mode  = env.get("TEST_MODE", "true").lower() == "true"
    approval_mode = env.get("APPROVAL_MODE", "false").lower() == "true"

    total_scraped = len(leads) + len(call_leads)
    with_email    = [l for l in leads if (l.get("email") or "").strip()]
    with_demo     = [l for l in leads if (l.get("demo_site_path") or "").strip()]
    already_sent  = [l for l in leads if (l.get("email_sent") or "").strip().lower() == "true"]
    suppressed    = [l for l in leads if (l.get("reply_status") or "").strip().lower()
                     in {"bounced", "stop", "stopped", "unsubscribe", "unsubscribed"}]

    pending_approval = [
        l for l in leads
        if (l.get("email") or "").strip()
        and (l.get("demo_site_path") or "").strip()
        and (l.get("email_sent") or "").strip().lower() != "true"
        and (l.get("approved") or "").strip().lower() not in ("true", "rejected")
        and (l.get("reply_status") or "").strip().lower()
            not in {"bounced", "stop", "stopped", "unsubscribe", "unsubscribed"}
    ]
    approved_ready = [
        l for l in leads
        if (l.get("email") or "").strip()
        and (l.get("demo_site_path") or "").strip()
        and (l.get("email_sent") or "").strip().lower() != "true"
        and (l.get("approved") or "").strip().lower() == "true"
    ]
    needs_demo = [
        l for l in leads
        if (l.get("email") or "").strip()
        and not (l.get("demo_site_path") or "").strip()
        and (l.get("email_sent") or "").strip().lower() != "true"
    ]

    return {
        "test_mode": test_mode,
        "approval_mode": approval_mode,
        "emails_today": emails_sent_today(),
        "nodes": {
            "scrape":    {"count": total_scraped,         "label": "Scraped",        "status": "done"},
            "score":     {"count": len(leads),            "label": "Scored & Split", "status": "done"},
            "demo":      {"count": len(with_demo),        "label": "Demos Built",    "status": "done",
                          "warning": len(needs_demo)},
            "approve":   {"count": len(pending_approval), "label": "Awaiting Approval",
                          "status": "active" if pending_approval else "done"},
            "send":      {"count": len(already_sent),     "label": "Emails Sent",    "status": "done"},
            "followup":  {"count": 0,                     "label": "Follow-Ups",     "status": "idle"},
        },
        "approved_ready": len(approved_ready),
        "pending_approval": len(pending_approval),
        "call_only": len(call_leads),
    }


# ─── API ROUTES ───────────────────────────────────────────────────────────────

@app.route("/api/stats")
def api_stats():
    return jsonify(pipeline_stats())

@app.route("/api/leads")
def api_leads():
    stage = request.args.get("stage", "all")
    leads = read_leads()
    if stage == "pending":
        leads = [l for l in leads
                 if (l.get("email") or "").strip()
                 and (l.get("demo_site_path") or "").strip()
                 and (l.get("email_sent") or "").strip().lower() != "true"
                 and (l.get("approved") or "").strip().lower() not in ("true", "rejected")]
    elif stage == "approved":
        leads = [l for l in leads if (l.get("approved") or "").strip().lower() == "true"
                 and (l.get("email_sent") or "").strip().lower() != "true"]
    elif stage == "sent":
        leads = [l for l in leads if (l.get("email_sent") or "").strip().lower() == "true"]
    elif stage == "needs_demo":
        leads = [l for l in leads
                 if (l.get("email") or "").strip()
                 and not (l.get("demo_site_path") or "").strip()
                 and (l.get("email_sent") or "").strip().lower() != "true"]
    return jsonify(leads[:200])

@app.route("/api/approve", methods=["POST"])
def api_approve():
    body = request.json or {}
    name = (body.get("business_name") or "").strip()
    action = body.get("action", "approve")  # "approve" | "reject"
    if not name:
        return jsonify({"error": "business_name required"}), 400

    rows = read_leads()
    if not rows:
        return jsonify({"error": "no leads"}), 404
    fieldnames = list(rows[0].keys())
    if "approved" not in fieldnames:
        fieldnames.append("approved")

    updated = False
    for row in rows:
        if row.get("business_name", "").strip().lower() == name.lower():
            row["approved"] = "true" if action == "approve" else "rejected"
            updated = True
            break

    if updated:
        write_leads(rows, fieldnames)
    return jsonify({"ok": updated, "name": name, "action": action})

@app.route("/api/approve-all", methods=["POST"])
def api_approve_all():
    rows = read_leads()
    if not rows:
        return jsonify({"error": "no leads"}), 404
    fieldnames = list(rows[0].keys())
    if "approved" not in fieldnames:
        fieldnames.append("approved")
    count = 0
    for row in rows:
        if ((row.get("email") or "").strip()
                and (row.get("demo_site_path") or "").strip()
                and (row.get("email_sent") or "").strip().lower() != "true"
                and (row.get("approved") or "").strip().lower() not in ("true", "rejected")):
            row["approved"] = "true"
            count += 1
    write_leads(rows, fieldnames)
    return jsonify({"ok": True, "approved": count})

@app.route("/api/email-preview")
def api_email_preview():
    name = request.args.get("name", "").strip()
    leads = read_leads()
    lead = next((l for l in leads if l.get("business_name", "").strip().lower() == name.lower()), None)
    if not lead:
        return jsonify({"error": "lead not found"}), 404
    return jsonify(build_email_preview(lead))

@app.route("/api/toggle-test-mode", methods=["POST"])
def api_toggle_test_mode():
    env = get_env()
    current = env.get("TEST_MODE", "true").lower() == "true"
    new_val = "false" if current else "true"
    set_env_var("TEST_MODE", new_val)
    return jsonify({"test_mode": new_val == "true"})

@app.route("/api/toggle-approval-mode", methods=["POST"])
def api_toggle_approval_mode():
    env = get_env()
    current = env.get("APPROVAL_MODE", "false").lower() == "true"
    new_val = "false" if current else "true"
    set_env_var("APPROVAL_MODE", new_val)
    return jsonify({"approval_mode": new_val == "true"})

@app.route("/api/run-pipeline", methods=["POST"])
def api_run_pipeline():
    import subprocess, sys
    try:
        subprocess.Popen(
            [sys.executable, os.path.join(SCRIPT_DIR, "agent.py"), "--once"],
            cwd=SCRIPT_DIR,
            stdout=open(os.path.join(SCRIPT_DIR, "scheduler.log"), "a"),
            stderr=subprocess.STDOUT,
        )
        return jsonify({"status": "started"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ─── DASHBOARD HTML ───────────────────────────────────────────────────────────

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Forge Pipeline</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:#f5f5f7;color:#1d1d1f;font-family:-apple-system,BlinkMacSystemFont,'SF Pro Display','SF Pro Text',system-ui,sans-serif;min-height:100vh;-webkit-font-smoothing:antialiased}
  :root{--blue:#0071e3;--blue-hover:#0077ed;--red:#ff3b30;--green:#34c759;--orange:#ff9500;--muted:#86868b;--card:#ffffff;--border:rgba(0,0,0,.08);--shadow:0 2px 12px rgba(0,0,0,.08);--shadow-lg:0 8px 32px rgba(0,0,0,.12)}

  /* NAV */
  nav{background:rgba(255,255,255,.85);backdrop-filter:saturate(180%) blur(20px);-webkit-backdrop-filter:saturate(180%) blur(20px);border-bottom:1px solid var(--border);padding:0 32px;display:flex;align-items:center;gap:16px;height:52px;position:sticky;top:0;z-index:50}
  .logo{font-size:17px;font-weight:600;color:#1d1d1f;letter-spacing:-.02em}
  .logo span{color:var(--muted);font-size:13px;font-weight:400;margin-left:6px}
  .nav-right{display:flex;gap:8px;margin-left:auto;align-items:center}
  .pill{display:inline-flex;align-items:center;gap:5px;padding:4px 10px;border-radius:20px;font-size:12px;font-weight:500}
  .pill-red{background:#fff2f2;color:var(--red)}
  .pill-green{background:#f0fff4;color:#248a3d}
  .pill-orange{background:#fff8f0;color:#c93400}
  .pill .dot{width:6px;height:6px;border-radius:50%;background:currentColor}
  .btn{display:inline-flex;align-items:center;gap:6px;padding:7px 14px;border-radius:980px;font-size:13px;font-weight:500;border:none;cursor:pointer;transition:all .15s;letter-spacing:-.01em}
  .btn-blue{background:var(--blue);color:#fff}
  .btn-blue:hover{background:var(--blue-hover)}
  .btn-secondary{background:#f5f5f7;color:#1d1d1f;border:1px solid var(--border)}
  .btn-secondary:hover{background:#e8e8ed}
  .btn-sm{padding:5px 12px;font-size:12px;border-radius:980px}
  .btn-approve{background:#f0fff4;color:#1a7f37;border:1px solid #c6f0d0;font-weight:600}
  .btn-approve:hover{background:#d1fae5}
  .btn-reject{background:#fff2f2;color:#c0392b;border:1px solid #ffd5d5;font-weight:600}
  .btn-reject:hover{background:#fee2e2}

  /* PIPELINE */
  .pipeline-wrap{padding:32px 32px 0;overflow-x:auto}
  .pipeline{display:flex;align-items:center;gap:0;min-width:720px}
  .node{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:18px 22px;min-width:130px;text-align:center;cursor:pointer;transition:all .2s;flex-shrink:0;box-shadow:var(--shadow)}
  .node:hover{transform:translateY(-3px);box-shadow:var(--shadow-lg);border-color:#c7c7cc}
  .node.active{border-color:var(--blue);box-shadow:0 0 0 3px rgba(0,113,227,.12),var(--shadow)}
  .node.warning{border-color:var(--orange)}
  .node-icon{font-size:26px;margin-bottom:8px;line-height:1}
  .node-count{font-size:30px;font-weight:700;color:#1d1d1f;line-height:1;letter-spacing:-.03em}
  .node-label{font-size:11px;color:var(--muted);margin-top:5px;font-weight:500}
  .node-warn{font-size:10px;color:var(--orange);margin-top:4px;font-weight:500}
  .node.active .node-count{color:var(--blue)}
  .connector{display:flex;align-items:center;padding:0 8px;flex-shrink:0}
  .connector-line{width:28px;height:1px;background:#d2d2d7}
  .connector-arrow{color:#aeaeb2;font-size:14px;margin-left:-4px}

  /* STATS */
  .stats-row{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;padding:24px 32px 0}
  .stat-card{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:20px 22px;box-shadow:var(--shadow)}
  .stat-label{font-size:12px;color:var(--muted);font-weight:500;margin-bottom:8px;letter-spacing:-.01em}
  .stat-val{font-size:32px;font-weight:700;color:#1d1d1f;letter-spacing:-.04em;line-height:1}
  .stat-sub{font-size:12px;color:#aeaeb2;margin-top:4px}

  /* TOOLBAR */
  .toolbar{display:flex;gap:10px;padding:20px 32px;align-items:center;flex-wrap:wrap}
  .toolbar-divider{width:1px;height:20px;background:var(--border);margin:0 2px}

  /* SECTION */
  .section{padding:0 32px 48px}
  .section-header{display:flex;align-items:center;gap:12px;margin-bottom:16px}
  .section-title{font-size:17px;font-weight:600;color:#1d1d1f;letter-spacing:-.02em}
  .tab-group{display:flex;background:#e8e8ed;border-radius:8px;padding:2px;margin-left:auto;gap:2px}
  .tab{padding:5px 14px;border-radius:6px;font-size:13px;font-weight:500;cursor:pointer;background:transparent;border:none;color:var(--muted);transition:all .15s}
  .tab.active{background:#fff;color:#1d1d1f;box-shadow:0 1px 4px rgba(0,0,0,.12)}

  /* TABLE */
  .table-wrap{background:var(--card);border:1px solid var(--border);border-radius:16px;overflow:hidden;box-shadow:var(--shadow)}
  table{width:100%;border-collapse:collapse;font-size:13px}
  th{text-align:left;padding:11px 16px;color:var(--muted);font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.04em;background:#fafafa;border-bottom:1px solid var(--border)}
  td{padding:12px 16px;border-bottom:1px solid #f5f5f7;vertical-align:middle;color:#1d1d1f}
  tr:last-child td{border-bottom:none}
  tr:hover td{background:#fafafa}
  .tier-hot{background:#fff2f2;color:#c0392b;padding:3px 8px;border-radius:6px;font-size:11px;font-weight:700;letter-spacing:.02em}
  .tier-warm{background:#fff8f0;color:#c93400;padding:3px 8px;border-radius:6px;font-size:11px;font-weight:700;letter-spacing:.02em}
  .chip{display:inline-flex;align-items:center;gap:5px;padding:3px 9px;border-radius:6px;font-size:12px;font-weight:500}
  .chip-green{background:#f0fff4;color:#248a3d}
  .chip-orange{background:#fff8f0;color:#c93400}
  .chip-red{background:#fff2f2;color:#c0392b}
  .chip-gray{background:#f5f5f7;color:var(--muted)}
  .chip .dot{width:5px;height:5px;border-radius:50%;background:currentColor}
  .actions{display:flex;gap:6px;align-items:center}
  .demo-link{font-size:11px;color:var(--blue);text-decoration:none;font-weight:500}
  .demo-link:hover{text-decoration:underline}
  .empty{text-align:center;padding:56px 24px;color:var(--muted);font-size:14px}

  /* MODAL */
  .modal-bg{position:fixed;inset:0;background:rgba(0,0,0,.4);backdrop-filter:blur(8px);display:none;align-items:center;justify-content:center;z-index:100;padding:24px}
  .modal-bg.open{display:flex}
  .modal{background:#fff;border-radius:20px;max-width:700px;width:100%;max-height:88vh;overflow:hidden;display:flex;flex-direction:column;box-shadow:0 24px 80px rgba(0,0,0,.25)}
  .modal-head{padding:20px 24px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:12px}
  .modal-title{font-weight:600;font-size:15px;flex:1;letter-spacing:-.01em}
  .modal-close{background:#f5f5f7;border:none;color:#86868b;font-size:16px;cursor:pointer;padding:6px 10px;border-radius:8px;line-height:1}
  .modal-close:hover{background:#e8e8ed;color:#1d1d1f}
  .modal-tabs{display:flex;gap:0;padding:0 24px;border-bottom:1px solid var(--border)}
  .modal-tab{padding:11px 16px;font-size:13px;cursor:pointer;border-bottom:2px solid transparent;color:var(--muted);background:none;border-left:none;border-right:none;border-top:none;font-weight:500;transition:.1s}
  .modal-tab.active{color:var(--blue);border-bottom-color:var(--blue)}
  .modal-body{flex:1;overflow:auto}
  .preview-frame{width:100%;border:none;height:520px;background:#f5f5f7;display:block}
  .plain-preview{padding:24px;font-family:'SF Mono',ui-monospace,monospace;font-size:12px;color:#3a3a3c;line-height:1.7;white-space:pre-wrap;background:#fafafa}

  /* TOAST */
  .toast{position:fixed;bottom:28px;left:50%;transform:translateX(-50%);background:rgba(29,29,31,.92);backdrop-filter:blur(12px);color:#fff;border-radius:980px;padding:11px 22px;font-size:13px;font-weight:500;display:none;z-index:200;white-space:nowrap;box-shadow:0 4px 20px rgba(0,0,0,.2)}
  .toast.show{display:block;animation:fadeup .2s ease}
  @keyframes fadeup{from{opacity:0;transform:translateX(-50%) translateY(8px)}to{opacity:1;transform:translateX(-50%) translateY(0)}}

  /* BILLING BANNER */
  .billing-warn{background:#fff8f0;border:1px solid #ffd5b0;border-radius:12px;padding:14px 20px;margin:20px 32px 0;font-size:13px;color:#7c3600;display:none;line-height:1.6}
  .billing-warn strong{font-weight:600}
  .billing-warn a{color:var(--blue);font-weight:500}
</style>
</head>
<body>

<nav>
  <div class="logo">Forge <span>Pipeline</span></div>
  <div class="nav-right">
    <span class="pill" id="mode-badge"><span class="dot"></span>Loading</span>
    <span class="pill pill-orange" id="approval-badge" style="display:none">Approval Mode</span>
    <button class="btn btn-secondary btn-sm" onclick="toggleTestMode()">Toggle Live / Test</button>
    <button class="btn btn-blue btn-sm" onclick="runPipeline()">▶ Run Now</button>
  </div>
</nav>

<div class="billing-warn" id="billing-warn">
  <strong>Google Places API — Billing Required</strong> &nbsp;·&nbsp;
  The scraper can't find new leads until billing is enabled. It's free up to $200/month and your volume won't exceed that.
  <a href="https://console.cloud.google.com/billing" target="_blank">Enable billing →</a>
  &nbsp; Your 49 existing leads are unaffected.
</div>

<!-- PIPELINE -->
<div class="pipeline-wrap">
  <div class="pipeline">
    <div class="node" id="node-scrape" onclick="showStage('all')">
      <div class="node-icon">🔍</div>
      <div class="node-count" id="cnt-scrape">—</div>
      <div class="node-label">Scraped</div>
    </div>
    <div class="connector"><div class="connector-line"></div><div class="connector-arrow">›</div></div>
    <div class="node" id="node-score" onclick="showStage('all')">
      <div class="node-icon">📊</div>
      <div class="node-count" id="cnt-score">—</div>
      <div class="node-label">Scored</div>
    </div>
    <div class="connector"><div class="connector-line"></div><div class="connector-arrow">›</div></div>
    <div class="node" id="node-demo" onclick="showStage('needs_demo')">
      <div class="node-icon">🌐</div>
      <div class="node-count" id="cnt-demo">—</div>
      <div class="node-label">Demos Built</div>
      <div class="node-warn" id="warn-demo" style="display:none"></div>
    </div>
    <div class="connector"><div class="connector-line"></div><div class="connector-arrow">›</div></div>
    <div class="node active" id="node-approve" onclick="showStage('pending')">
      <div class="node-icon">✅</div>
      <div class="node-count" id="cnt-approve">—</div>
      <div class="node-label">Awaiting Approval</div>
    </div>
    <div class="connector"><div class="connector-line"></div><div class="connector-arrow">›</div></div>
    <div class="node" id="node-send" onclick="showStage('sent')">
      <div class="node-icon">📨</div>
      <div class="node-count" id="cnt-send">—</div>
      <div class="node-label">Sent</div>
    </div>
    <div class="connector"><div class="connector-line"></div><div class="connector-arrow">›</div></div>
    <div class="node" id="node-followup">
      <div class="node-icon">🔄</div>
      <div class="node-count" id="cnt-followup">—</div>
      <div class="node-label">Follow-Ups</div>
    </div>
  </div>
</div>

<!-- STATS -->
<div class="stats-row">
  <div class="stat-card">
    <div class="stat-label">Sent Today</div>
    <div class="stat-val" id="stat-today">—</div>
    <div class="stat-sub">emails delivered</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Approved & Ready</div>
    <div class="stat-val" id="stat-ready">—</div>
    <div class="stat-sub">sends next cycle</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Call-Only Leads</div>
    <div class="stat-val" id="stat-calls">—</div>
    <div class="stat-sub">no email on file</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Awaiting Approval</div>
    <div class="stat-val" id="stat-pending">—</div>
    <div class="stat-sub">ready to review</div>
  </div>
</div>

<!-- TOOLBAR -->
<div class="toolbar">
  <button class="btn btn-secondary btn-sm" id="approval-toggle" onclick="toggleApproval()">...</button>
  <div class="toolbar-divider"></div>
  <button class="btn btn-secondary btn-sm" onclick="approveAll()">Approve All Pending</button>
</div>

<!-- LEADS TABLE -->
<div class="section">
  <div class="section-header">
    <div class="section-title" id="table-title">Leads</div>
    <div class="tab-group">
      <button class="tab active" onclick="showStage('pending')" id="tab-pending">Pending</button>
      <button class="tab" onclick="showStage('approved')" id="tab-approved">Approved</button>
      <button class="tab" onclick="showStage('sent')" id="tab-sent">Sent</button>
      <button class="tab" onclick="showStage('all')" id="tab-all">All</button>
    </div>
  </div>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>Business</th>
          <th>Type</th>
          <th>City</th>
          <th>Tier</th>
          <th>Score</th>
          <th>Email</th>
          <th>Status</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody id="leads-body">
        <tr><td colspan="8" class="empty">Loading...</td></tr>
      </tbody>
    </table>
  </div>
</div>

<!-- EMAIL PREVIEW MODAL -->
<div class="modal-bg" id="preview-modal" onclick="closeModal(event)">
  <div class="modal">
    <div class="modal-head">
      <div class="modal-title" id="preview-title">Email Preview</div>
      <button class="modal-close" onclick="closeModalDirect()">✕</button>
    </div>
    <div class="modal-tabs">
      <button class="modal-tab active" onclick="switchPreviewTab('html',event)">Preview</button>
      <button class="modal-tab" onclick="switchPreviewTab('plain',event)">Plain Text</button>
    </div>
    <div class="modal-body">
      <iframe class="preview-frame" id="preview-frame"></iframe>
      <pre class="plain-preview" id="preview-plain" style="display:none"></pre>
    </div>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
const FORGE_API_KEY = "{{FORGE_API_KEY}}";
function forgeHeaders(extra) {
  return Object.assign({"X-FORGE-API-Key": FORGE_API_KEY}, extra || {});
}
let currentStage = 'pending';
let statsData = {};

async function loadStats() {
  const r = await fetch('/api/stats', {headers: forgeHeaders()});
  statsData = await r.json();
  const n = statsData.nodes;

  document.getElementById('cnt-scrape').textContent   = n.scrape.count;
  document.getElementById('cnt-score').textContent    = n.score.count;
  document.getElementById('cnt-demo').textContent     = n.demo.count;
  document.getElementById('cnt-approve').textContent  = n.approve.count;
  document.getElementById('cnt-send').textContent     = n.send.count;
  document.getElementById('cnt-followup').textContent = n.followup.count;

  if (n.demo.warning) {
    const w = document.getElementById('warn-demo');
    w.textContent = n.demo.warning + ' need demos';
    w.style.display = 'block';
    document.getElementById('node-demo').classList.add('warning');
  }

  document.getElementById('stat-today').textContent   = statsData.emails_today;
  document.getElementById('stat-ready').textContent   = statsData.approved_ready;
  document.getElementById('stat-calls').textContent   = statsData.call_only;
  document.getElementById('stat-pending').textContent = statsData.pending_approval;

  const tm = statsData.test_mode;
  const badge = document.getElementById('mode-badge');
  badge.innerHTML = `<span class="dot"></span>${tm ? 'Test Mode' : 'Live'}`;
  badge.className = 'pill ' + (tm ? 'pill-red' : 'pill-green');

  const am = statsData.approval_mode;
  const ab = document.getElementById('approval-badge');
  ab.style.display = am ? 'inline-flex' : 'none';

  document.getElementById('approval-toggle').textContent =
    am ? '🔒 Approval Mode: On' : '🔓 Approval Mode: Off';
}

async function loadLeads(stage) {
  const r = await fetch('/api/leads?stage=' + stage, {headers: forgeHeaders()});
  const leads = await r.json();

  const titles = {pending:'Awaiting Approval', approved:'Approved — Ready to Send',
                  sent:'Sent', needs_demo:'Needs Demo Built', all:'All Leads'};
  document.getElementById('table-title').textContent = titles[stage] || 'Leads';

  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  const tabEl = document.getElementById('tab-' + stage);
  if (tabEl) tabEl.classList.add('active');

  const tbody = document.getElementById('leads-body');
  if (!leads.length) {
    tbody.innerHTML = '<tr><td colspan="8" class="empty">No leads in this stage</td></tr>';
    return;
  }

  tbody.innerHTML = leads.map(l => {
    const tier = l.lead_tier === 'HOT'
      ? '<span class="tier-hot">HOT</span>'
      : '<span class="tier-warm">WARM</span>';

    let statusChip = '<span class="chip chip-gray"><span class="dot"></span>Pending</span>';
    if ((l.email_sent||'').toLowerCase() === 'true')
      statusChip = '<span class="chip chip-green"><span class="dot"></span>Sent</span>';
    else if ((l.approved||'').toLowerCase() === 'true')
      statusChip = '<span class="chip chip-orange"><span class="dot"></span>Approved</span>';
    else if ((l.approved||'').toLowerCase() === 'rejected')
      statusChip = '<span class="chip chip-red"><span class="dot"></span>Rejected</span>';
    else if (!(l.demo_site_path||'').trim())
      statusChip = '<span class="chip chip-red"><span class="dot"></span>No Demo</span>';

    const canApprove = (l.email_sent||'').toLowerCase() !== 'true'
      && (l.approved||'').toLowerCase() !== 'true'
      && (l.approved||'').toLowerCase() !== 'rejected';

    const demoLink = l.demo_site_path
      ? `<a class="demo-link" href="${l.demo_site_path}" target="_blank">↗ view</a>` : '';

    const approveBtn = canApprove
      ? `<button class="btn btn-sm btn-approve" onclick="approveLead('${esc(l.business_name)}','approve')">Approve</button>
         <button class="btn btn-sm btn-reject" onclick="approveLead('${esc(l.business_name)}','reject')">Reject</button>` : '';

    const previewBtn = l.demo_site_path
      ? `<button class="btn btn-sm btn-secondary" onclick="previewEmail('${esc(l.business_name)}')">Preview Email</button>` : '';

    return `<tr>
      <td><span style="font-weight:500;color:#1d1d1f">${l.business_name||'—'}</span> ${demoLink}</td>
      <td style="color:var(--muted);font-size:12px;text-transform:capitalize">${(l.business_type||'—').replace(/_/g,' ')}</td>
      <td style="color:var(--muted);font-size:12px">${l.city||'—'}</td>
      <td>${tier}</td>
      <td style="font-weight:600;color:#1d1d1f">${l.score||'—'}</td>
      <td style="font-size:12px;color:var(--muted)">${(l.email||'').substring(0,28)||'—'}</td>
      <td>${statusChip}</td>
      <td><div class="actions">${approveBtn}${previewBtn}</div></td>
    </tr>`;
  }).join('');
}

function showStage(stage) {
  currentStage = stage;
  loadLeads(stage);
}

function esc(s) {
  return (s||'').replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

async function approveLead(name, action) {
  const r = await fetch('/api/approve', {
    method:'POST', headers:forgeHeaders({'Content-Type':'application/json'}),
    body: JSON.stringify({business_name: name, action})
  });
  const d = await r.json();
  if (d.ok) {
    showToast(action === 'approve' ? '✓ Approved: ' + name : '✗ Rejected: ' + name);
    loadLeads(currentStage);
    loadStats();
  }
}

async function approveAll() {
  const r = await fetch('/api/approve-all', {method:'POST', headers: forgeHeaders()});
  const d = await r.json();
  showToast('✓ Approved ' + d.approved + ' leads');
  loadLeads(currentStage);
  loadStats();
}

async function previewEmail(name) {
  document.getElementById('preview-title').textContent = 'Email Preview — ' + name;
  document.getElementById('preview-frame').srcdoc = '<p style="padding:20px;font-family:sans-serif;color:#666">Loading preview...</p>';
  document.getElementById('preview-modal').classList.add('open');

  const r = await fetch('/api/email-preview?name=' + encodeURIComponent(name), {headers: forgeHeaders()});
  const d = await r.json();
  document.getElementById('preview-frame').srcdoc = d.html || d.error;
  document.getElementById('preview-plain').textContent = d.plain || d.error;
}

function switchPreviewTab(tab, event) {
  document.querySelectorAll('.modal-tab').forEach(t => t.classList.remove('active'));
  event.target.classList.add('active');
  if (tab === 'html') {
    document.getElementById('preview-frame').style.display = 'block';
    document.getElementById('preview-plain').style.display = 'none';
  } else {
    document.getElementById('preview-frame').style.display = 'none';
    document.getElementById('preview-plain').style.display = 'block';
  }
}

function closeModal(e) {
  if (e.target === document.getElementById('preview-modal'))
    document.getElementById('preview-modal').classList.remove('open');
}
function closeModalDirect() {
  document.getElementById('preview-modal').classList.remove('open');
}

async function toggleTestMode() {
  await fetch('/api/toggle-test-mode', {method:'POST', headers: forgeHeaders()});
  loadStats();
  showToast('Test mode toggled');
}

async function toggleApproval() {
  await fetch('/api/toggle-approval-mode', {method:'POST', headers: forgeHeaders()});
  loadStats();
  showToast('Approval mode toggled');
}

async function runPipeline() {
  showToast('▶ Pipeline started — check scheduler.log for progress');
  await fetch('/api/run-pipeline', {method:'POST', headers: forgeHeaders()});
}

function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'toast show';
  clearTimeout(t._timer);
  t._timer = setTimeout(() => t.className = 'toast', 3000);
}

// Boot
loadStats();
loadLeads('pending');
setInterval(loadStats, 15000);
</script>
</body>
</html>"""


@app.route("/")
def index():
    ensure_approved_column()
    api_key = os.getenv("FORGE_API_KEY", "")
    html = DASHBOARD_HTML.replace("{{FORGE_API_KEY}}", api_key)
    return Response(html, mimetype="text/html")


if __name__ == "__main__":
    print("\n⚠️  FORGE Pipeline Dashboard — DEPRECATED, local dev only")
    print("   Not for production. Prefer /admin or TradeBuilt dashboard.")
    print("   Open: http://127.0.0.1:5050")
    if is_auth_enabled():
        print("   API routes require X-FORGE-API-Key (set FORGE_API_KEY in .env)\n")
    else:
        print("   WARNING: FORGE_API_KEY not set — API routes are unprotected\n")
    ensure_approved_column()
    app.run(host="127.0.0.1", port=5050, debug=False)
