"""
scraper.py — FORGE Lead Scraper + 20-Point Scoring Engine
Scrapes Google Places, scores every lead, and writes leads.csv / call_list.csv
"""

import requests
import csv
import os
import re
import time
import shutil
import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from system_logger import log

load_dotenv()

GOOGLE_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LEADS_CSV = os.path.join(SCRIPT_DIR, "leads.csv")
CALL_LIST_CSV = os.path.join(SCRIPT_DIR, "call_list.csv")

TARGET_STATES = {
    "CT", "NY", "NJ", "MA", "PA", "RI", "MD", "VA",
    "NC", "GA", "FL", "TX", "IL", "OH", "MI", "CA",
    "AZ", "NV", "WA", "CO",
}

BUSINESS_TYPES = [
    "HVAC contractor",
    "plumber",
    "electrician",
    "roofer",
    "landscaper",
    "pest control",
    "auto detailing",
    "pressure washing",
    "pool service",
    "carpet cleaning",
    "moving company",
    "appliance repair",
    "house painting",
    "handyman",
    "tree service",
    "masonry",
    "window cleaning",
    "junk removal",
    "garage door repair",
    "locksmith",
    "mobile mechanic",
    "boat detailing",
    "fence installation",
    "gutter service",
    "drywall repair",
    "flooring installation",
]

CITIES = {
    "CT": [
        "Greenwich", "Darien", "New Canaan", "Westport", "Fairfield", "Ridgefield",
        "Stamford", "Norwalk", "Bridgeport", "New Haven", "Hartford",
        "Waterbury", "Danbury",
    ],
    "NY": [
        "White Plains", "Yonkers", "New Rochelle", "Scarsdale", "Rye", "Bronxville",
        "Albany", "Troy", "Schenectady", "Utica", "Syracuse", "Rochester", "Buffalo",
        "Poughkeepsie", "Newburgh",
    ],
    "NJ": [
        "Hoboken", "Jersey City", "Newark", "Paterson", "Elizabeth", "Trenton",
        "Camden", "Edison", "Montclair", "Morristown", "Princeton",
    ],
    "MA": [
        "Boston", "Cambridge", "Worcester", "Springfield", "Lowell",
        "Brockton", "Quincy", "Wellesley", "Newton", "Needham", "Framingham",
    ],
    "PA": [
        "Philadelphia", "Pittsburgh", "Allentown", "Erie", "Reading",
        "Scranton", "Bethlehem", "Lancaster", "West Chester",
    ],
    "RI": ["Providence", "Cranston", "Pawtucket", "Warwick", "Newport"],
    "MD": [
        "Baltimore", "Silver Spring", "Rockville", "Gaithersburg", "Annapolis",
        "Bethesda", "Columbia", "Towson",
    ],
    "VA": [
        "Virginia Beach", "Norfolk", "Richmond", "Arlington", "Alexandria",
        "Roanoke", "Chesapeake", "Newport News", "McLean", "Herndon",
    ],
    "NC": [
        "Charlotte", "Raleigh", "Greensboro", "Durham", "Winston-Salem",
        "Fayetteville", "Cary", "Chapel Hill", "Wilmington",
    ],
    "GA": [
        "Atlanta", "Augusta", "Savannah", "Columbus", "Macon",
        "Athens", "Alpharetta", "Roswell", "Marietta",
    ],
    "FL": [
        "Miami", "Orlando", "Tampa", "Jacksonville", "Fort Lauderdale",
        "St Petersburg", "Tallahassee", "Gainesville", "Naples",
        "Boca Raton", "Sarasota", "Cape Coral", "Clearwater",
    ],
    "TX": [
        "Houston", "Dallas", "San Antonio", "Austin", "Fort Worth",
        "El Paso", "Arlington", "Corpus Christi", "Plano", "Laredo",
        "Lubbock", "Garland", "Irving", "Amarillo", "Grand Prairie",
        "Waco", "McAllen", "Killeen", "Beaumont", "Odessa",
        "Midland", "Tyler", "Denton", "Abilene", "Round Rock",
        "The Woodlands", "Katy", "Sugar Land", "Frisco", "McKinney",
        "Brownsville", "Pearland", "League City", "Wichita Falls",
    ],
    "IL": [
        "Chicago", "Aurora", "Rockford", "Joliet", "Naperville",
        "Springfield", "Peoria", "Elgin", "Waukegan", "Champaign",
    ],
    "OH": [
        "Columbus", "Cleveland", "Cincinnati", "Toledo", "Akron",
        "Dayton", "Canton", "Youngstown", "Dublin",
    ],
    "MI": [
        "Detroit", "Grand Rapids", "Warren", "Sterling Heights",
        "Lansing", "Ann Arbor", "Flint", "Dearborn", "Troy",
    ],
    "CA": [
        "Los Angeles", "San Diego", "San Jose", "Fresno", "Sacramento",
        "Oakland", "Bakersfield", "Anaheim", "Stockton", "Riverside",
        "Irvine", "Chula Vista", "Modesto", "Santa Ana",
    ],
    "AZ": [
        "Phoenix", "Tucson", "Mesa", "Chandler", "Scottsdale",
        "Tempe", "Gilbert", "Peoria", "Surprise",
    ],
    "NV": [
        "Las Vegas", "Henderson", "Reno", "North Las Vegas", "Sparks",
    ],
    "WA": [
        "Seattle", "Spokane", "Tacoma", "Vancouver", "Bellevue",
        "Redmond", "Kirkland", "Bellingham",
    ],
    "CO": [
        "Denver", "Colorado Springs", "Aurora", "Fort Collins",
        "Lakewood", "Boulder", "Thornton", "Arvada",
    ],
}

SEARCH_QUERIES = [
    (f"{btype} in {city} {state}", city, state)
    for state, cities in CITIES.items()
    for city in cities
    for btype in BUSINESS_TYPES
]

SKIP_KEYWORDS = [
    "one hour heating", "one hour air", "comfort systems", "service experts",
    "trane comfort", "carrier factory authorized",
    "roto-rooter", "roto rooter", "mr. rooter", "mr rooter",
    "mr. electric", "mr electric",
    "terminix", "orkin", "rollins", "truly nolen", "servicemaster",
    "rentokil", "massey services", "aptive",
    "trugreen", "tru green", "scotts lawn", "weed man", "davey tree",
    "brightview", "brickman",
    "homeadvisor", "angi ", "angies list", "thumbtack",
]

CSV_COLUMNS = [
    "business_name", "owner_name", "owner_confidence", "owner_source", "email", "email_confidence", "phone", "city", "state",
    "business_type", "google_rating", "review_count", "website_url",
    "website_status", "score", "lead_tier", "site_tier", "date_scraped",
    "demo_site_path", "email_sent", "email_sent_date", "reply_status",
]


def get_business_type(name, query=""):
    """
    Infer business type from the business name and search query string.

    Parameters:
        name (str): Business name from Google Places.
        query (str): The search query used to find this business.

    Returns:
        str: One of the canonical BUSINESS_TYPES keys.
    """
    name_lower = name.lower()
    query_lower = query.lower()

    # Name-based detection (checked first — most reliable)
    if any(x in name_lower for x in ["hvac", "heating", "cooling", "air conditioning", "furnace", "ac repair"]):
        return "hvac"
    if any(x in name_lower for x in ["plumb", "drain", "pipe", "sewer", "rooter"]):
        return "plumber"
    if any(x in name_lower for x in ["electric", "wiring"]):
        return "electrician"
    if any(x in name_lower for x in ["roof", "roofing"]):
        return "roofer"
    if any(x in name_lower for x in ["landscape", "landscaping", "lawn", "yard", "garden", "mow"]):
        return "landscaper"
    if any(x in name_lower for x in ["pest", "exterminator", "termite", "bug control", "rodent"]):
        return "pest control"
    if any(x in name_lower for x in ["auto detail", "car detail", "mobile detail", "auto spa"]):
        return "auto detailing"
    if any(x in name_lower for x in ["pressure wash", "power wash", "soft wash"]):
        return "pressure washing"
    if any(x in name_lower for x in ["pool service", "pool clean", "pool care", "pool mainten"]):
        return "pool service"
    if any(x in name_lower for x in ["carpet clean", "rug clean", "upholstery clean"]):
        return "carpet cleaning"
    if any(x in name_lower for x in ["moving", "movers", "relocation", "hauling"]):
        return "moving company"
    if any(x in name_lower for x in ["appliance repair", "washer repair", "dryer repair", "refrigerator repair"]):
        return "appliance repair"
    if any(x in name_lower for x in ["painting", "painter", "paint contractor"]):
        return "house painting"
    if any(x in name_lower for x in ["handyman", "home repair", "odd job"]):
        return "handyman"
    if any(x in name_lower for x in ["tree service", "tree removal", "arborist", "tree trim", "stump"]):
        return "tree service"
    if any(x in name_lower for x in ["mason", "masonry", "concrete", "brick", "stone work"]):
        return "masonry"
    if any(x in name_lower for x in ["window clean", "window wash"]):
        return "window cleaning"
    if any(x in name_lower for x in ["junk removal", "junk haul", "debris removal", "cleanout"]):
        return "junk removal"
    if any(x in name_lower for x in ["garage door"]):
        return "garage door repair"
    if any(x in name_lower for x in ["locksmith", "lock service", "key service"]):
        return "locksmith"
    if any(x in name_lower for x in ["mobile mechanic", "mobile auto", "roadside mechanic"]):
        return "mobile mechanic"
    if any(x in name_lower for x in ["boat detail", "marine detail", "yacht clean"]):
        return "boat detailing"
    if any(x in name_lower for x in ["fence install", "fence contractor", "fencing"]):
        return "fence installation"
    if any(x in name_lower for x in ["gutter", "gutter clean", "gutter guard"]):
        return "gutter service"
    if any(x in name_lower for x in ["drywall", "sheetrock"]):
        return "drywall repair"
    if any(x in name_lower for x in ["flooring", "floor install", "tile install", "hardwood floor"]):
        return "flooring installation"

    # Query-based fallback
    if "hvac" in query_lower or "heating" in query_lower or "cooling" in query_lower:
        return "hvac"
    if "plumb" in query_lower:
        return "plumber"
    if "electric" in query_lower:
        return "electrician"
    if "roof" in query_lower:
        return "roofer"
    if "landscape" in query_lower or "landscap" in query_lower:
        return "landscaper"
    if "pest" in query_lower:
        return "pest control"
    if "auto detail" in query_lower or "car detail" in query_lower:
        return "auto detailing"
    if "pressure wash" in query_lower or "power wash" in query_lower:
        return "pressure washing"
    if "pool service" in query_lower or "pool clean" in query_lower:
        return "pool service"
    if "carpet clean" in query_lower:
        return "carpet cleaning"
    if "moving" in query_lower or "movers" in query_lower:
        return "moving company"
    if "appliance repair" in query_lower:
        return "appliance repair"
    if "house paint" in query_lower or "painting contractor" in query_lower:
        return "house painting"
    if "handyman" in query_lower:
        return "handyman"
    if "tree service" in query_lower or "tree removal" in query_lower:
        return "tree service"
    if "masonry" in query_lower or "concrete" in query_lower:
        return "masonry"
    if "window clean" in query_lower:
        return "window cleaning"
    if "junk removal" in query_lower:
        return "junk removal"
    if "garage door" in query_lower:
        return "garage door repair"
    if "locksmith" in query_lower:
        return "locksmith"
    if "mobile mechanic" in query_lower:
        return "mobile mechanic"
    if "boat detail" in query_lower:
        return "boat detailing"
    if "fence install" in query_lower or "fencing" in query_lower:
        return "fence installation"
    if "gutter" in query_lower:
        return "gutter service"
    if "drywall" in query_lower:
        return "drywall repair"
    if "flooring" in query_lower:
        return "flooring installation"

    return "hvac"


def load_existing_leads():
    """Return set of already-seen business names (lowercase)."""
    from storage import use_postgres

    if use_postgres():
        from repositories import leads_repo
        names = set()
        for lead in leads_repo.list_all(limit=10000):
            key = (lead.get("business_name") or lead.get("name", "")).strip().lower()
            if key:
                names.add(key)
        return names

    existing = set()
    for f in [LEADS_CSV, CALL_LIST_CSV]:
        if not os.path.exists(f):
            continue
        with open(f, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                key = (row.get("business_name") or row.get("name", "")).strip().lower()
                if key:
                    existing.add(key)
    return existing


# ─── 20-POINT SCORING ENGINE ──────────────────────────────────────────────────

def score_website_quality(website: str) -> tuple:
    """
    Returns (points, website_status_string).
    +5  no website at all
    +3  bad/outdated website
     0  solid modern website → caller should skip this lead
    """
    if not website:
        return 5, "no_website"

    try:
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
        resp = requests.get(website, headers=headers, timeout=7, allow_redirects=True)
        html_lower = resp.text.lower()
        soup = BeautifulSoup(resp.text, "html.parser")

        bad_signals = 0

        # No SSL
        if website.startswith("http://"):
            bad_signals += 1

        # Not mobile responsive
        viewport = soup.find("meta", attrs={"name": "viewport"})
        if not viewport:
            bad_signals += 1

        # Copyright year older than 2022
        years = re.findall(r'(?:copyright|©|&copy;).*?20(\d{2})', html_lower)
        if not years:
            years = re.findall(r'20(\d{2})', html_lower)
        if years:
            latest_year = max(int(y) for y in years)
            if latest_year < 22:
                bad_signals += 1

        # Wix/Weebly free subdomain
        free_builders = ["wix.com", "weebly.com", "yolasite.com", "angelfire.com", "tripod.com", "homestead.com"]
        if any(b in website.lower() or b in html_lower for b in free_builders):
            bad_signals += 1

        # Slow load is hard to detect here — check for heavy page
        if len(resp.content) > 3_000_000:
            bad_signals += 1

        if bad_signals >= 2:
            return 3, "bad_website"
        elif bad_signals == 1:
            return 1, "weak_website"
        else:
            return 0, "solid_website"

    except Exception:
        return 3, "site_unreachable"


def score_lead(place_details: dict, website: str, city: str, state: str) -> tuple:
    """
    Full 20-point scoring. Returns (total_score, website_status, notes_list).
    """
    score = 0
    notes = []

    # ── WEBSITE DETECTION (max 5 pts) ──
    web_pts, website_status = score_website_quality(website)
    if website_status == "solid_website":
        return 0, website_status, ["solid website — skip"]
    score += web_pts
    notes.append(website_status)

    # ── REPUTATION SIGNALS (max 4 pts) ──
    rating = float(place_details.get("rating") or 0)
    reviews = int(place_details.get("user_ratings_total") or 0)

    if rating > 0 and rating < 4.0:
        score += 3
        notes.append(f"low_rating_{rating}")
    elif 4.0 <= rating < 4.5:
        score += 1
        notes.append(f"ok_rating_{rating}")

    if reviews < 20:
        score += 2
        notes.append("very_few_reviews")
    elif reviews < 50:
        score += 1
        notes.append("few_reviews")

    # ── BUSINESS PROFILE SIGNALS (max 6 pts) ──
    # Business registered under 3 years ago — estimated from place opening if available
    # Google doesn't expose age directly; skip or proxy via reviews
    # We'll award if very few reviews (already counted) AND no website
    if not website and reviews < 30:
        score += 2
        notes.append("new_or_low_profile")

    # No social media — inferred from website check or Google listing
    # (Google Places doesn't expose social; we check the website)
    if website_status in ("no_website", "site_unreachable"):
        score += 1
        notes.append("no_social_found")

    # No email publicly listed
    if not place_details.get("email_found"):
        score += 1
        notes.append("no_public_email")

    # No business hours listed
    if not place_details.get("opening_hours"):
        score += 1
        notes.append("no_hours_listed")

    # In target service area
    if state.upper() in TARGET_STATES:
        score += 1
        notes.append("target_market")

    return min(score, 20), website_status, notes


def get_tier(score: int) -> str:
    if score >= 14:
        return "HOT"
    elif score >= 8:
        return "WARM"
    else:
        return "LOW"


_EMAIL_BLOCK_TERMS = [
    "noreply", "no-reply", "donotreply", "support", "admin",
    "webmaster", "hostmaster", "postmaster", "abuse", "spam",
    "example", "test", "placeholder", "sentry", "schema",
    "jquery", "wordpress", "wix", "squarespace", "shopify",
    "mailchimp", "hubspot", "constantcontact", "fontawesome",
    "googleapis", "gstatic", "cloudflare",
]

_EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')

_CONTACT_PATHS = [
    "/contact", "/contact-us", "/about", "/about-us",
    "/reach-us", "/get-in-touch", "/info",
]

_OWNER_TITLES = (
    "owner",
    "founder",
    "co-founder",
    "ceo",
    "president",
    "principal",
    "operator",
    "managing partner",
)

_OWNER_STOPWORDS = {
    "team", "staff", "service", "support", "contact", "about",
    "home", "our", "we", "us", "llc", "inc", "corp", "company",
    "business", "google", "facebook", "instagram", "linkedin",
}

_OWNER_EMAIL_LOCALPART_BLOCKLIST = {
    "info", "contact", "support", "hello", "admin", "office",
    "sales", "billing", "service", "customerservice",
}

_OWNER_BUSINESS_SUBSTRINGS = (
    "roof", "plumb", "electric", "hvac", "landscap", "pest",
    "service", "contract", "company", "inc", "llc", "mechanical",
)

_BUSINESS_NAME_CUTOFF_WORDS = {
    "services", "service", "landscaping", "landscape", "roofing", "roof",
    "plumbing", "plumber", "electric", "electrical", "electrician", "hvac",
    "heating", "cooling", "pest", "control", "contracting", "construction",
    "maintenance", "design", "solutions", "restoration", "systems", "supply",
    "bros", "brothers", "group", "company", "co", "corp", "inc", "llc",
}

_NON_NAME_TOKENS = {
    "greenwich", "bridgeport", "comfort", "property", "solutions", "park", "city",
    "valley", "cedar", "copper", "northwind", "legacy", "rodent", "central",
    "mass", "second", "nature", "alpha", "elite", "texas", "ground", "south",
    "denton", "clear", "fork", "new", "age", "just", "for", "you", "four", "seasons",
}


def _normalize_person_name(candidate: str) -> str:
    """
    Normalize and validate a likely person name.

    Parameters:
        candidate (str): Raw candidate text.

    Returns:
        str: Normalized person name, or empty string if invalid.
    """
    if not candidate:
        return ""
    cleaned = re.sub(r"\s+", " ", candidate).strip(" -,:;|")
    cleaned = re.sub(r"^(mr|mrs|ms|dr)\.?\s+", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\b(jr|sr|ii|iii|iv)\.?$", "", cleaned, flags=re.I).strip()
    if not cleaned:
        return ""

    tokens = cleaned.split()
    if len(tokens) < 2 or len(tokens) > 4:
        return ""
    if any(any(ch.isdigit() for ch in token) for token in tokens):
        return ""
    if any(len(token) <= 1 for token in tokens):
        return ""
    lowered_tokens = [t.lower().strip(".,") for t in tokens]
    if any(t in _OWNER_STOPWORDS for t in lowered_tokens):
        return ""
    if any(re.search(r"[^a-zA-Z\-']", token) for token in tokens):
        return ""

    return " ".join(t.capitalize() for t in tokens)


def _is_likely_owner_name(name: str) -> bool:
    """
    Return True when the value looks like a human owner name.
    """
    normalized = _normalize_person_name(name)
    if not normalized:
        return False
    lowered_tokens = [t.lower() for t in normalized.split()]
    if any(any(sub in token for sub in _OWNER_BUSINESS_SUBSTRINGS) for token in lowered_tokens):
        return False
    return True


def _is_likely_owner_token(token: str) -> bool:
    """Return True when token can reasonably be a first name."""
    t = (token or "").strip()
    if len(t) < 2 or len(t) > 24:
        return False
    if any(ch.isdigit() for ch in t):
        return False
    if not re.match(r"^[A-Za-z][A-Za-z'\-]*$", t):
        return False
    return t.lower() not in _NON_NAME_TOKENS


def _owner_confidence_from_existing_name(owner_name: str, email: str = "") -> str:
    """
    Infer owner confidence from an existing owner_name + optional email corroboration.
    """
    name = (owner_name or "").strip()
    if not name:
        return "none"

    tokens = [t for t in re.findall(r"[A-Za-z][A-Za-z'\-]*", name) if t]
    if not tokens:
        return "none"

    if len(tokens) >= 2 and _is_likely_owner_name(" ".join(tokens[:2])):
        if email:
            email_l = email.lower()
            if any(len(t) >= 3 and t.lower() in email_l for t in tokens[:2]):
                return "high"
        return "medium"

    if len(tokens) == 1 and _is_likely_owner_token(tokens[0]):
        return "medium"

    return "none"


def _owner_source_from_existing_name(owner_name: str, email: str = "") -> str:
    """Infer source label for already-populated owner names."""
    confidence = _owner_confidence_from_existing_name(owner_name, email)
    if confidence == "none":
        return "none"
    if confidence == "high" and email:
        return "email"
    return "existing"


def _extract_owner_from_text(text: str) -> str:
    """
    Extract owner/founder style name from page text.

    Parameters:
        text (str): Visible text from a web page.

    Returns:
        str: Owner name if found, else empty string.
    """
    if not text:
        return ""

    # Pattern examples:
    # "Owner: John Smith"
    # "Founded by Maria Lopez"
    # "John Smith, Founder"
    title_group = "|".join(re.escape(t) for t in _OWNER_TITLES)
    patterns = [
        rf"(?:{title_group})\s*[:\-]\s*([A-Z][a-zA-Z'\\-]+(?:\s+[A-Z][a-zA-Z'\\-]+){{1,3}})",
        rf"(?:founded|run|owned)\s+by\s+([A-Z][a-zA-Z'\\-]+(?:\s+[A-Z][a-zA-Z'\\-]+){{1,3}})",
        rf"([A-Z][a-zA-Z'\\-]+(?:\s+[A-Z][a-zA-Z'\\-]+){{1,3}})\s*,\s*(?:{title_group})\b",
    ]

    for pattern in patterns:
        m = re.search(pattern, text, flags=re.I)
        if not m:
            continue
        candidate = m.group(1).strip()
        normalized = _normalize_person_name(candidate)
        if normalized and _is_likely_owner_name(normalized):
            return normalized
    return ""


def _extract_owner_from_email(email: str) -> str:
    """
    Infer a person's name from email local-part when possible.

    Parameters:
        email (str): Candidate email.

    Returns:
        str: Inferred owner name, else empty string.
    """
    if not email or "@" not in email:
        return ""
    local = email.split("@", 1)[0].lower()
    if local in _OWNER_EMAIL_LOCALPART_BLOCKLIST:
        return ""

    tokens = [p for p in re.split(r"[._\-]+", local) if p]
    if len(tokens) < 2 or len(tokens) > 3:
        return ""
    if any(t in _OWNER_STOPWORDS for t in tokens):
        return ""
    if any(any(sub in t for sub in _OWNER_BUSINESS_SUBSTRINGS) for t in tokens):
        return ""
    candidate = " ".join(tokens)
    normalized = _normalize_person_name(candidate)
    if normalized and _is_likely_owner_name(normalized):
        return normalized
    return ""


def _extract_owner_from_business_name(business_name: str, email: str = "") -> str:
    """
    Infer owner name from business name patterns.

    Examples:
      - "John Richmond Landscaping" -> "John Richmond"
      - "Ray's Landscape Services" -> "Ray"
    """
    if not business_name:
        return ""

    normalized_name = business_name.replace("’", "'").strip()

    email_l = (email or "").lower()

    # Possessive pattern: "Ray's Landscape ..."
    poss = re.match(r"^([A-Z][a-zA-Z'\-]{1,24})'s\b", normalized_name)
    if poss:
        first = poss.group(1)
        if first.lower() not in _BUSINESS_NAME_CUTOFF_WORDS and first.lower() not in _NON_NAME_TOKENS:
            return first.capitalize()

    raw_tokens = re.findall(r"[A-Za-z][A-Za-z'\-]*", normalized_name)
    tokens = [t for t in raw_tokens if t]
    if len(tokens) < 2:
        return ""

    # Collect leading person-like tokens until a trade/business cutoff word.
    person_tokens = []
    for token in tokens:
        low = token.lower()
        if low in _BUSINESS_NAME_CUTOFF_WORDS:
            break
        if any(sub in low for sub in _OWNER_BUSINESS_SUBSTRINGS):
            break
        if not re.match(r"^[A-Z][a-zA-Z'\-]{1,24}$", token):
            break
        if token.isupper():
            break
        if low in _NON_NAME_TOKENS:
            break
        person_tokens.append(token)
        if len(person_tokens) == 3:
            break

    if len(person_tokens) < 2:
        return ""

    # Require cutoff word after candidate to ensure it's "Name + Trade".
    if len(tokens) <= len(person_tokens):
        return ""

    # Require weak corroboration from email local/domain when available.
    # This prevents synthetic names from generic business labels.
    if email_l:
        token_hits = sum(1 for t in person_tokens[:2] if len(t) >= 3 and t.lower() in email_l)
        if token_hits == 0:
            return ""

    candidate = " ".join(person_tokens[:2])
    if _is_likely_owner_name(candidate):
        return _normalize_person_name(candidate)
    return ""


def find_owner_name(website: str, business_name: str = "", email: str = "") -> tuple:
    """
    Attempt to enrich owner_name from business web presence.

    Strategy:
      1. Try email local-part (fast, often accurate for small businesses).
      2. Scrape homepage text and common contact/about pages.
      3. Extract names near owner/founder/title signals.

    Parameters:
        website (str): Business website URL.
        business_name (str): Business name for logging.
        email (str): Already discovered email (optional).

    Returns:
        tuple: (owner_name, owner_confidence, owner_source)
    """
    inferred = _extract_owner_from_email(email)
    if inferred:
        log("owner_extract", "SUCCESS", f"{business_name} | method=email | result={inferred}")
        return inferred, "high", "email"

    inferred = _extract_owner_from_business_name(business_name, email=email)
    if inferred:
        log("owner_extract", "SUCCESS", f"{business_name} | method=business_name | result={inferred}")
        return inferred, "medium", "business_name"

    if not website:
        log("owner_extract", "FAIL", f"{business_name} | method=none | result=none")
        return "", "none", "none"

    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    urls = [website.rstrip("/")] + [website.rstrip("/") + p for p in _CONTACT_PATHS]
    seen = set()

    for url in urls:
        if url in seen:
            continue
        seen.add(url)
        try:
            r = requests.get(url, headers=headers, timeout=5, allow_redirects=True)
            if r.status_code != 200:
                continue
            text = BeautifulSoup(r.text, "html.parser").get_text(" ", strip=True)
            owner = _extract_owner_from_text(text)
            if owner:
                log("owner_extract", "SUCCESS", f"{business_name} | method=website | result={owner} | url={url}")
                return owner, "high", "website"
        except Exception:
            continue

    log("owner_extract", "FAIL", f"{business_name} | method=website | result=none")
    return "", "none", "none"


def _is_valid_email(email: str) -> bool:
    """
    Return True if the email passes quality filters.

    Parameters:
        email (str): Email address to validate.

    Returns:
        bool: True if the email should be kept, False if it should be discarded.
    """
    if len(email) > 60:
        return False
    parts = email.split("@")
    if len(parts) != 2:
        return False
    domain_part = parts[1]
    if "." not in domain_part:
        return False
    email_lower = email.lower()
    if any(term in email_lower for term in _EMAIL_BLOCK_TERMS):
        return False
    return True


def _extract_emails_from_text(text: str) -> list:
    """
    Extract and filter email addresses from raw HTML/text.

    Parameters:
        text (str): Raw page content.

    Returns:
        list: Unique, filtered email addresses.
    """
    raw = _EMAIL_PATTERN.findall(text)
    return [e for e in set(raw) if _is_valid_email(e)]


def _rank_emails(emails: list, domain: str) -> list:
    """
    Rank emails by quality. Domain-matched first, then personal providers, then any.

    Parameters:
        emails (list): List of candidate email addresses.
        domain (str): The business's root domain (e.g. "smithplumbing.com").

    Returns:
        list: Emails sorted from highest to lowest priority.
    """
    domain_matched = [e for e in emails if domain in e.lower()]
    personal = [
        e for e in emails
        if any(p in e.lower() for p in ["gmail", "yahoo", "hotmail", "outlook", "icloud"])
        and e not in domain_matched
    ]
    other = [e for e in emails if e not in domain_matched and e not in personal]
    return domain_matched + personal + other


def find_email(website: str, business_name: str = "") -> tuple:
    """
    5-step email extraction pipeline.

    Steps:
        1. Use Google Places email if pre-populated on the details dict.
        2. Scrape homepage for emails.
        3. Scrape known contact paths (/contact, /about, etc.) for emails.
        4. Rank all found emails by domain match, then personal provider, then any.
        5. Assign confidence level: verified (found on site) or none.

    Parameters:
        website (str): Business website URL.
        business_name (str): Business name for logging.

    Returns:
        tuple: (email: str, confidence: str) where confidence is 'verified' or 'none'.
    """
    if not website:
        log("email_extract", "FAIL", f"{business_name} | method=none | result=none | confidence=none")
        return "", "none"

    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    root_domain = website.replace("https://", "").replace("http://", "").split("/")[0].replace("www.", "")
    all_emails = []

    # STEP 2 — Homepage scrape
    try:
        r = requests.get(website, headers=headers, timeout=6, allow_redirects=True)
        if r.status_code == 200:
            found = _extract_emails_from_text(r.text)
            all_emails.extend(found)
    except Exception as e:
        log("email_extract", "WARN", f"{business_name} | homepage fetch failed: {e}")

    # STEP 3 — Contact page scrape
    base = website.rstrip("/")
    for path in _CONTACT_PATHS:
        try:
            r = requests.get(base + path, headers=headers, timeout=5, allow_redirects=True)
            if r.status_code == 200:
                found = _extract_emails_from_text(r.text)
                all_emails.extend(found)
        except Exception:
            pass

    # STEP 4 — Rank
    ranked = _rank_emails(list(set(all_emails)), root_domain)

    if ranked:
        chosen = ranked[0]
        log("email_extract", "SUCCESS", f"{business_name} | method=website | result={chosen} | confidence=verified")
        return chosen, "verified"

    log("email_extract", "FAIL", f"{business_name} | method=website | result=none | confidence=none")
    return "", "none"


def search_places(query: str) -> list:
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {"query": query, "key": GOOGLE_KEY}
    try:
        r = requests.get(url, params=params, timeout=10)
        return r.json().get("results", [])
    except Exception as e:
        log("search_places", "ERROR", str(e))
        return []


def get_place_details(place_id: str) -> dict:
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "name,formatted_phone_number,website,rating,user_ratings_total,formatted_address,opening_hours",
        "key": GOOGLE_KEY,
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        return r.json().get("result", {})
    except Exception as e:
        log("get_place_details", "ERROR", str(e))
        return {}


def passes_criteria(place: dict, name: str) -> bool:
    reviews = place.get("user_ratings_total", 0)
    name_lower = name.lower()
    for kw in SKIP_KEYWORDS:
        if kw in name_lower:
            return False
    if reviews > 300:
        return False
    return True


def parse_city_state(address: str, hint_city: str, hint_state: str) -> tuple:
    """Extract city and state from formatted_address."""
    parts = [p.strip() for p in address.split(",")]
    # Typical format: "123 Main St, City, ST 12345, USA"
    if len(parts) >= 3:
        city = parts[-3] if len(parts) >= 4 else hint_city
        state_zip = parts[-2] if len(parts) >= 3 else hint_state
        state_match = re.match(r'([A-Z]{2})', state_zip.strip())
        state = state_match.group(1) if state_match else hint_state
        return city or hint_city, state or hint_state
    return hint_city, hint_state


def run_scraper(cities_filter=None):
    """
    Main scrape function. cities_filter = list of (city, state) tuples to limit scope.
    Returns (email_leads, call_leads) lists of dicts.
    """
    log("scraper_start", "INFO", f"Starting scrape | cities_filter={cities_filter}")
    print("\nFORGE Scraper — Starting...\n")

    existing = load_existing_leads()
    email_leads = []
    call_leads = []

    queries = SEARCH_QUERIES
    if cities_filter:
        filter_set = {(c.lower(), s.upper()) for c, s in cities_filter}
        queries = [
            (q, c, s) for (q, c, s) in SEARCH_QUERIES
            if (c.lower(), s.upper()) in filter_set
        ]

    print(f"Running {len(queries)} queries...\n")

    for query, hint_city, hint_state in queries:
        print(f"\nSearching: {query}")
        results = search_places(query)
        time.sleep(0.3)

        for place in results:
            name = place.get("name", "").strip()
            if not name or name.lower() in existing:
                continue
            if not passes_criteria(place, name):
                print(f"  Skipping chain: {name}")
                continue

            details = get_place_details(place["place_id"])
            time.sleep(0.2)

            phone = details.get("formatted_phone_number", "")
            website = details.get("website", "")
            address = details.get("formatted_address", "")
            city, state = parse_city_state(address, hint_city, hint_state)
            business_type = get_business_type(name, query)
            rating = place.get("rating", 0)
            reviews = place.get("user_ratings_total", 0)
            has_hours = bool(details.get("opening_hours"))

            details["opening_hours"] = has_hours

            print(f"  Scoring {name}...")
            score, website_status, notes = score_lead(details, website, city, state)

            if website_status == "solid_website":
                print(f"  SKIP: {name} — solid website")
                existing.add(name.lower())
                log("score_lead", "SKIP", f"{name} — solid website")
                continue

            tier = get_tier(score)
            if tier == "LOW":
                print(f"  SKIP: {name} — LOW score ({score})")
                existing.add(name.lower())
                log("score_lead", "SKIP", f"{name} — LOW score {score}")
                continue

            email, email_confidence = find_email(website, business_name=name)

            owner_name, owner_confidence, owner_source = find_owner_name(website, business_name=name, email=email)
            site_tier = "premium" if tier == "HOT" else "standard"
            lead = {
                "business_name": name,
                "owner_name": owner_name,
                "owner_confidence": owner_confidence,
                "owner_source": owner_source,
                "email": email,
                "email_confidence": email_confidence,
                "phone": phone,
                "city": city,
                "state": state,
                "business_type": business_type,
                "google_rating": rating,
                "review_count": reviews,
                "website_url": website,
                "website_status": website_status,
                "score": score,
                "lead_tier": tier,
                "site_tier": site_tier,
                "date_scraped": datetime.datetime.now().strftime("%Y-%m-%d"),
                "demo_site_path": "",
                "email_sent": "false",
                "email_sent_date": "",
                "reply_status": "none",
            }

            existing.add(name.lower())

            if email:
                email_leads.append(lead)
                print(f"  [{tier}] EMAIL: {name} | score {score} | {email}")
                log("lead_found", "SUCCESS", f"{name} | {tier} | score={score} | {email}")
            else:
                call_leads.append(lead)
                print(f"  [{tier}] CALL: {name} | score {score} | {phone}")
                log("lead_found", "INFO", f"{name} | {tier} | score={score} | phone_only")

    # Sort: HOT first, then WARM
    def tier_order(lead):
        return 0 if lead["lead_tier"] == "HOT" else 1

    email_leads.sort(key=tier_order)
    call_leads.sort(key=tier_order)

    return email_leads, call_leads


def save_leads(email_leads, call_leads):
    """Persist new leads via storage layer (CSV or Postgres)."""
    from storage.leads_storage import save_leads as _persist
    _persist(email_leads, call_leads)


def backfill_owner_names(csv_path: str = LEADS_CSV, limit: int = 0) -> dict:
    """
    Backfill missing owner_name values in an existing leads CSV.

    Parameters:
        csv_path (str): Path to leads CSV to update.
        limit (int): Optional max number of rows to process (0 = all).

    Returns:
        dict: Summary with scanned, updated, already_filled, and unresolved counts.
    """
    if not os.path.exists(csv_path):
        return {"scanned": 0, "updated": 0, "already_filled": 0, "unresolved": 0}

    with open(csv_path, "r", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    if "owner_name" not in fieldnames:
        raise ValueError(f"'owner_name' column not found in {csv_path}")
    if "owner_confidence" not in fieldnames:
        fieldnames.insert(fieldnames.index("owner_name") + 1, "owner_confidence")
        for row in rows:
            row["owner_confidence"] = row.get("owner_confidence", "none")
    if "owner_source" not in fieldnames:
        idx = fieldnames.index("owner_confidence") + 1 if "owner_confidence" in fieldnames else fieldnames.index("owner_name") + 1
        fieldnames.insert(idx, "owner_source")
        for row in rows:
            row["owner_source"] = row.get("owner_source", "none")

    scanned = 0
    updated = 0
    already_filled = 0
    unresolved = 0

    for row in rows:
        current_owner = (row.get("owner_name") or "").strip()
        existing_conf = _owner_confidence_from_existing_name(current_owner, row.get("email", ""))
        if current_owner and existing_conf != "none":
            row["owner_confidence"] = existing_conf
            row["owner_source"] = _owner_source_from_existing_name(current_owner, row.get("email", ""))
            already_filled += 1
            continue
        if current_owner and existing_conf == "none":
            row["owner_name"] = ""
            row["owner_confidence"] = "none"
            row["owner_source"] = "none"

        if limit and scanned >= limit:
            break

        scanned += 1
        business_name = (row.get("business_name") or row.get("name") or "").strip()
        website = (row.get("website_url") or "").strip()
        email = (row.get("email") or "").strip()

        owner, confidence, source = find_owner_name(website=website, business_name=business_name, email=email)
        if owner:
            row["owner_name"] = owner
            row["owner_confidence"] = confidence
            row["owner_source"] = source
            updated += 1
        else:
            row["owner_confidence"] = "none"
            row["owner_source"] = "none"
            unresolved += 1

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "scanned": scanned,
        "updated": updated,
        "already_filled": already_filled,
        "unresolved": unresolved,
    }
    log("owner_backfill", "INFO", f"{os.path.basename(csv_path)} | {summary}")
    return summary


def main(cities_filter=None):
    email_leads, call_leads = run_scraper(cities_filter)
    save_leads(email_leads, call_leads)
    hot = sum(1 for l in email_leads + call_leads if l["lead_tier"] == "HOT")
    warm = sum(1 for l in email_leads + call_leads if l["lead_tier"] == "WARM")
    print(f"\nTotal: {len(email_leads)} to email, {len(call_leads)} to call")
    print(f"HOT: {hot} | WARM: {warm}")
    log("scraper_complete", "SUCCESS", f"email={len(email_leads)} call={len(call_leads)} hot={hot} warm={warm}")
    return email_leads, call_leads


if __name__ == "__main__":
    main()
