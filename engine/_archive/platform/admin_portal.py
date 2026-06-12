"""
platform/admin_portal.py — FORGE Admin Dashboard (Task 8)
Password-protected internal command center. Replaces dashboard.py.
Handles: lead table, clients table, bookings, revenue chart, resellers tab,
pipeline trigger, and system log.
"""

import os
import sys
import csv
import json
import subprocess
import datetime
import traceback

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from flask import (
    Blueprint, request, session, redirect, url_for,
    render_template_string, jsonify, send_file, Response
)
from dotenv import load_dotenv
from system_logger import log

load_dotenv()

LEADS_CSV = os.path.join(BASE_DIR, "leads.csv")
CONVERSIONS_CSV = os.path.join(BASE_DIR, "conversions.csv")
BOOKINGS_FILE = os.path.join(BASE_DIR, "bookings.json")
SEND_LOG = os.path.join(BASE_DIR, "send_log.json")
LOG_FILE = os.path.join(BASE_DIR, "system_log.txt")
SITES_DIR = os.path.join(BASE_DIR, "sites")
WHITELABEL_CLIENTS_CSV = os.path.join(BASE_DIR, "whitelabel_clients.csv")
WHITELABEL_USAGE_FILE = os.path.join(BASE_DIR, "whitelabel_usage.json")
NOTIFICATIONS_FILE = os.path.join(BASE_DIR, "notifications.json")

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "forge_admin")
DAILY_EMAIL_LIMIT = 500

PLAN_AMOUNTS = {"starter": 200, "growth": 500, "autopilot": 800}

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# ─── DATA HELPERS ──────────────────────────────────────────────────────────────

def _read_csv(path: str) -> list:
    """Read a CSV file and return list of dicts."""
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r") as f:
            reader = csv.DictReader(f)
            return list(reader)
    except Exception:
        return []


def _read_leads() -> list:
    """Read and return all leads."""
    return _read_csv(LEADS_CSV)


def _read_conversions() -> list:
    """Read and return all conversions."""
    return _read_csv(CONVERSIONS_CSV)


def _read_bookings() -> list:
    """Read bookings.json."""
    if not os.path.exists(BOOKINGS_FILE):
        return []
    try:
        with open(BOOKINGS_FILE, "r") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _read_whitelabel_clients() -> list:
    """Read whitelabel reseller records."""
    return _read_csv(WHITELABEL_CLIENTS_CSV)


def _emails_today() -> int:
    """Count emails sent today from send_log.json."""
    if not os.path.exists(SEND_LOG):
        return 0
    try:
        with open(SEND_LOG) as f:
            data = json.load(f)
        today = datetime.date.today().isoformat()
        return data.get("count", 0) if data.get("date") == today else 0
    except Exception:
        return 0


def _compute_metrics() -> dict:
    """
    Compute the six overview metric values from live data.

    Returns:
        dict: Keys: total_leads, hot_pending, emails_today, daily_limit,
              clients, mrr, arr.
    """
    leads = _read_leads()
    conversions = _read_conversions()

    total_leads = len(leads)
    hot_pending = sum(
        1 for l in leads
        if l.get("lead_tier") == "HOT" and l.get("email_sent", "false") != "true"
    )
    emails_today = _emails_today()
    clients = len(conversions)

    mrr = 0
    for c in conversions:
        tier = c.get("tier", "").lower()
        if tier == "starter":
            pass  # one-time, not recurring
        else:
            mrr += PLAN_AMOUNTS.get(tier, 0)

    return {
        "total_leads": total_leads,
        "hot_pending": hot_pending,
        "emails_today": emails_today,
        "daily_limit": DAILY_EMAIL_LIMIT,
        "clients": clients,
        "mrr": mrr,
        "arr": mrr * 12,
    }


def _revenue_chart_data(days: int = 30) -> list:
    """
    Build 30-day revenue data from conversions.csv for Chart.js.

    Parameters:
        days (int): Number of days to include.

    Returns:
        list: [{"date": "YYYY-MM-DD", "amount": int}, ...] for each day.
    """
    today = datetime.date.today()
    buckets = {}
    for i in range(days - 1, -1, -1):
        d = (today - datetime.timedelta(days=i)).isoformat()
        buckets[d] = 0

    for c in _read_conversions():
        date = c.get("date", "")
        if date in buckets:
            try:
                buckets[date] += int(float(c.get("amount", 0)))
            except Exception:
                pass

    return [{"date": d, "amount": v} for d, v in buckets.items()]


def _log_lines(n: int = 80) -> list:
    """Return the last n lines from system_log.txt."""
    if not os.path.exists(LOG_FILE):
        return []
    try:
        with open(LOG_FILE, "r") as f:
            lines = f.readlines()
        return [l.rstrip() for l in lines[-n:]]
    except Exception:
        return []


# ─── AUTH HELPERS ──────────────────────────────────────────────────────────────

def _is_auth() -> bool:
    """Check admin session validity."""
    from .auth import is_admin_authenticated
    return is_admin_authenticated()


# ─── LOGIN / LOGOUT ────────────────────────────────────────────────────────────

@admin_bp.route("/", methods=["GET"])
def login_page():
    """Render admin login form or redirect to dashboard if authenticated."""
    if _is_auth():
        return redirect(url_for("admin.dashboard"))
    next_url = request.args.get("next", "")
    msg = request.args.get("msg", "")
    from .auth import generate_csrf_token
    return render_template_string(
        _LOGIN_HTML,
        message=msg,
        next_url=next_url,
        csrf_token=generate_csrf_token(),
    )


@admin_bp.route("/login", methods=["POST"])
def login():
    """Authenticate admin with password from .env."""
    password = request.form.get("password", "")
    next_url = request.form.get("next_url", "")
    if password == ADMIN_PASSWORD:
        from .auth import login_admin
        login_admin()
        log("admin_login", "SUCCESS", "Admin authenticated")
        return redirect(next_url or url_for("admin.dashboard"))
    log("admin_login", "WARNING", "Failed login attempt")
    from .auth import generate_csrf_token
    return render_template_string(
        _LOGIN_HTML,
        message="Incorrect password.",
        next_url=next_url,
        csrf_token=generate_csrf_token(),
    )


@admin_bp.route("/logout", methods=["GET"])
def logout():
    """Clear admin session."""
    from .auth import logout_admin
    logout_admin()
    return redirect(url_for("admin.login_page"))


# ─── DASHBOARD ─────────────────────────────────────────────────────────────────

@admin_bp.route("/dashboard", methods=["GET"])
def dashboard():
    """Main admin dashboard. Requires authentication."""
    if not _is_auth():
        return redirect(url_for("admin.login_page"))
    return render_template_string(_DASHBOARD_HTML)


# ─── API ROUTES ────────────────────────────────────────────────────────────────

@admin_bp.route("/api/stats", methods=["GET"])
def api_stats():
    """Return overview metric data as JSON."""
    if not _is_auth():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        return jsonify(_compute_metrics())
    except Exception as e:
        log("admin_api_stats", "ERROR", str(e))
        return jsonify({"error": "Failed to compute stats"}), 500


@admin_bp.route("/api/leads", methods=["GET"])
def api_leads():
    """Return leads as JSON with optional filtering."""
    if not _is_auth():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        leads = _read_leads()
        q = request.args.get("q", "").lower()
        tier = request.args.get("tier", "").upper()
        if q:
            leads = [l for l in leads if any(
                q in (l.get(f, "") or "").lower()
                for f in ["business_name", "city", "state", "email", "business_type"]
            )]
        if tier:
            leads = [l for l in leads if l.get("lead_tier", "").upper() == tier]
        return jsonify(leads)
    except Exception as e:
        log("admin_api_leads", "ERROR", str(e))
        return jsonify([])


@admin_bp.route("/api/clients", methods=["GET"])
def api_clients():
    """Return conversion records as JSON."""
    if not _is_auth():
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(_read_conversions())


@admin_bp.route("/api/bookings", methods=["GET"])
def api_bookings():
    """Return booking agent records as JSON."""
    if not _is_auth():
        return jsonify({"error": "Unauthorized"}), 401
    slug_filter = request.args.get("slug", "")
    bookings = _read_bookings()
    if slug_filter:
        bookings = [b for b in bookings if b.get("slug") == slug_filter]
    return jsonify(bookings)


@admin_bp.route("/api/revenue-chart", methods=["GET"])
def api_revenue_chart():
    """Return 30-day daily revenue data for Chart.js."""
    if not _is_auth():
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(_revenue_chart_data(30))


@admin_bp.route("/api/log", methods=["GET"])
def api_log():
    """Return the last 80 system log lines."""
    if not _is_auth():
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(_log_lines(80))


@admin_bp.route("/api/resellers", methods=["GET"])
def api_resellers():
    """Return white-label reseller records with usage data."""
    if not _is_auth():
        return jsonify({"error": "Unauthorized"}), 401
    clients = _read_whitelabel_clients()
    usage = {}
    if os.path.exists(WHITELABEL_USAGE_FILE):
        try:
            with open(WHITELABEL_USAGE_FILE, "r") as f:
                usage = json.load(f)
        except Exception:
            pass
    today = datetime.date.today().isoformat()
    for c in clients:
        fid = c.get("freelancer_id", "")
        c["calls_today"] = usage.get(f"{fid}:{today}", 0)
    return jsonify(clients)


@admin_bp.route("/api/notifications", methods=["GET"])
def api_notifications():
    """Return dashboard push notifications."""
    if not _is_auth():
        return jsonify({"error": "Unauthorized"}), 401
    if not os.path.exists(NOTIFICATIONS_FILE):
        return jsonify([])
    try:
        with open(NOTIFICATIONS_FILE, "r") as f:
            return jsonify(json.load(f))
    except Exception:
        return jsonify([])


@admin_bp.route("/api/run-pipeline", methods=["POST"])
def api_run_pipeline():
    """Trigger one agent pipeline cycle in the background."""
    if not _is_auth():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        subprocess.Popen(
            ["python3", "agent.py", "--once"],
            cwd=BASE_DIR,
            stdout=open(os.path.join(BASE_DIR, "agent_output.log"), "a"),
            stderr=subprocess.STDOUT,
        )
        log("admin_run_pipeline", "INFO", "Pipeline triggered from dashboard")
        return jsonify({"status": "started"})
    except Exception as e:
        log("admin_run_pipeline", "ERROR", str(e))
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/api/export-leads", methods=["GET"])
def api_export_leads():
    """Download leads.csv."""
    if not _is_auth():
        return jsonify({"error": "Unauthorized"}), 401
    if not os.path.exists(LEADS_CSV):
        return "No leads file found", 404
    return send_file(LEADS_CSV, as_attachment=True, download_name="leads.csv")


@admin_bp.route("/api/send-email/<slug>", methods=["POST"])
def api_send_email(slug: str):
    """
    Manually trigger outreach for a specific lead by slug.

    Parameters:
        slug (str): Business URL slug.
    """
    if not _is_auth():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        import re
        leads = _read_leads()
        target = None
        for lead in leads:
            name = lead.get("business_name", "")
            row_slug = re.sub(r"[^a-z0-9-]", "", name.lower().replace(" ", "-").replace("'", "").replace(",", ""))
            if row_slug == slug:
                target = lead
                break
        if not target:
            return jsonify({"error": "Lead not found"}), 404
        # Import and use the emailer
        from emailer import send_outreach_email
        result = send_outreach_email(target)
        return jsonify({"status": "sent" if result else "failed"})
    except Exception as e:
        log("admin_send_email", "ERROR", str(e)[:200])
        return jsonify({"error": str(e)}), 500


# ─── HTML TEMPLATES ────────────────────────────────────────────────────────────

_LOGIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>Admin Login — Forge</title>
  <link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet"/>
  <style>
    *,*::before,*::after{margin:0;padding:0;box-sizing:border-box;}
    body{background:#0a0a0a;color:#f5f5f0;font-family:'DM Sans',sans-serif;
    display:flex;align-items:center;justify-content:center;min-height:100vh;}
    .card{background:#111;border:1px solid rgba(255,255,255,0.07);padding:52px;max-width:400px;width:100%;}
    .brand{font-family:'DM Serif Display',serif;color:#c9a84c;font-size:1.2rem;margin-bottom:6px;}
    .brand-sub{font-size:0.62rem;letter-spacing:0.2em;text-transform:uppercase;color:#8a8a8a;display:block;margin-bottom:36px;}
    h2{font-family:'DM Serif Display',serif;font-weight:400;font-size:1.4rem;margin-bottom:24px;}
    label{display:block;font-size:0.62rem;letter-spacing:0.16em;text-transform:uppercase;color:#8a8a8a;margin-bottom:7px;}
    input{width:100%;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.1);
          color:#f5f5f0;padding:13px 16px;font-family:'DM Sans',sans-serif;font-size:0.9rem;}
    input:focus{outline:none;border-color:#c9a84c;}
    button{width:100%;background:#c9a84c;color:#0a0a0a;border:none;padding:15px;
           font-family:'DM Sans',sans-serif;font-size:0.78rem;font-weight:600;
           letter-spacing:0.08em;text-transform:uppercase;cursor:pointer;margin-top:20px;}
    button:hover{opacity:0.85;}
    .alert{background:rgba(255,80,80,0.07);border:1px solid rgba(255,80,80,0.15);
           padding:11px 15px;font-size:0.85rem;color:#ff8080;margin-bottom:18px;}
  </style>
</head>
<body>
  <div class="card">
    <div class="brand">Forge</div>
    <span class="brand-sub">Admin Access</span>
    <h2>Sign In</h2>
    {% if message %}<div class="alert">{{ message }}</div>{% endif %}
    <form method="POST" action="/admin/login">
      <input type="hidden" name="_csrf_token" value="{{ csrf_token }}"/>
      <input type="hidden" name="next_url" value="{{ next_url }}"/>
      <div style="margin-bottom:16px;">
        <label>Password</label>
        <input type="password" name="password" autofocus required/>
      </div>
      <button type="submit">Sign In</button>
    </form>
  </div>
</body>
</html>"""

_DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>Forge Admin</title>
  <link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet"/>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
  <style>
    :root{--bg:#0a0a0a;--surface:#111;--surface2:#161616;--border:rgba(255,255,255,0.07);
          --gold:#c9a84c;--text:#f5f5f0;--muted:#8a8a8a;--hot:#ef4444;--warm:#f59e0b;
          --green:#22c55e;--blue:#3b82f6;}
    *,*::before,*::after{margin:0;padding:0;box-sizing:border-box;}
    body{background:var(--bg);color:var(--text);font-family:'DM Sans',sans-serif;font-size:14px;min-height:100vh;}

    /* NAV */
    .nav{background:var(--surface);border-bottom:1px solid var(--border);
         padding:0 32px;display:flex;align-items:center;justify-content:space-between;height:56px;position:sticky;top:0;z-index:100;}
    .nav-brand{font-family:'DM Serif Display',serif;color:var(--gold);font-size:1.15rem;}
    .nav-links{display:flex;gap:4px;}
    .nav-link{padding:8px 14px;font-size:0.8rem;color:var(--muted);cursor:pointer;letter-spacing:0.04em;
               text-decoration:none;border:none;background:none;font-family:inherit;}
    .nav-link:hover,.nav-link.active{color:var(--text);}
    .nav-right{display:flex;align-items:center;gap:16px;}
    .nav-logout{font-size:0.72rem;color:var(--muted);text-decoration:none;letter-spacing:0.06em;text-transform:uppercase;}
    .nav-logout:hover{color:var(--text);}

    /* MAIN */
    .main{padding:32px;max-width:1440px;margin:0 auto;}

    /* SECTIONS */
    .section{display:none;}
    .section.active{display:block;}

    /* METRIC CARDS */
    .metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:28px;}
    @media(max-width:900px){.metrics{grid-template-columns:repeat(2,1fr);}}
    @media(max-width:560px){.metrics{grid-template-columns:1fr;}}
    .metric{background:var(--surface);border:1px solid var(--border);padding:24px;}
    .metric-val{font-family:'DM Serif Display',serif;font-size:2.4rem;color:var(--gold);line-height:1;}
    .metric-label{font-size:0.65rem;letter-spacing:0.14em;text-transform:uppercase;color:var(--muted);margin-top:6px;}
    .metric-sub{font-size:0.78rem;color:var(--muted);margin-top:4px;}

    /* CHART */
    .chart-card{background:var(--surface);border:1px solid var(--border);padding:28px;margin-bottom:28px;}
    .chart-card h3{font-family:'DM Serif Display',serif;font-size:1rem;font-weight:400;margin-bottom:20px;color:var(--muted);}
    .chart-wrap{height:220px;position:relative;}

    /* TABLES */
    .table-card{background:var(--surface);border:1px solid var(--border);margin-bottom:24px;}
    .table-header{padding:16px 20px;border-bottom:1px solid var(--border);
                  display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;}
    .table-title{font-size:0.75rem;letter-spacing:0.14em;text-transform:uppercase;color:var(--muted);}
    .table-wrap{overflow-x:auto;}
    table{width:100%;border-collapse:collapse;}
    th{padding:10px 16px;text-align:left;font-size:0.62rem;color:var(--muted);
       text-transform:uppercase;letter-spacing:0.12em;border-bottom:1px solid var(--border);
       white-space:nowrap;cursor:pointer;user-select:none;}
    th:hover{color:var(--text);}
    td{padding:11px 16px;border-bottom:1px solid rgba(255,255,255,0.04);font-size:0.85rem;white-space:nowrap;}
    tr:last-child td{border-bottom:none;}
    tr.hot-row{border-left:2px solid var(--gold);}
    tr.warm-row{border-left:2px solid var(--muted);}
    tr.sent-row{opacity:0.6;}
    tr:hover td{background:rgba(255,255,255,0.02);cursor:pointer;}
    .badge{display:inline-block;padding:2px 8px;font-size:0.68rem;font-weight:600;letter-spacing:0.06em;}
    .badge-hot{background:rgba(239,68,68,0.1);color:#ef4444;border:1px solid rgba(239,68,68,0.2);}
    .badge-warm{background:rgba(245,158,11,0.1);color:#f59e0b;border:1px solid rgba(245,158,11,0.2);}
    .badge-sent{background:rgba(34,197,94,0.1);color:#22c55e;border:1px solid rgba(34,197,94,0.2);}
    .badge-none{background:rgba(255,255,255,0.05);color:var(--muted);border:1px solid var(--border);}

    /* SEARCH */
    .search{background:rgba(255,255,255,0.04);border:1px solid var(--border);color:var(--text);
            padding:7px 12px;font-family:'DM Sans',sans-serif;font-size:0.82rem;width:220px;outline:none;}
    .search:focus{border-color:var(--gold);}

    /* BUTTONS */
    .btn{padding:8px 16px;border:1px solid var(--border);background:var(--surface);
         color:var(--text);cursor:pointer;font-family:'DM Sans',sans-serif;
         font-size:0.75rem;font-weight:500;letter-spacing:0.04em;text-decoration:none;display:inline-block;}
    .btn:hover{border-color:var(--gold);color:var(--gold);}
    .btn-primary{background:var(--gold);color:#0a0a0a;border-color:var(--gold);font-weight:600;}
    .btn-primary:hover{opacity:0.85;color:#0a0a0a;}
    .btn-sm{padding:5px 10px;font-size:0.7rem;}

    /* SIDE PANEL */
    .side-panel{position:fixed;right:-500px;top:0;width:460px;height:100vh;
                background:var(--surface2);border-left:1px solid var(--border);
                z-index:200;transition:right 0.28s ease;overflow-y:auto;padding:28px;}
    .side-panel.open{right:0;}
    .side-close{float:right;cursor:pointer;color:var(--muted);font-size:20px;
                background:none;border:none;color:var(--muted);}
    .side-close:hover{color:var(--text);}
    .side-field{margin-bottom:18px;}
    .side-label{font-size:0.6rem;letter-spacing:0.16em;text-transform:uppercase;color:var(--muted);margin-bottom:5px;}
    .side-value{font-size:0.9rem;color:var(--text);line-height:1.5;}
    .side-value a{color:var(--gold);text-decoration:none;}

    /* NOTIFICATION BANNER */
    #notif-bar{display:none;position:fixed;top:64px;left:50%;transform:translateX(-50%);
               background:var(--surface);border:1px solid var(--gold);padding:12px 24px;
               z-index:300;max-width:480px;width:90%;font-size:0.85rem;color:var(--gold);}

    /* LOG PANEL */
    .log-wrap{height:320px;overflow-y:auto;font-family:'SF Mono','Monaco',monospace;font-size:0.75rem;}
    .log-line{padding:5px 20px;border-bottom:1px solid rgba(255,255,255,0.03);line-height:1.5;}
    .log-success{color:var(--green);}
    .log-critical{color:var(--hot);background:rgba(239,68,68,0.05);}
    .log-info{color:var(--blue);}
    .log-warning{color:var(--warm);}
    .log-skip{color:#444;}

    /* CONTROLS BAR */
    .controls{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:24px;align-items:center;}
    .test-badge{padding:6px 12px;font-size:0.72rem;font-weight:600;border:1px solid;cursor:pointer;}
    .test-on{background:rgba(245,158,11,0.08);border-color:rgba(245,158,11,0.25);color:var(--warm);}
    .test-off{background:rgba(34,197,94,0.08);border-color:rgba(34,197,94,0.25);color:var(--green);}
  </style>
</head>
<body>

<div id="notif-bar"></div>

<!-- NAVIGATION -->
<nav class="nav">
  <div class="nav-brand">Forge</div>
  <div class="nav-links">
    <button class="nav-link active" onclick="showSection('overview', this)">Overview</button>
    <button class="nav-link" onclick="showSection('leads', this)">Leads</button>
    <button class="nav-link" onclick="showSection('clients', this)">Clients</button>
    <button class="nav-link" onclick="showSection('bookings', this)">Bookings</button>
    <button class="nav-link" onclick="showSection('resellers', this)">Resellers</button>
    <button class="nav-link" onclick="showSection('log', this)">Log</button>
  </div>
  <div class="nav-right">
    <a href="/admin/logout" class="nav-logout">Sign out</a>
  </div>
</nav>

<div class="main">

  <!-- ── OVERVIEW ─────────────────────────────────────────────────────── -->
  <div class="section active" id="section-overview">
    <div class="controls">
      <button class="btn btn-primary" onclick="runPipeline(this)">Run Pipeline</button>
      <div class="test-badge test-on" id="test-badge" onclick="toggleTestMode()">
        TEST MODE: <span id="test-mode-label">ON</span>
      </div>
      <a href="/admin/api/export-leads" class="btn">Export Leads CSV</a>
    </div>

    <div class="metrics" id="metrics-grid">
      <div class="metric"><div class="metric-val" id="m-leads">—</div><div class="metric-label">Total Leads</div></div>
      <div class="metric"><div class="metric-val" id="m-hot">—</div><div class="metric-label">HOT Leads Pending</div></div>
      <div class="metric"><div class="metric-val" id="m-emails">—</div><div class="metric-label">Emails Today</div><div class="metric-sub" id="m-emails-sub"></div></div>
      <div class="metric"><div class="metric-val" id="m-clients">—</div><div class="metric-label">Converted Clients</div></div>
      <div class="metric"><div class="metric-val" id="m-mrr">—</div><div class="metric-label">Monthly Recurring Revenue</div></div>
      <div class="metric"><div class="metric-val" id="m-arr">—</div><div class="metric-label">Annual Revenue Run Rate</div></div>
    </div>

    <div class="chart-card">
      <h3>30-Day Revenue</h3>
      <div class="chart-wrap"><canvas id="revenue-chart"></canvas></div>
    </div>
  </div>

  <!-- ── LEADS ─────────────────────────────────────────────────────────── -->
  <div class="section" id="section-leads">
    <div class="table-card">
      <div class="table-header">
        <span class="table-title">Leads</span>
        <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
          <input class="search" id="leads-search" placeholder="Search..." oninput="filterLeads(this.value)"/>
          <select class="search" style="width:auto;" id="tier-filter" onchange="filterLeads(document.getElementById('leads-search').value)">
            <option value="">All tiers</option>
            <option value="HOT">HOT</option>
            <option value="WARM">WARM</option>
          </select>
        </div>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th onclick="sortLeads('business_name')">Business</th>
              <th onclick="sortLeads('city')">City</th>
              <th onclick="sortLeads('state')">State</th>
              <th onclick="sortLeads('score')">Score</th>
              <th onclick="sortLeads('lead_tier')">Tier</th>
              <th onclick="sortLeads('website_url')">Website</th>
              <th onclick="sortLeads('email_sent')">Sent</th>
              <th onclick="sortLeads('reply_status')">Reply</th>
              <th onclick="sortLeads('date_scraped')">Scraped</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody id="leads-tbody">
            <tr><td colspan="10" style="text-align:center;padding:32px;color:var(--muted);">Loading...</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- ── CLIENTS ────────────────────────────────────────────────────────── -->
  <div class="section" id="section-clients">
    <div class="table-card">
      <div class="table-header">
        <span class="table-title">Converted Clients</span>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Business</th>
              <th>Tier</th>
              <th>Monthly Value</th>
              <th>Start Date</th>
              <th>Email</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody id="clients-tbody">
            <tr><td colspan="6" style="text-align:center;padding:32px;color:var(--muted);">Loading...</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- ── BOOKINGS ───────────────────────────────────────────────────────── -->
  <div class="section" id="section-bookings">
    <div class="table-card">
      <div class="table-header">
        <span class="table-title">Booking Agent Conversations</span>
        <input class="search" id="bookings-search" placeholder="Filter by business..." oninput="filterBookings(this.value)"/>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Business</th>
              <th>Visitor Name</th>
              <th>Phone</th>
              <th>Service Requested</th>
              <th>Outcome</th>
              <th>Timestamp</th>
            </tr>
          </thead>
          <tbody id="bookings-tbody">
            <tr><td colspan="6" style="text-align:center;padding:32px;color:var(--muted);">Loading...</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- ── RESELLERS ──────────────────────────────────────────────────────── -->
  <div class="section" id="section-resellers">
    <div style="margin-bottom:16px;display:flex;gap:10px;">
      <a href="/whitelabel" target="_blank" class="btn">View Registration Page</a>
    </div>
    <div class="table-card">
      <div class="table-header">
        <span class="table-title">White-Label Resellers</span>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Studio Name</th>
              <th>Email</th>
              <th>API Key (partial)</th>
              <th>Calls Today</th>
              <th>Status</th>
              <th>Since</th>
            </tr>
          </thead>
          <tbody id="resellers-tbody">
            <tr><td colspan="6" style="text-align:center;padding:32px;color:var(--muted);">Loading...</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- ── LOG ───────────────────────────────────────────────────────────── -->
  <div class="section" id="section-log">
    <div class="table-card">
      <div class="table-header">
        <span class="table-title">System Log</span>
        <button class="btn btn-sm" onclick="loadLog()">Refresh</button>
      </div>
      <div class="log-wrap" id="log-panel">
        <div class="log-line" style="color:var(--muted);">Loading...</div>
      </div>
    </div>
  </div>

</div><!-- /main -->

<!-- SIDE PANEL (lead detail) -->
<div class="side-panel" id="side-panel">
  <button class="side-close" onclick="closeSidePanel()">&#x2715;</button>
  <h3 style="font-family:'DM Serif Display',serif;font-weight:400;font-size:1.1rem;margin:0 0 24px;" id="side-title"></h3>
  <div id="side-content"></div>
</div>

<script>
// ── NAV ─────────────────────────────────────────────────────────────────────
var currentSection = 'overview';
function showSection(name, btn) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.nav-link').forEach(b => b.classList.remove('active'));
  document.getElementById('section-' + name).classList.add('active');
  if (btn) btn.classList.add('active');
  currentSection = name;
  if (name === 'leads' && !window._leadsLoaded) loadLeads();
  if (name === 'clients') loadClients();
  if (name === 'bookings') loadBookings();
  if (name === 'resellers') loadResellers();
  if (name === 'log') loadLog();
}

// ── STATS ────────────────────────────────────────────────────────────────────
async function loadStats() {
  const r = await fetch('/admin/api/stats');
  const s = await r.json();
  document.getElementById('m-leads').textContent = s.total_leads || 0;
  document.getElementById('m-hot').textContent = s.hot_pending || 0;
  document.getElementById('m-emails').textContent = (s.emails_today || 0);
  document.getElementById('m-emails-sub').textContent = '/ ' + (s.daily_limit || 500) + ' limit';
  document.getElementById('m-clients').textContent = s.clients || 0;
  document.getElementById('m-mrr').textContent = '$' + (s.mrr || 0).toLocaleString();
  document.getElementById('m-arr').textContent = '$' + (s.arr || 0).toLocaleString();
  loadTestMode();
}

// ── REVENUE CHART ────────────────────────────────────────────────────────────
var revenueChart = null;
async function loadChart() {
  const r = await fetch('/admin/api/revenue-chart');
  const data = await r.json();
  const labels = data.map(d => d.date.slice(5));
  const values = data.map(d => d.amount);
  const ctx = document.getElementById('revenue-chart').getContext('2d');
  if (revenueChart) revenueChart.destroy();
  revenueChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        data: values,
        backgroundColor: 'rgba(201,168,76,0.4)',
        borderColor: '#c9a84c',
        borderWidth: 1,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#8a8a8a', font: { size: 10 } } },
        y: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#8a8a8a', font: { size: 10 },
             callback: v => '$' + v } }
      }
    }
  });
}

// ── LEADS ────────────────────────────────────────────────────────────────────
var allLeads = [], leadsSort = { field: 'score', dir: -1 };
async function loadLeads() {
  const r = await fetch('/admin/api/leads');
  allLeads = await r.json();
  window._leadsLoaded = true;
  renderLeads(allLeads);
}
function filterLeads(q) {
  q = q.toLowerCase();
  var tier = document.getElementById('tier-filter').value;
  var filtered = allLeads.filter(l => {
    var matchQ = !q || ['business_name','city','state','email','business_type'].some(
      f => (l[f]||'').toLowerCase().includes(q));
    var matchT = !tier || (l.lead_tier||'').toUpperCase() === tier;
    return matchQ && matchT;
  });
  renderLeads(filtered);
}
function sortLeads(field) {
  if (leadsSort.field === field) leadsSort.dir *= -1;
  else { leadsSort.field = field; leadsSort.dir = 1; }
  filterLeads(document.getElementById('leads-search').value);
}
function renderLeads(leads) {
  leads = [...leads].sort((a, b) => {
    var av = a[leadsSort.field] || '', bv = b[leadsSort.field] || '';
    if (leadsSort.field === 'score') { av = +av; bv = +bv; }
    return av < bv ? -leadsSort.dir : av > bv ? leadsSort.dir : 0;
  });
  var tbody = document.getElementById('leads-tbody');
  if (!leads.length) { tbody.innerHTML = '<tr><td colspan="10" style="text-align:center;padding:28px;color:var(--muted);">No leads</td></tr>'; return; }
  tbody.innerHTML = leads.map(l => {
    var tier = l.lead_tier || '';
    var sent = l.email_sent === 'true';
    var slug = (l.business_name||'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/'/g,'');
    var rowCls = tier==='HOT'?'hot-row':tier==='WARM'?'warm-row':'';
    if (sent) rowCls += ' sent-row';
    return `<tr class="${rowCls}" onclick="showLeadDetail(${JSON.stringify(l).replace(/"/g,'&quot;')})">
      <td style="max-width:180px;overflow:hidden;text-overflow:ellipsis;">${esc(l.business_name||'')}</td>
      <td>${esc(l.city||'')}</td><td>${esc(l.state||'')}</td>
      <td style="font-weight:600;">${l.score||''}</td>
      <td><span class="badge badge-${tier==='HOT'?'hot':tier==='WARM'?'warm':'none'}">${tier||'—'}</span></td>
      <td>${l.website_url?'<span style="color:var(--green);">Yes</span>':'<span style="color:var(--muted);">None</span>'}</td>
      <td>${sent?'<span style="color:var(--green);">Sent</span>':'<span style="color:var(--muted);">—</span>'}</td>
      <td>${l.reply_status&&l.reply_status!=='none'?'<span class="badge badge-sent">'+esc(l.reply_status)+'</span>':'<span style="color:var(--muted);">—</span>'}</td>
      <td style="color:var(--muted);">${l.date_scraped||''}</td>
      <td onclick="event.stopPropagation()">
        ${l.demo_site_path?`<a href="${esc(l.demo_site_path)}" target="_blank" class="btn btn-sm" style="margin-right:4px;">Demo</a>`:''}
        <button class="btn btn-sm" onclick="sendEmail('${slug}', this)">Send</button>
      </td>
    </tr>`;
  }).join('');
}

async function sendEmail(slug, btn) {
  btn.textContent = '...';
  btn.disabled = true;
  try {
    const r = await fetch('/admin/api/send-email/' + slug, {method:'POST',headers:{'X-CSRF-Token': getCsrf()}});
    const d = await r.json();
    btn.textContent = d.status === 'sent' ? 'Sent' : 'Failed';
  } catch(e) { btn.textContent = 'Error'; }
}

// ── SIDE PANEL ───────────────────────────────────────────────────────────────
function showLeadDetail(l) {
  document.getElementById('side-title').textContent = l.business_name || 'Lead';
  var fields = [
    ['Business Type', l.business_type], ['City', l.city], ['State', l.state],
    ['Score', l.score], ['Tier', l.lead_tier], ['Phone', l.phone], ['Email', l.email],
    ['Website', l.website_url ? `<a href="${l.website_url}" target="_blank">${l.website_url}</a>` : '—'],
    ['Demo', l.demo_site_path ? `<a href="${l.demo_site_path}" target="_blank">View Demo</a>` : '—'],
    ['Rating', l.google_rating], ['Reviews', l.review_count],
    ['Email Sent', l.email_sent], ['Sent Date', l.email_sent_date],
    ['Reply Status', l.reply_status], ['Converted', l.converted],
    ['Plan', l.plan_tier], ['Date Scraped', l.date_scraped],
  ];
  document.getElementById('side-content').innerHTML = fields.filter(([_,v])=>v).map(([label,val])=>
    `<div class="side-field"><div class="side-label">${label}</div><div class="side-value">${val}</div></div>`
  ).join('');
  document.getElementById('side-panel').classList.add('open');
}
function closeSidePanel() { document.getElementById('side-panel').classList.remove('open'); }

// ── CLIENTS ──────────────────────────────────────────────────────────────────
async function loadClients() {
  const r = await fetch('/admin/api/clients');
  const clients = await r.json();
  var amounts = {starter:200,growth:500,autopilot:800};
  var tbody = document.getElementById('clients-tbody');
  if (!clients.length) { tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:28px;color:var(--muted);">No clients yet</td></tr>'; return; }
  tbody.innerHTML = clients.map(c => {
    var tier = c.tier||'';
    var amt = tier==='starter'?'$200 one-time':'$'+(amounts[tier]||0)+'/mo';
    return `<tr>
      <td>${esc(c.business_name||'')}</td>
      <td><span class="badge badge-hot">${tier}</span></td>
      <td>${amt}</td>
      <td style="color:var(--muted);">${c.date||''}</td>
      <td><a href="mailto:${esc(c.email||'')}" style="color:var(--gold);">${esc(c.email||'')}</a></td>
      <td><a href="/portal" target="_blank" class="btn btn-sm">Portal</a></td>
    </tr>`;
  }).join('');
}

// ── BOOKINGS ─────────────────────────────────────────────────────────────────
var allBookings = [];
async function loadBookings() {
  const r = await fetch('/admin/api/bookings');
  allBookings = await r.json();
  renderBookings(allBookings);
}
function filterBookings(q) {
  q = q.toLowerCase();
  renderBookings(allBookings.filter(b => !q || (b.slug||'').includes(q) || (b.visitor_name||'').toLowerCase().includes(q)));
}
function renderBookings(bookings) {
  var tbody = document.getElementById('bookings-tbody');
  if (!bookings.length) { tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:28px;color:var(--muted);">No bookings yet</td></tr>'; return; }
  tbody.innerHTML = bookings.slice().reverse().map(b => `<tr>
    <td>${esc(b.slug||'')}</td>
    <td>${esc(b.visitor_name||'—')}</td>
    <td>${esc(b.visitor_phone||'—')}</td>
    <td>${esc(b.service_requested||'—')}</td>
    <td><span class="badge badge-sent">${esc(b.outcome||'')}</span></td>
    <td style="color:var(--muted);">${(b.timestamp||'').slice(0,16).replace('T',' ')}</td>
  </tr>`).join('');
}

// ── RESELLERS ────────────────────────────────────────────────────────────────
async function loadResellers() {
  const r = await fetch('/admin/api/resellers');
  const resellers = await r.json();
  var tbody = document.getElementById('resellers-tbody');
  if (!resellers.length) { tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:28px;color:var(--muted);">No resellers yet. <a href="/whitelabel" style="color:var(--gold);">View registration page</a></td></tr>'; return; }
  tbody.innerHTML = resellers.map(r => `<tr>
    <td>${esc(r.business_name||'')}</td>
    <td><a href="mailto:${esc(r.email||'')}" style="color:var(--gold);">${esc(r.email||'')}</a></td>
    <td style="font-family:monospace;font-size:0.78rem;color:var(--muted);">${(r.api_key||'').slice(0,12)}...</td>
    <td>${r.calls_today||0} / 100</td>
    <td><span class="badge ${r.status==='active'?'badge-sent':'badge-none'}">${esc(r.status||'')}</span></td>
    <td style="color:var(--muted);">${r.created_date||''}</td>
  </tr>`).join('');
}

// ── LOG ──────────────────────────────────────────────────────────────────────
async function loadLog() {
  const r = await fetch('/admin/api/log');
  const lines = await r.json();
  var panel = document.getElementById('log-panel');
  panel.innerHTML = lines.slice().reverse().map(line => {
    var cls = 'log-default';
    if (line.includes('[SUCCESS]')) cls = 'log-success';
    else if (line.includes('[CRITICAL]')) cls = 'log-critical';
    else if (line.includes('[INFO]')) cls = 'log-info';
    else if (line.includes('[WARNING]')) cls = 'log-warning';
    else if (line.includes('[SKIP]')) cls = 'log-skip';
    return `<div class="log-line ${cls}">${esc(line)}</div>`;
  }).join('');
}

// ── TEST MODE ────────────────────────────────────────────────────────────────
async function loadTestMode() {
  try {
    const r = await fetch('/api/test-mode');
    const d = await r.json();
    var badge = document.getElementById('test-badge');
    var label = document.getElementById('test-mode-label');
    if (d.test_mode) { badge.className='test-badge test-on'; label.textContent='ON'; }
    else { badge.className='test-badge test-off'; label.textContent='OFF'; }
  } catch(e) {}
}
async function toggleTestMode() {
  await fetch('/api/toggle-test-mode', {method:'POST',headers:{'X-CSRF-Token':getCsrf()}});
  loadTestMode();
}

// ── PIPELINE ─────────────────────────────────────────────────────────────────
async function runPipeline(btn) {
  btn.textContent = 'Running...';
  btn.disabled = true;
  try {
    const r = await fetch('/admin/api/run-pipeline', {method:'POST',headers:{'X-CSRF-Token':getCsrf()}});
    const d = await r.json();
    btn.textContent = d.status === 'started' ? 'Pipeline Started' : 'Error';
    setTimeout(() => { btn.textContent = 'Run Pipeline'; btn.disabled = false; }, 4000);
  } catch(e) { btn.textContent = 'Error'; btn.disabled = false; }
}

// ── NOTIFICATIONS ────────────────────────────────────────────────────────────
var lastNotifTs = '';
async function checkNotifications() {
  try {
    const r = await fetch('/admin/api/notifications');
    const notifs = await r.json();
    if (!notifs.length) return;
    var last = notifs[notifs.length - 1];
    if (last.ts === lastNotifTs) return;
    lastNotifTs = last.ts;
    var bar = document.getElementById('notif-bar');
    bar.textContent = last.message;
    bar.style.display = 'block';
    setTimeout(() => bar.style.display = 'none', 7000);
  } catch(e) {}
}

// ── UTILS ────────────────────────────────────────────────────────────────────
function esc(s) {
  return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function getCsrf() {
  var m = document.cookie.match(/csrf_token=([^;]+)/);
  return m ? m[1] : '';
}

// ── TEST MODE ROUTES (pass-through from old dashboard.py) ────────────────────
// These routes are registered at the root level in app.py via the API.
// We proxy them here to the admin API.
async function apiTestMode(method) {
  return fetch(method === 'GET' ? '/api/test-mode' : '/api/toggle-test-mode',
    {method, headers: {'X-CSRF-Token': getCsrf()}});
}

// ── INIT ────────────────────────────────────────────────────────────────────
loadStats();
loadChart();
loadLeads();
checkNotifications();
setInterval(() => { if (currentSection==='overview') { loadStats(); loadChart(); } checkNotifications(); }, 60000);
</script>
</body>
</html>"""


# ─── TEST MODE API (compatibility with old dashboard.py) ───────────────────────
# These routes are registered on the main app, not the admin blueprint, because
# the old dashboard.py had them at root level. We register them on the admin
# blueprint with /api prefix to avoid conflicts.

@admin_bp.route("/api-test-mode", methods=["GET"])
def api_test_mode():
    """Return current TEST_MODE state."""
    if not _is_auth():
        return jsonify({"error": "Unauthorized"}), 401
    from dotenv import dotenv_values
    env = dotenv_values(os.path.join(BASE_DIR, ".env"))
    return jsonify({"test_mode": env.get("TEST_MODE", "true").lower() == "true"})
