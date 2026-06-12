"""
platform/booking_agent.py — FORGE AI Booking Agent (Autopilot Tier)
Handles inbound visitor inquiries via a chat widget embedded on client demo sites.
Uses the Claude API to answer questions and collect booking information.
Sessions expire after 30 minutes of inactivity.
"""

import os
import sys
import json
import datetime
import traceback

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from flask import Blueprint, request, jsonify, render_template_string
from dotenv import load_dotenv
from system_logger import log

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
BOOKINGS_FILE = os.path.join(BASE_DIR, "bookings.json")
PROFILES_DIR = os.path.join(BASE_DIR, "client_profiles")

SESSION_TTL_MINUTES = 30
MODEL = "claude-sonnet-4-6"

# In-memory conversation store: {session_id: {"messages": [...], "last_active": iso_str, "slug": str}}
_conversations: dict = {}

booking_bp = Blueprint("booking", __name__)


# ─── CLIENT PROFILE MANAGEMENT ─────────────────────────────────────────────────

def _load_profile(slug: str) -> dict:
    """
    Load a client's business profile JSON.

    Parameters:
        slug (str): Business slug identifier.

    Returns:
        dict: Business profile, or a minimal placeholder if not found.
    """
    os.makedirs(PROFILES_DIR, exist_ok=True)
    profile_path = os.path.join(PROFILES_DIR, f"{slug}.json")
    if os.path.exists(profile_path):
        try:
            with open(profile_path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    # Fallback: look up lead data from leads.csv
    return _profile_from_leads(slug)


def _profile_from_leads(slug: str) -> dict:
    """
    Build a minimal business profile from leads.csv data.

    Parameters:
        slug (str): Business slug identifier.

    Returns:
        dict: Minimal business profile.
    """
    import csv
    import re
    leads_path = os.path.join(BASE_DIR, "leads.csv")
    if not os.path.exists(leads_path):
        return {}
    try:
        with open(leads_path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get("business_name", "")
                row_slug = re.sub(
                    r"[^a-z0-9-]", "",
                    name.lower().replace(" ", "-").replace("'", "").replace(",", "")
                )
                if row_slug == slug:
                    return {
                        "business_name": name,
                        "business_type": row.get("business_type", ""),
                        "phone": row.get("phone", ""),
                        "address": f"{row.get('city', '')}, {row.get('state', '')}",
                        "services": [],
                        "hours": {
                            "monday": "9am-5pm",
                            "tuesday": "9am-5pm",
                            "wednesday": "9am-5pm",
                            "thursday": "9am-5pm",
                            "friday": "9am-5pm",
                            "saturday": "closed",
                            "sunday": "closed",
                        },
                        "booking_lead_time_hours": 24,
                        "confirmation_sms": False,
                    }
    except Exception:
        pass
    return {}


def _build_system_prompt(profile: dict) -> str:
    """
    Build the Claude system prompt injected with the client's business profile.

    Parameters:
        profile (dict): Business profile data.

    Returns:
        str: System prompt string.
    """
    business_name = profile.get("business_name", "this business")
    business_type = profile.get("business_type", "service business")
    phone = profile.get("phone", "")
    address = profile.get("address", "")
    services = profile.get("services", [])
    hours = profile.get("hours", {})
    lead_time = profile.get("booking_lead_time_hours", 24)

    services_text = ", ".join(services) if services else "general services"
    hours_text = "\n".join(
        f"  {day.title()}: {time}" for day, time in hours.items()
    ) if hours else "  Contact us for hours"

    return f"""You are a professional booking assistant for {business_name}, a {business_type} located in {address}.

Your responsibilities:
1. Greet visitors warmly and ask how you can help
2. Answer questions about the business using only the information provided below
3. Collect visitor name, phone number, and the service they need before confirming any appointment
4. Confirm appointment requests based on the business hours listed below
5. Log every completed booking

Business information:
  Name: {business_name}
  Type: {business_type}
  Phone: {phone}
  Address: {address}
  Services offered: {services_text}
  Lead time required: {lead_time} hours minimum

Hours of operation:
{hours_text}

Strict rules you must follow:
- Never claim to be a human. You are an AI assistant for {business_name}.
- Never make up information not listed above. If you do not know, say so.
- Stay strictly on topic: booking and business questions only.
- Always collect the visitor's name and phone number before confirming any appointment.
- Collect the requested service and preferred date/time.
- Use professional, direct language. No filler phrases like "Certainly!" or "Of course!".
- If asked about pricing, say the business will provide a quote after confirming the appointment.
- Keep responses concise — no more than 3 sentences per turn.

When a visitor provides their name, phone, and service, respond with a confirmation and state that {business_name} will follow up to confirm the exact time."""


# ─── SESSION MANAGEMENT ────────────────────────────────────────────────────────

def _get_conversation(session_id: str):
    """
    Return a conversation state dict if it exists and has not expired.

    Parameters:
        session_id (str): Unique session identifier.

    Returns:
        dict or None: Conversation state, or None if expired/missing.
    """
    conv = _conversations.get(session_id)
    if not conv:
        return None
    last_active = datetime.datetime.fromisoformat(conv["last_active"])
    if datetime.datetime.now() - last_active > datetime.timedelta(minutes=SESSION_TTL_MINUTES):
        del _conversations[session_id]
        return None
    return conv


def _update_conversation(session_id: str, slug: str, messages: list):
    """
    Create or update a conversation session.

    Parameters:
        session_id (str): Unique session identifier.
        slug (str): Business slug this session is for.
        messages (list): Full conversation message list.
    """
    _conversations[session_id] = {
        "messages": messages,
        "slug": slug,
        "last_active": datetime.datetime.now().isoformat(),
    }


def _purge_expired_sessions():
    """Remove all conversation sessions that have exceeded the TTL."""
    cutoff = datetime.datetime.now() - datetime.timedelta(minutes=SESSION_TTL_MINUTES)
    to_delete = [
        sid for sid, data in _conversations.items()
        if datetime.datetime.fromisoformat(data["last_active"]) < cutoff
    ]
    for sid in to_delete:
        del _conversations[sid]


# ─── BOOKING LOG ───────────────────────────────────────────────────────────────

def _log_booking(slug: str, visitor_info: dict, outcome: str):
    """
    Append a booking record to bookings.json.

    Parameters:
        slug (str): Business slug.
        visitor_info (dict): Collected visitor data (name, phone, service).
        outcome (str): Result of the interaction.
    """
    entries = []
    if os.path.exists(BOOKINGS_FILE):
        try:
            with open(BOOKINGS_FILE, "r") as f:
                entries = json.load(f)
        except Exception:
            entries = []
    entries.append({
        "timestamp": datetime.datetime.now().isoformat(),
        "slug": slug,
        "visitor_name": visitor_info.get("name", ""),
        "visitor_phone": visitor_info.get("phone", ""),
        "service_requested": visitor_info.get("service", ""),
        "outcome": outcome,
    })
    with open(BOOKINGS_FILE, "w") as f:
        json.dump(entries, f, indent=2)


def _extract_visitor_info(messages: list) -> dict:
    """
    Scan conversation messages for collected visitor information.

    Parameters:
        messages (list): List of {"role": ..., "content": ...} message dicts.

    Returns:
        dict: Extracted visitor info with keys name, phone, service.
    """
    import re
    full_text = " ".join(m.get("content", "") for m in messages if m.get("role") == "user")
    phone_match = re.search(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", full_text)
    return {
        "name": "",
        "phone": phone_match.group(0) if phone_match else "",
        "service": "",
    }


# ─── CLAUDE API CALL ───────────────────────────────────────────────────────────

def _call_claude(system_prompt: str, messages: list) -> str:
    """
    Send messages to the Claude API and return the assistant reply.
    Returns an error string if the API key is missing or the call fails.

    Parameters:
        system_prompt (str): Injected business context.
        messages (list): Conversation history in Claude message format.

    Returns:
        str: Assistant reply text.
    """
    if not ANTHROPIC_API_KEY:
        return (
            "The booking assistant is not yet configured. "
            "Please call us directly to schedule an appointment."
        )
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            model=MODEL,
            max_tokens=512,
            system=system_prompt,
            messages=messages,
        )
        return response.content[0].text.strip()
    except Exception as e:
        log("booking_agent", "ERROR", str(e)[:200])
        return "I am having trouble connecting right now. Please call us directly."


# ─── ROUTES ────────────────────────────────────────────────────────────────────

@booking_bp.route("/api/booking/chat", methods=["POST"])
def booking_chat():
    """
    Handle a single chat turn from the booking widget.
    Expects JSON: {session_id, message, slug}
    Returns JSON: {reply, session_id}
    """
    try:
        data = request.get_json(force=True) or {}
        session_id = data.get("session_id", "")
        user_message = (data.get("message") or "").strip()
        slug = (data.get("slug") or "").strip()

        if not session_id or not slug:
            return jsonify({"error": "session_id and slug are required"}), 400

        if not user_message:
            return jsonify({"error": "message is required"}), 400

        _purge_expired_sessions()

        profile = _load_profile(slug)
        system_prompt = _build_system_prompt(profile)

        conv = _get_conversation(session_id)
        if conv:
            messages = conv["messages"]
        else:
            messages = []

        messages.append({"role": "user", "content": user_message})
        reply = _call_claude(system_prompt, messages)
        messages.append({"role": "assistant", "content": reply})

        _update_conversation(session_id, slug, messages)

        # Detect completed booking (heuristic: assistant confirmed and phone found)
        if len(messages) > 4 and any(
            kw in reply.lower() for kw in ["follow up", "confirm", "appointment confirmed", "will contact"]
        ):
            visitor_info = _extract_visitor_info(messages)
            if visitor_info.get("phone"):
                try:
                    _log_booking(slug, visitor_info, "booked")
                    _send_confirmation_sms(profile, visitor_info)
                except Exception:
                    pass

        return jsonify({"reply": reply, "session_id": session_id})

    except Exception as e:
        log("booking_chat", "ERROR", traceback.format_exc()[:300])
        return jsonify({"error": "Internal error. Please try again."}), 500


def _send_confirmation_sms(profile: dict, visitor_info: dict):
    """
    Send an SMS confirmation to the visitor if Twilio is configured and the
    business profile has confirmation_sms enabled.

    Parameters:
        profile (dict): Business profile.
        visitor_info (dict): Visitor contact information.
    """
    if not profile.get("confirmation_sms"):
        return
    twilio_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    twilio_token = os.getenv("TWILIO_AUTH_TOKEN", "")
    twilio_from = os.getenv("TWILIO_FROM", "")
    visitor_phone = visitor_info.get("phone", "")
    if not all([twilio_sid, twilio_token, twilio_from, visitor_phone]):
        return
    try:
        from twilio.rest import Client
        client = Client(twilio_sid, twilio_token)
        business_name = profile.get("business_name", "the business")
        client.messages.create(
            body=(
                f"Your appointment request with {business_name} has been received. "
                f"We will follow up to confirm your time. "
                f"Questions? Call {profile.get('phone', 'us')}."
            ),
            from_=twilio_from,
            to=visitor_phone,
        )
        log("booking_sms", "SUCCESS", f"SMS sent to {visitor_phone}")
    except ImportError:
        log("booking_sms", "SKIP", "twilio not installed")
    except Exception as e:
        log("booking_sms", "ERROR", str(e)[:120])


@booking_bp.route("/api/booking/widget.js")
def widget_script():
    """Serve the booking widget JavaScript for a given slug."""
    slug = request.args.get("slug", "")
    profile = _load_profile(slug)
    business_name = profile.get("business_name", "this business")
    js = _build_widget_js(slug, business_name)
    return js, 200, {"Content-Type": "application/javascript"}


def _build_widget_js(slug: str, business_name: str) -> str:
    """
    Build the self-contained booking widget JavaScript.

    Parameters:
        slug (str): Business slug.
        business_name (str): Display name for the business.

    Returns:
        str: Standalone JavaScript that renders the chat widget.
    """
    return f"""
(function() {{
  var SLUG = {json.dumps(slug)};
  var BUSINESS = {json.dumps(business_name)};
  var SESSION_ID = 'sess_' + Math.random().toString(36).slice(2);
  var API_BASE = window.location.origin;

  var style = document.createElement('style');
  style.textContent = `
    #forge-widget-btn {{
      position:fixed; bottom:24px; right:24px; z-index:9998;
      background:#c9a84c; border:none; border-radius:0; width:56px; height:56px;
      cursor:pointer; display:flex; align-items:center; justify-content:center;
      box-shadow:0 4px 20px rgba(0,0,0,0.4);
    }}
    #forge-widget-btn svg {{ width:24px; height:24px; fill:#0a0a0a; }}
    #forge-chat {{
      position:fixed; bottom:96px; right:24px; z-index:9999; width:340px;
      background:#111; border:1px solid rgba(255,255,255,0.1);
      font-family:'DM Sans',system-ui,sans-serif; display:none; flex-direction:column;
      max-height:480px;
    }}
    #forge-chat-header {{
      background:#0a0a0a; padding:14px 18px; border-bottom:1px solid rgba(255,255,255,0.07);
      display:flex; justify-content:space-between; align-items:center;
    }}
    #forge-chat-title {{ color:#f5f5f0; font-size:0.85rem; font-weight:500; }}
    #forge-chat-close {{ color:#8a8a8a; cursor:pointer; font-size:18px; background:none; border:none; }}
    #forge-chat-msgs {{
      flex:1; overflow-y:auto; padding:16px; display:flex; flex-direction:column; gap:10px;
    }}
    .forge-msg {{ max-width:88%; font-size:0.85rem; line-height:1.5; padding:10px 14px; }}
    .forge-msg.bot {{ background:rgba(255,255,255,0.05); color:#f5f5f0; align-self:flex-start; }}
    .forge-msg.user {{ background:#c9a84c; color:#0a0a0a; align-self:flex-end; }}
    #forge-chat-form {{
      display:flex; border-top:1px solid rgba(255,255,255,0.07); padding:12px;
      gap:8px;
    }}
    #forge-chat-input {{
      flex:1; background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.1);
      color:#f5f5f0; padding:10px 12px; font-family:inherit; font-size:0.85rem; outline:none;
    }}
    #forge-chat-send {{
      background:#c9a84c; color:#0a0a0a; border:none; padding:10px 14px;
      cursor:pointer; font-size:0.8rem; font-weight:600;
    }}
  `;
  document.head.appendChild(style);

  var btn = document.createElement('button');
  btn.id = 'forge-widget-btn';
  btn.innerHTML = '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/></svg>';
  document.body.appendChild(btn);

  var chat = document.createElement('div');
  chat.id = 'forge-chat';
  chat.innerHTML = `
    <div id="forge-chat-header">
      <span id="forge-chat-title">${{BUSINESS}}</span>
      <button id="forge-chat-close">&#x2715;</button>
    </div>
    <div id="forge-chat-msgs"></div>
    <form id="forge-chat-form">
      <input id="forge-chat-input" type="text" placeholder="Type a message..." autocomplete="off"/>
      <button type="submit" id="forge-chat-send">Send</button>
    </form>
  `;
  document.body.appendChild(chat);

  var opened = false;
  function addMsg(text, role) {{
    var msgs = document.getElementById('forge-chat-msgs');
    var div = document.createElement('div');
    div.className = 'forge-msg ' + role;
    div.textContent = text;
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
  }}

  function sendMsg(text) {{
    addMsg(text, 'user');
    fetch(API_BASE + '/api/booking/chat', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{session_id: SESSION_ID, message: text, slug: SLUG}})
    }}).then(r => r.json()).then(d => {{
      if (d.reply) addMsg(d.reply, 'bot');
    }}).catch(() => addMsg('Connection error. Please try again.', 'bot'));
  }}

  btn.addEventListener('click', function() {{
    if (!opened) {{
      chat.style.display = 'flex';
      addMsg('Hello! How can I help you today?', 'bot');
      opened = true;
    }} else {{
      chat.style.display = chat.style.display === 'none' ? 'flex' : 'none';
    }}
  }});

  document.getElementById('forge-chat-close').addEventListener('click', function() {{
    chat.style.display = 'none';
  }});

  document.getElementById('forge-chat-form').addEventListener('submit', function(e) {{
    e.preventDefault();
    var input = document.getElementById('forge-chat-input');
    var text = input.value.trim();
    if (!text) return;
    input.value = '';
    sendMsg(text);
  }});
}})();
"""
