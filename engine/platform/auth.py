"""
platform/auth.py — FORGE Admin Session Management
Password-based admin authentication. Sessions expire after 24 hours of inactivity.
"""

import os
import sys
import functools

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import datetime
from flask import session, redirect, url_for, request


ADMIN_SESSION_HOURS = 24


def is_admin_authenticated() -> bool:
    """
    Check if the current session has a valid, non-expired admin auth token.

    Returns:
        bool: True if admin is authenticated and session has not expired.
    """
    if not session.get("admin_authenticated"):
        return False
    last_seen_str = session.get("admin_last_seen", "")
    if not last_seen_str:
        return False
    try:
        last_seen = datetime.datetime.fromisoformat(last_seen_str)
        if datetime.datetime.now() - last_seen > datetime.timedelta(hours=ADMIN_SESSION_HOURS):
            session.clear()
            return False
    except Exception:
        session.clear()
        return False
    # Refresh last-seen timestamp on activity
    session["admin_last_seen"] = datetime.datetime.now().isoformat()
    return True


def login_admin():
    """Mark the current session as admin-authenticated."""
    session["admin_authenticated"] = True
    session["admin_last_seen"] = datetime.datetime.now().isoformat()
    session.permanent = True


def logout_admin():
    """Clear admin authentication from the current session."""
    session.pop("admin_authenticated", None)
    session.pop("admin_last_seen", None)


def require_admin(view_fn):
    """
    Decorator that redirects to admin login if session is not authenticated.

    Parameters:
        view_fn: The Flask view function to protect.

    Returns:
        Wrapped function that enforces admin auth.
    """
    @functools.wraps(view_fn)
    def wrapper(*args, **kwargs):
        if not is_admin_authenticated():
            return redirect(url_for("admin.login_page", next=request.path))
        return view_fn(*args, **kwargs)
    return wrapper


def generate_csrf_token() -> str:
    """
    Return the CSRF token for the current session, creating one if absent.

    Returns:
        str: CSRF token string.
    """
    import secrets
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)
    return session["csrf_token"]


def validate_csrf(token: str) -> bool:
    """
    Validate a submitted CSRF token against the session.

    Parameters:
        token (str): Token from the form or header.

    Returns:
        bool: True if valid.
    """
    return token == session.get("csrf_token", "")
