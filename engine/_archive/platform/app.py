"""
platform/app.py — FORGE Central Flask Application

LEGACY (Phase 3 — FROZEN): Do not extend. Admin portal and checkout UI only.
- Stripe webhook → FastAPI POST /webhook/stripe
- Pipeline jobs → Celery + POST /run-pipeline
- Retire entirely in Phase 4
Registers all blueprints, configures sessions, CSRF, error handlers,
request logging, and core routes (landing, demo claim, health check).
"""

import os
import sys
import csv
import json
import datetime
import traceback

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from flask import (
    Flask, request, session, render_template, jsonify,
    redirect, url_for, render_template_string
)
from dotenv import load_dotenv

load_dotenv()

LEADS_CSV = os.path.join(BASE_DIR, "leads.csv")
CONVERSIONS_CSV = os.path.join(BASE_DIR, "conversions.csv")
SITES_DIR = os.path.join(BASE_DIR, "sites")


# ─── APP FACTORY ───────────────────────────────────────────────────────────────

def create_app() -> Flask:
    """
    Create and configure the FORGE Flask application.

    Returns:
        Flask: Configured application instance with all blueprints registered.
    """
    app = Flask(
        __name__,
        template_folder=os.path.join(BASE_DIR, "templates"),
        static_folder=os.path.join(BASE_DIR, "static"),
    )

    app.secret_key = os.getenv("FLASK_SECRET_KEY", "forge_dev_secret_change_me")
    app.permanent_session_lifetime = datetime.timedelta(days=7)

    _register_blueprints(app)
    _register_core_routes(app)
    _register_error_handlers(app)
    _register_request_hooks(app)

    return app


# ─── BLUEPRINTS ────────────────────────────────────────────────────────────────

def _register_blueprints(app: Flask):
    """Import and register all route blueprints."""
    from .stripe_handler import stripe_bp
    from .client_portal import portal_bp
    from .admin_portal import admin_bp
    from .booking_agent import booking_bp
    from .whitelabel import whitelabel_bp

    app.register_blueprint(stripe_bp)
    app.register_blueprint(portal_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(booking_bp)
    app.register_blueprint(whitelabel_bp)


# ─── CSRF ──────────────────────────────────────────────────────────────────────

def _csrf_exempt(path: str) -> bool:
    """Return True for routes that manage their own verification."""
    exempt = ["/webhook/stripe", "/webhook/stripe/simulate", "/api/"]
    return any(path.startswith(p) for p in exempt)


# ─── REQUEST HOOKS ─────────────────────────────────────────────────────────────

def _register_request_hooks(app: Flask):
    """Register before/after request hooks for logging and CSRF."""

    @app.before_request
    def enforce_csrf():
        """Validate CSRF token on all state-mutating POST requests."""
        if request.method != "POST":
            return
        if _csrf_exempt(request.path):
            return
        from .auth import validate_csrf, generate_csrf_token
        generate_csrf_token()
        submitted = (
            request.form.get("_csrf_token")
            or request.headers.get("X-CSRF-Token")
        )
        if not validate_csrf(submitted or ""):
            return render_template_string(_CSRF_ERROR_HTML), 403

    @app.after_request
    def log_request(response):
        """Log every request to system_log.txt."""
        try:
            from system_logger import log
            path = request.path
            if path in ("/health", "/favicon.ico"):
                return response
            log(
                "http_request",
                "INFO",
                f"{request.method} {path} -> {response.status_code}",
            )
        except Exception:
            pass
        return response

    @app.context_processor
    def inject_globals():
        """Inject CSRF token into all template contexts."""
        from .auth import generate_csrf_token
        return {"csrf_token": generate_csrf_token()}


# ─── CORE ROUTES ───────────────────────────────────────────────────────────────

def _register_core_routes(app: Flask):
    """Register landing page, demo claim, and health check routes."""

    @app.route("/")
    def landing():
        """Public marketing landing page."""
        try:
            lead_count = _count_leads()
        except Exception:
            lead_count = 0
        return render_template("landing.html", lead_count=lead_count)

    @app.route("/demo/<slug>")
    def demo_claim(slug: str):
        """Demo claim page for a specific business slug."""
        try:
            lead = _find_lead_by_slug(slug)
            if not lead:
                return render_template_string(_NOT_FOUND_HTML, slug=slug), 404
            _record_demo_view(slug)
            return render_template("demo_claim.html", lead=lead, slug=slug)
        except Exception:
            try:
                from system_logger import log
                log("demo_claim", "ERROR", traceback.format_exc()[:400])
            except Exception:
                pass
            return render_template_string(_ERROR_HTML, message="Unable to load demo page."), 500

    @app.route("/api/test-mode", methods=["GET"])
    def api_test_mode():
        """Return current TEST_MODE value from .env (admin only)."""
        from .auth import is_admin_authenticated
        if not is_admin_authenticated():
            return jsonify({"error": "Unauthorized"}), 401
        from dotenv import dotenv_values
        env = dotenv_values(os.path.join(BASE_DIR, ".env"))
        return jsonify({"test_mode": env.get("TEST_MODE", "true").lower() == "true"})

    @app.route("/api/toggle-test-mode", methods=["POST"])
    def api_toggle_test_mode():
        """Toggle TEST_MODE in .env between true and false (admin only)."""
        from .auth import is_admin_authenticated
        if not is_admin_authenticated():
            return jsonify({"error": "Unauthorized"}), 401
        env_path = os.path.join(BASE_DIR, ".env")
        if not os.path.exists(env_path):
            return jsonify({"error": ".env not found"}), 404
        with open(env_path, "r") as f:
            lines = f.readlines()
        current_mode = None
        new_lines = []
        for line in lines:
            if line.startswith("TEST_MODE="):
                current_val = line.strip().split("=", 1)[1].lower()
                current_mode = current_val == "true"
                new_lines.append(f"TEST_MODE={'false' if current_mode else 'true'}\n")
            else:
                new_lines.append(line)
        with open(env_path, "w") as f:
            f.writelines(new_lines)
        return jsonify({"test_mode": not current_mode if current_mode is not None else True})

    @app.route("/health")
    def health():
        """System health check endpoint."""
        try:
            lead_count = _count_leads()
            client_count = _count_conversions()
        except Exception:
            lead_count = 0
            client_count = 0

        uptime = _uptime()
        return jsonify({
            "status": "ok",
            "uptime_seconds": uptime,
            "lead_count": lead_count,
            "client_count": client_count,
            "timestamp": datetime.datetime.now().isoformat(),
        })


# ─── DATA HELPERS ──────────────────────────────────────────────────────────────

_START_TIME = datetime.datetime.now()


def _uptime() -> float:
    """Return seconds since app start."""
    return (datetime.datetime.now() - _START_TIME).total_seconds()


def _count_leads() -> int:
    """Count rows in leads.csv."""
    if not os.path.exists(LEADS_CSV):
        return 0
    with open(LEADS_CSV, "r") as f:
        return max(0, sum(1 for _ in f) - 1)


def _count_conversions() -> int:
    """Count rows in conversions.csv."""
    if not os.path.exists(CONVERSIONS_CSV):
        return 0
    with open(CONVERSIONS_CSV, "r") as f:
        return max(0, sum(1 for _ in f) - 1)


def _find_lead_by_slug(slug: str) -> dict:
    """
    Find a lead in leads.csv matching the given URL slug.

    Parameters:
        slug (str): URL-safe business identifier.

    Returns:
        dict: Lead record or empty dict if not found.
    """
    if not os.path.exists(LEADS_CSV):
        return {}
    import re
    with open(LEADS_CSV, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("business_name", "")
            row_slug = re.sub(
                r"[^a-z0-9-]", "",
                name.lower().replace(" ", "-").replace("'", "").replace(",", "")
            )
            if row_slug == slug:
                return row
    return {}


def _record_demo_view(slug: str):
    """
    Record a demo page view in the SQLite database if available.

    Parameters:
        slug (str): Business slug that was viewed.
    """
    try:
        import sqlite3
        db_path = os.path.join(BASE_DIR, "forge.db")
        conn = sqlite3.connect(db_path)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS demo_visits "
            "(id INTEGER PRIMARY KEY AUTOINCREMENT, slug TEXT, ts TEXT)"
        )
        conn.execute(
            "INSERT INTO demo_visits (slug, ts) VALUES (?, ?)",
            (slug, datetime.datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


# ─── ERROR HANDLERS ────────────────────────────────────────────────────────────

def _register_error_handlers(app: Flask):
    """Register 404 and 500 handlers that return clean HTML pages."""

    @app.errorhandler(404)
    def not_found(e):
        return render_template_string(_NOT_FOUND_HTML, slug=""), 404

    @app.errorhandler(500)
    def server_error(e):
        try:
            from system_logger import log
            log("http_500", "ERROR", traceback.format_exc()[:400])
        except Exception:
            pass
        return render_template_string(_ERROR_HTML, message="An internal error occurred."), 500


# ─── INLINE ERROR TEMPLATES ────────────────────────────────────────────────────

_BASE_ERR = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>{{ title }} — Forge</title>
  <link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@400;500&display=swap" rel="stylesheet"/>
  <style>
    body { margin:0; background:#0a0a0a; color:#f5f5f0; font-family:'DM Sans',sans-serif;
           display:flex; align-items:center; justify-content:center; min-height:100vh; }
    .box { text-align:center; max-width:420px; padding:40px 24px; }
    .brand { font-family:'DM Serif Display',serif; font-size:1.2rem; color:#c9a84c; margin-bottom:32px; }
    h1 { font-family:'DM Serif Display',serif; font-size:3rem; font-weight:400; color:#c9a84c; margin-bottom:12px; }
    p { color:#8a8a8a; line-height:1.7; margin-bottom:28px; }
    a { color:#c9a84c; text-decoration:none; font-size:0.8rem; letter-spacing:0.08em; text-transform:uppercase; }
  </style>
</head>
<body>
  <div class="box">
    <div class="brand">Forge</div>
    {% block content %}{% endblock %}
    <a href="/">Return to homepage</a>
  </div>
</body>
</html>"""

_NOT_FOUND_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>Page Not Found — Forge</title>
  <link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@400;500&display=swap" rel="stylesheet"/>
  <style>
    body{margin:0;background:#0a0a0a;color:#f5f5f0;font-family:'DM Sans',sans-serif;
    display:flex;align-items:center;justify-content:center;min-height:100vh;}
    .box{text-align:center;max-width:420px;padding:40px 24px;}
    .brand{font-family:'DM Serif Display',serif;font-size:1.2rem;color:#c9a84c;margin-bottom:32px;}
    h1{font-family:'DM Serif Display',serif;font-size:5rem;font-weight:400;color:#c9a84c;margin:0 0 8px;}
    p{color:#8a8a8a;line-height:1.7;margin-bottom:28px;}
    a{color:#c9a84c;text-decoration:none;font-size:0.8rem;letter-spacing:0.08em;text-transform:uppercase;}
  </style>
</head>
<body>
  <div class="box">
    <div class="brand">Forge</div>
    <h1>404</h1>
    <p>This page does not exist.</p>
    <a href="/">Return to homepage</a>
  </div>
</body>
</html>"""

_ERROR_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>Error — Forge</title>
  <link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@400;500&display=swap" rel="stylesheet"/>
  <style>
    body{margin:0;background:#0a0a0a;color:#f5f5f0;font-family:'DM Sans',sans-serif;
    display:flex;align-items:center;justify-content:center;min-height:100vh;}
    .box{text-align:center;max-width:420px;padding:40px 24px;}
    .brand{font-family:'DM Serif Display',serif;font-size:1.2rem;color:#c9a84c;margin-bottom:32px;}
    h1{font-family:'DM Serif Display',serif;font-size:2rem;font-weight:400;margin-bottom:12px;}
    p{color:#8a8a8a;line-height:1.7;margin-bottom:28px;}
    a{color:#c9a84c;text-decoration:none;font-size:0.8rem;letter-spacing:0.08em;text-transform:uppercase;}
  </style>
</head>
<body>
  <div class="box">
    <div class="brand">Forge</div>
    <h1>Something went wrong.</h1>
    <p>{{ message }}</p>
    <a href="/">Return to homepage</a>
  </div>
</body>
</html>"""

_CSRF_ERROR_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <title>Invalid Request — Forge</title>
  <style>
    body{margin:0;background:#0a0a0a;color:#f5f5f0;font-family:sans-serif;
    display:flex;align-items:center;justify-content:center;min-height:100vh;}
    .box{text-align:center;max-width:380px;padding:32px;}
    h1{color:#c9a84c;margin-bottom:12px;}
    p{color:#8a8a8a;}
    a{color:#c9a84c;text-decoration:none;font-size:0.8rem;text-transform:uppercase;}
  </style>
</head>
<body>
  <div class="box">
    <h1>Invalid Request</h1>
    <p>CSRF token mismatch. Please go back and try again.</p><br/>
    <a href="javascript:history.back()">Go back</a>
  </div>
</body>
</html>"""
