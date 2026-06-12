"""
dashboard.py — TradeBuilt Command Center

DEPRECATED (Phase 1): Superseded by platform/admin_portal.py. Do not use.
Local Flask dashboard. Run: python3 dashboard.py
Open: http://localhost:8080
"""

import csv
import json
import os
import subprocess
import datetime
from flask import Flask, jsonify, send_file, request, Response
from dotenv import load_dotenv

load_dotenv()

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LEADS_CSV = os.path.join(SCRIPT_DIR, "leads.csv")
LOG_FILE = os.path.join(SCRIPT_DIR, "system_log.txt")
SEND_LOG = os.path.join(SCRIPT_DIR, "send_log.json")
NOTIF_FILE = os.path.join(SCRIPT_DIR, "notifications.json")
SITES_DIR = os.path.join(SCRIPT_DIR, "sites")

app = Flask(__name__)


# ─── DATA HELPERS ─────────────────────────────────────────────────────────────

def read_leads() -> list:
    if not os.path.exists(LEADS_CSV):
        return []
    with open(LEADS_CSV, "r") as f:
        reader = csv.DictReader(f)
        return list(reader)


def count_sites() -> int:
    if not os.path.exists(SITES_DIR):
        return 0
    return len([f for f in os.listdir(SITES_DIR) if f.endswith(".html")])


def emails_today() -> int:
    if not os.path.exists(SEND_LOG):
        return 0
    with open(SEND_LOG) as f:
        data = json.load(f)
    today = datetime.date.today().isoformat()
    return data.get("count", 0) if data.get("date") == today else 0


def get_notifications() -> list:
    if not os.path.exists(NOTIF_FILE):
        return []
    with open(NOTIF_FILE) as f:
        return json.load(f)


def get_log_lines(n=50) -> list:
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE) as f:
        lines = f.readlines()
    return [l.rstrip() for l in lines[-n:]]


# ─── ROUTES ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return Response(DASHBOARD_HTML, mimetype="text/html")


@app.route("/api/stats")
def api_stats():
    leads = read_leads()
    hot = sum(1 for l in leads if l.get("lead_tier") == "HOT")
    warm = sum(1 for l in leads if l.get("lead_tier") == "WARM")
    replies = sum(1 for l in leads if l.get("reply_status", "none") not in ("none", ""))
    sent_today = emails_today()
    sites = count_sites()
    return jsonify({
        "total_leads": len(leads),
        "emails_today": sent_today,
        "daily_limit": 50,
        "hot_leads": hot,
        "warm_leads": warm,
        "replies": replies,
        "sites_built": sites,
        "revenue_pipeline": replies * 200,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })


@app.route("/api/leads")
def api_leads():
    leads = read_leads()
    # Support query params: q (search), tier, state
    q = request.args.get("q", "").lower()
    tier = request.args.get("tier", "").upper()
    if q:
        leads = [l for l in leads if
                 q in (l.get("business_name", "")).lower() or
                 q in (l.get("city", "")).lower() or
                 q in (l.get("state", "")).lower()]
    if tier:
        leads = [l for l in leads if l.get("lead_tier") == tier]
    return jsonify(leads)


@app.route("/api/log")
def api_log():
    return jsonify(get_log_lines(50))


@app.route("/api/notifications")
def api_notifications():
    return jsonify(get_notifications())


@app.route("/api/export")
def api_export():
    if not os.path.exists(LEADS_CSV):
        return "No leads.csv found", 404
    return send_file(LEADS_CSV, as_attachment=True, download_name="leads.csv")


@app.route("/api/run-pipeline", methods=["POST"])
def api_run_pipeline():
    """Trigger one pipeline cycle in the background."""
    try:
        subprocess.Popen(
            ["python3", "agent.py", "--once"],
            cwd=SCRIPT_DIR,
            stdout=open(os.path.join(SCRIPT_DIR, "agent_output.log"), "a"),
            stderr=subprocess.STDOUT,
        )
        return jsonify({"status": "started", "message": "Pipeline cycle triggered"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/toggle-test-mode", methods=["POST"])
def api_toggle_test_mode():
    """Toggle TEST_MODE in .env file."""
    env_path = os.path.join(SCRIPT_DIR, ".env")
    if not os.path.exists(env_path):
        return jsonify({"error": ".env not found"}), 404
    with open(env_path, "r") as f:
        lines = f.readlines()
    new_lines = []
    current_mode = None
    for line in lines:
        if line.startswith("TEST_MODE="):
            current = line.strip().split("=", 1)[1].lower()
            current_mode = current == "true"
            new_val = "false" if current_mode else "true"
            new_lines.append(f"TEST_MODE={new_val}\n")
        else:
            new_lines.append(line)
    with open(env_path, "w") as f:
        f.writelines(new_lines)
    new_mode = not current_mode if current_mode is not None else True
    return jsonify({"test_mode": new_mode})


@app.route("/api/test-mode")
def api_test_mode():
    from dotenv import dotenv_values
    env = dotenv_values(os.path.join(SCRIPT_DIR, ".env"))
    return jsonify({"test_mode": env.get("TEST_MODE", "true").lower() == "true"})


# ─── DASHBOARD HTML ───────────────────────────────────────────────────────────

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TradeBuilt Command Center</title>
<style>
  :root {
    --bg: #0f0f0f;
    --surface: #1a1a1a;
    --border: #2a2a2a;
    --gold: #FFD700;
    --text: #e8e8e8;
    --muted: #888;
    --hot: #ef4444;
    --warm: #f59e0b;
    --success: #22c55e;
    --info: #3b82f6;
    --font: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  }
  * { margin:0; padding:0; box-sizing:border-box; }
  body { background:var(--bg); color:var(--text); font-family:var(--font); font-size:14px; }

  /* HEADER */
  .header { background:#111; border-bottom:1px solid var(--border); padding:16px 24px; display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:12px; position:sticky; top:0; z-index:100; }
  .header-left { display:flex; align-items:center; gap:16px; }
  .logo { font-size:28px; font-weight:bold; color:var(--gold); letter-spacing:-0.02em; line-height:1; }
  .logo-sub { font-size:11px; color:var(--muted); letter-spacing:0.15em; text-transform:uppercase; }
  .header-title { font-size:15px; font-weight:600; color:var(--text); }
  .header-right { display:flex; align-items:center; gap:16px; flex-wrap:wrap; }
  .clock { font-size:13px; color:var(--muted); font-variant-numeric:tabular-nums; }
  .status-badge { display:inline-flex; align-items:center; gap:6px; background:#1a2a1a; border:1px solid #22c55e40; color:#22c55e; padding:6px 12px; border-radius:100px; font-size:12px; font-weight:600; }
  .status-dot { width:7px; height:7px; background:#22c55e; border-radius:50%; animation:pulse 2s infinite; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }

  /* MAIN */
  .main { padding:24px; max-width:1400px; margin:0 auto; }

  /* STAT CARDS */
  .stats-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:16px; margin-bottom:28px; }
  .stat-card { background:var(--surface); border:1px solid var(--border); border-radius:8px; padding:20px; }
  .stat-label { font-size:11px; color:var(--muted); text-transform:uppercase; letter-spacing:0.12em; margin-bottom:8px; }
  .stat-value { font-size:28px; font-weight:700; color:var(--text); line-height:1; }
  .stat-sub { font-size:11px; color:var(--muted); margin-top:4px; }
  .stat-card.gold .stat-value { color:var(--gold); }
  .stat-card.hot .stat-value { color:var(--hot); }
  .stat-card.warm .stat-value { color:var(--warm); }
  .stat-card.green .stat-value { color:var(--success); }

  /* NOTIFICATION BANNER */
  #notif-banner { display:none; position:fixed; top:70px; left:50%; transform:translateX(-50%); background:#1a1a1a; border:1px solid var(--gold); color:var(--text); padding:12px 24px; border-radius:6px; z-index:200; max-width:500px; width:90%; font-size:14px; box-shadow:0 4px 20px rgba(0,0,0,0.5); }
  #notif-banner .notif-close { float:right; cursor:pointer; color:var(--muted); margin-left:16px; }

  /* CONTROLS */
  .controls { display:flex; gap:12px; flex-wrap:wrap; margin-bottom:28px; }
  .btn { padding:10px 18px; border-radius:6px; border:1px solid var(--border); background:var(--surface); color:var(--text); cursor:pointer; font-size:13px; font-weight:500; transition:all 0.2s; }
  .btn:hover { border-color:var(--gold); color:var(--gold); }
  .btn.primary { background:var(--gold); color:#000; border-color:var(--gold); font-weight:700; }
  .btn.primary:hover { opacity:0.85; }
  .test-mode-indicator { display:inline-flex; align-items:center; gap:8px; padding:8px 14px; border-radius:6px; border:1px solid; font-size:12px; font-weight:600; }
  .test-mode-on { background:#1a1a00; border-color:#f59e0b40; color:#f59e0b; }
  .test-mode-off { background:#001a00; border-color:#22c55e40; color:#22c55e; }

  /* TWO COL LAYOUT */
  .two-col { display:grid; grid-template-columns:1fr 380px; gap:24px; margin-bottom:28px; }
  @media (max-width:1000px) { .two-col { grid-template-columns:1fr; } }

  /* LEAD TABLE */
  .card { background:var(--surface); border:1px solid var(--border); border-radius:8px; overflow:hidden; }
  .card-header { padding:16px 20px; border-bottom:1px solid var(--border); display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap; }
  .card-title { font-size:14px; font-weight:600; }
  .search-input { background:#111; border:1px solid var(--border); color:var(--text); padding:7px 12px; border-radius:5px; font-size:13px; width:200px; outline:none; }
  .search-input:focus { border-color:var(--gold); }
  .table-wrap { overflow-x:auto; }
  table { width:100%; border-collapse:collapse; }
  th { padding:10px 14px; text-align:left; font-size:11px; color:var(--muted); text-transform:uppercase; letter-spacing:0.1em; border-bottom:1px solid var(--border); white-space:nowrap; }
  td { padding:11px 14px; border-bottom:1px solid #1f1f1f; font-size:13px; white-space:nowrap; }
  tr:last-child td { border-bottom:none; }
  tr:hover td { background:#1f1f1f; cursor:pointer; }
  .badge { display:inline-block; padding:3px 8px; border-radius:4px; font-size:11px; font-weight:600; }
  .badge-hot { background:#2a0a0a; color:#ef4444; border:1px solid #ef444430; }
  .badge-warm { background:#2a1800; color:#f59e0b; border:1px solid #f59e0b30; }
  .badge-sent { background:#001a0a; color:#22c55e; border:1px solid #22c55e30; }
  .badge-none { background:#1a1a1a; color:#888; border:1px solid #2a2a2a; }

  /* LOG PANEL */
  .log-panel { height:100%; max-height:500px; overflow-y:auto; }
  .log-line { padding:7px 16px; font-size:11px; font-family:'SF Mono', 'Monaco', monospace; border-bottom:1px solid #1f1f1f; line-height:1.5; }
  .log-success { color:#22c55e; }
  .log-critical { color:#ef4444; background:#1a0000; }
  .log-skip { color:#555; }
  .log-info { color:#3b82f6; }
  .log-warning { color:#f59e0b; }
  .log-default { color:#888; }

  /* SIDE PANEL */
  .side-panel { position:fixed; right:-480px; top:0; width:460px; height:100vh; background:#111; border-left:1px solid var(--border); z-index:300; transition:right 0.3s ease; overflow-y:auto; padding:24px; }
  .side-panel.open { right:0; }
  .side-close { cursor:pointer; color:var(--muted); font-size:20px; float:right; }
  .side-field { margin-bottom:18px; }
  .side-label { font-size:11px; color:var(--muted); text-transform:uppercase; letter-spacing:0.1em; margin-bottom:5px; }
  .side-value { font-size:14px; color:var(--text); }
  .side-value a { color:var(--gold); text-decoration:none; }

  /* RESPONSIVE */
  @media (max-width:600px) { .header { padding:12px 16px; } .main { padding:16px; } .stats-grid { grid-template-columns:repeat(2,1fr); } }
</style>
</head>
<body>

<div id="notif-banner">
  <span id="notif-text"></span>
  <span class="notif-close" onclick="this.parentElement.style.display='none'">✕</span>
</div>

<!-- HEADER -->
<div class="header">
  <div class="header-left">
    <div>
      <div class="logo">RR</div>
    </div>
    <div>
      <div class="header-title">TradeBuilt Command Center</div>
      <div style="font-size:11px;color:var(--muted);margin-top:2px;">Lead Generation Engine</div>
    </div>
  </div>
  <div class="header-right">
    <span class="clock" id="clock">Loading...</span>
    <span class="status-badge"><span class="status-dot"></span>AGENT RUNNING</span>
  </div>
</div>

<!-- MAIN -->
<div class="main">

  <!-- STAT CARDS -->
  <div class="stats-grid" id="stats-grid">
    <div class="stat-card gold">
      <div class="stat-label">Total Leads</div>
      <div class="stat-value" id="s-total">—</div>
      <div class="stat-sub">all time</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Emails Today</div>
      <div class="stat-value" id="s-emails">—</div>
      <div class="stat-sub" id="s-emails-sub">/ 50 limit</div>
    </div>
    <div class="stat-card hot">
      <div class="stat-label">HOT Leads</div>
      <div class="stat-value" id="s-hot">—</div>
      <div class="stat-sub">score ≥ 14</div>
    </div>
    <div class="stat-card warm">
      <div class="stat-label">WARM Leads</div>
      <div class="stat-value" id="s-warm">—</div>
      <div class="stat-sub">score 8–13</div>
    </div>
    <div class="stat-card green">
      <div class="stat-label">Replies</div>
      <div class="stat-value" id="s-replies">—</div>
      <div class="stat-sub">reply_status set</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Sites Built</div>
      <div class="stat-value" id="s-sites">—</div>
      <div class="stat-sub">in /sites/</div>
    </div>
    <div class="stat-card gold">
      <div class="stat-label">Revenue Pipeline</div>
      <div class="stat-value" id="s-revenue">—</div>
      <div class="stat-sub">$200 × replies</div>
    </div>
  </div>

  <!-- CONTROLS -->
  <div class="controls">
    <button class="btn primary" onclick="runPipeline()">▶ Run Pipeline Now</button>
    <div class="test-mode-indicator" id="test-mode-badge" onclick="toggleTestMode()" style="cursor:pointer;">
      TEST MODE: <span id="test-mode-label">ON</span>
    </div>
    <button class="btn" onclick="window.location='/api/export'">⬇ Export Leads CSV</button>
    <button class="btn" onclick="loadLeads()">↻ Refresh Table</button>
  </div>

  <!-- LEAD TABLE + LOG PANEL -->
  <div class="two-col">
    <!-- Lead Table -->
    <div class="card">
      <div class="card-header">
        <span class="card-title">Leads</span>
        <input class="search-input" id="lead-search" placeholder="Search city, state, name..." oninput="filterLeads(this.value)">
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Business</th>
              <th>City</th>
              <th>State</th>
              <th>Score</th>
              <th>Tier</th>
              <th>Sent</th>
              <th>Reply</th>
              <th>Date</th>
            </tr>
          </thead>
          <tbody id="leads-tbody">
            <tr><td colspan="8" style="text-align:center;padding:32px;color:var(--muted);">Loading...</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Activity Log -->
    <div class="card">
      <div class="card-header">
        <span class="card-title">Activity Log</span>
        <span style="font-size:11px;color:var(--muted);">last 50 lines</span>
      </div>
      <div class="log-panel" id="log-panel">
        <div class="log-line log-default">Loading...</div>
      </div>
    </div>
  </div>
</div>

<!-- SIDE PANEL (lead detail) -->
<div class="side-panel" id="side-panel">
  <span class="side-close" onclick="closeSidePanel()">✕</span>
  <h3 style="margin-bottom:24px;color:var(--gold);" id="side-title">Lead Detail</h3>
  <div id="side-content"></div>
</div>

<script>
  let allLeads = [];

  // Clock
  function updateClock() {
    document.getElementById('clock').textContent = new Date().toLocaleString();
  }
  setInterval(updateClock, 1000);
  updateClock();

  // Load stats
  async function loadStats() {
    const r = await fetch('/api/stats');
    const s = await r.json();
    document.getElementById('s-total').textContent = s.total_leads;
    document.getElementById('s-emails').textContent = s.emails_today;
    document.getElementById('s-hot').textContent = s.hot_leads;
    document.getElementById('s-warm').textContent = s.warm_leads;
    document.getElementById('s-replies').textContent = s.replies;
    document.getElementById('s-sites').textContent = s.sites_built;
    document.getElementById('s-revenue').textContent = '$' + s.revenue_pipeline.toLocaleString();
  }

  // Load leads table
  async function loadLeads() {
    const r = await fetch('/api/leads');
    allLeads = await r.json();
    renderLeads(allLeads);
  }

  function renderLeads(leads) {
    const tbody = document.getElementById('leads-tbody');
    if (!leads.length) {
      tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;padding:32px;color:var(--muted);">No leads found</td></tr>';
      return;
    }
    tbody.innerHTML = leads.map(l => {
      const tier = l.lead_tier || '';
      const sent = l.email_sent === 'true';
      const reply = l.reply_status || 'none';
      const tierBadge = tier === 'HOT' ? 'hot' : tier === 'WARM' ? 'warm' : 'none';
      const replyBadge = reply !== 'none' ? 'sent' : 'none';
      return `<tr onclick="showDetail(${JSON.stringify(l).replace(/"/g, '&quot;')})">
        <td style="max-width:180px;overflow:hidden;text-overflow:ellipsis;">${l.business_name || l.name || ''}</td>
        <td>${l.city || ''}</td>
        <td>${l.state || ''}</td>
        <td style="font-weight:700;">${l.score || ''}</td>
        <td><span class="badge badge-${tierBadge}">${tier}</span></td>
        <td>${sent ? '<span style="color:#22c55e;">✓</span>' : '<span style="color:#555;">—</span>'}</td>
        <td><span class="badge badge-${replyBadge}">${reply}</span></td>
        <td style="color:var(--muted);">${l.date_scraped || ''}</td>
      </tr>`;
    }).join('');
  }

  function filterLeads(q) {
    q = q.toLowerCase();
    const filtered = allLeads.filter(l =>
      (l.business_name || l.name || '').toLowerCase().includes(q) ||
      (l.city || '').toLowerCase().includes(q) ||
      (l.state || '').toLowerCase().includes(q)
    );
    renderLeads(filtered);
  }

  // Side panel
  function showDetail(lead) {
    document.getElementById('side-title').textContent = lead.business_name || lead.name || 'Lead';
    const fields = [
      ['Business', lead.business_name || lead.name],
      ['Type', lead.business_type],
      ['City', lead.city],
      ['State', lead.state],
      ['Phone', lead.phone],
      ['Email', lead.email],
      ['Score', lead.score],
      ['Tier', lead.lead_tier],
      ['Website', lead.website_url ? `<a href="${lead.website_url}" target="_blank">${lead.website_url}</a>` : '—'],
      ['Demo Site', lead.demo_site_path ? `<a href="${lead.demo_site_path}" target="_blank">View Demo</a>` : '—'],
      ['Google Rating', lead.google_rating],
      ['Reviews', lead.review_count],
      ['Email Sent', lead.email_sent],
      ['Email Sent Date', lead.email_sent_date],
      ['Reply Status', lead.reply_status],
      ['Date Scraped', lead.date_scraped],
    ];
    document.getElementById('side-content').innerHTML = fields
      .filter(([_, v]) => v)
      .map(([label, val]) => `
        <div class="side-field">
          <div class="side-label">${label}</div>
          <div class="side-value">${val}</div>
        </div>`)
      .join('');
    document.getElementById('side-panel').classList.add('open');
  }

  function closeSidePanel() {
    document.getElementById('side-panel').classList.remove('open');
  }

  // Load activity log
  async function loadLog() {
    const r = await fetch('/api/log');
    const lines = await r.json();
    const panel = document.getElementById('log-panel');
    panel.innerHTML = lines.reverse().map(line => {
      let cls = 'log-default';
      if (line.includes('[SUCCESS]')) cls = 'log-success';
      else if (line.includes('[CRITICAL]')) cls = 'log-critical';
      else if (line.includes('[SKIP]')) cls = 'log-skip';
      else if (line.includes('[INFO]')) cls = 'log-info';
      else if (line.includes('[WARNING]')) cls = 'log-warning';
      return `<div class="log-line ${cls}">${line}</div>`;
    }).join('');
  }

  // Check notifications
  async function checkNotifications() {
    const r = await fetch('/api/notifications');
    const notifs = await r.json();
    if (!notifs.length) return;
    const last = notifs[notifs.length - 1];
    const banner = document.getElementById('notif-banner');
    document.getElementById('notif-text').textContent = last.message;
    banner.style.display = 'block';
    setTimeout(() => banner.style.display = 'none', 8000);
  }

  // Test mode
  async function loadTestMode() {
    const r = await fetch('/api/test-mode');
    const d = await r.json();
    const badge = document.getElementById('test-mode-badge');
    const label = document.getElementById('test-mode-label');
    if (d.test_mode) {
      badge.className = 'test-mode-indicator test-mode-on';
      label.textContent = 'ON';
    } else {
      badge.className = 'test-mode-indicator test-mode-off';
      label.textContent = 'OFF';
    }
  }

  async function toggleTestMode() {
    await fetch('/api/toggle-test-mode', { method: 'POST' });
    loadTestMode();
  }

  // Run pipeline
  async function runPipeline() {
    const btn = event.target;
    btn.textContent = '⏳ Running...';
    btn.disabled = true;
    try {
      const r = await fetch('/api/run-pipeline', { method: 'POST' });
      const d = await r.json();
      btn.textContent = '✓ Pipeline Started!';
      setTimeout(() => { btn.textContent = '▶ Run Pipeline Now'; btn.disabled = false; }, 3000);
    } catch (e) {
      btn.textContent = '❌ Error';
      btn.disabled = false;
    }
  }

  // Initial load + auto-refresh
  loadStats();
  loadLeads();
  loadLog();
  loadTestMode();
  checkNotifications();

  setInterval(() => { loadStats(); loadLog(); checkNotifications(); }, 60000);
</script>
</body>
</html>"""


if __name__ == "__main__":
    host = "0.0.0.0"  # accessible on local network (iPhone on same WiFi)
    port = 8080
    print(f"\n🚀 TradeBuilt Dashboard running at http://localhost:{port}")
    print(f"   On your phone (same WiFi): http://[your-mac-ip]:{port}\n")
    app.run(host=host, port=port, debug=False)
