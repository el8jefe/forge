"""FORGE mail delivery — Resend (production) with Gmail SMTP fallback."""

from mail.sender import active_provider, send_message

__all__ = ["active_provider", "send_message"]