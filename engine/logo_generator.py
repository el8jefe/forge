"""
logo_generator.py — FORGE Logo System
Generates SVG logomarks and icon sets for every supported business type.
No emojis. No stock icons. Clean geometric SVG paths only.
"""

# ─── BUSINESS ICONS ───────────────────────────────────────────────────────────
# Each entry is a raw SVG <path> or <g> block that sits inside a
# viewBox="0 0 24 24" coordinate space.
# stroke="currentColor" so the parent can set color via CSS.

ICONS = {
    "hvac": """
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z" fill="none" stroke="currentColor" stroke-width="1.4"/>
        <path d="M12 6v6l4 2" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M8 2.5C6 4 4.5 6 4 8.5" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M16 2.5C18 4 19.5 6 20 8.5" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M7 17c1.3 1.3 3 2 5 2s3.7-.7 5-2" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
    """,
    "plumber": """
        <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
    """,
    "electrician": """
        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
    """,
    "roofer": """
        <polyline points="3 9 12 2 21 9" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
        <rect x="5" y="9" width="14" height="13" rx="0" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M9 22V12h6v10" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
    """,
    "landscaper": """
        <path d="M12 22V12" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M12 12C12 12 8 8 4 9c0 5 4 7 8 3" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M12 12C12 12 16 7 20 8c0 6-4 8-8 4" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M5 22h14" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
    """,
    "pest control": """
        <path d="M12 22c-4.97 0-9-2.69-9-6 0-1.66 1-3.16 2.63-4.25" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M12 22c4.97 0 9-2.69 9-6 0-1.66-1-3.16-2.63-4.25" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8z" fill="none" stroke="currentColor" stroke-width="1.4"/>
        <path d="M12 8V4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M6 6l2.5 3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M18 6l-2.5 3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M4 13l2.5.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M20 13l-2.5.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
    """,
    "auto detailing": """
        <rect x="1" y="3" width="15" height="13" rx="2" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M16 8h4l3 3v5h-7V8z" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
        <circle cx="5.5" cy="18.5" r="2.5" fill="none" stroke="currentColor" stroke-width="1.4"/>
        <circle cx="18.5" cy="18.5" r="2.5" fill="none" stroke="currentColor" stroke-width="1.4"/>
    """,
    "pressure washing": """
        <path d="M3 3h7v7H3z" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M10 6.5h4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M14 6.5l3.5-3.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M14 6.5l3.5 3.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M6 10v4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M6 14l-3 5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M6 14l3 5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M9 19l3 2" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M3 19l-1 2" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
    """,
    "pool service": """
        <path d="M2 12h20" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M2 17c1.5-1 3-1 4.5 0s3 1 4.5 0 3-1 4.5 0 3 1 4.5 0" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M2 7c1.5-1 3-1 4.5 0s3 1 4.5 0 3-1 4.5 0 3 1 4.5 0" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <circle cx="12" cy="4" r="1.5" fill="none" stroke="currentColor" stroke-width="1.4"/>
    """,
    "carpet cleaning": """
        <rect x="2" y="4" width="20" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="1.4"/>
        <path d="M6 8h12" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-dasharray="2 2"/>
        <path d="M6 12h12" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-dasharray="2 2"/>
        <path d="M6 16h12" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-dasharray="2 2"/>
    """,
    "moving company": """
        <rect x="1" y="3" width="15" height="13" rx="1" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M16 8h4l3 3v5h-7V8z" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
        <circle cx="5.5" cy="18.5" r="2.5" fill="none" stroke="currentColor" stroke-width="1.4"/>
        <circle cx="18.5" cy="18.5" r="2.5" fill="none" stroke="currentColor" stroke-width="1.4"/>
        <path d="M8 9l3-3 3 3" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M11 6v6" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
    """,
    "appliance repair": """
        <rect x="2" y="3" width="20" height="18" rx="2" fill="none" stroke="currentColor" stroke-width="1.4"/>
        <path d="M2 9h20" stroke="currentColor" stroke-width="1.4"/>
        <circle cx="7" cy="6" r="1" fill="currentColor"/>
        <circle cx="11" cy="6" r="1" fill="currentColor"/>
        <path d="M14.7 13.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l1.6-1.6a1 1 0 0 0 0-1.4l-1.6-1.6a1 1 0 0 0-1.4 0l-1.6 1.6z" fill="none" stroke="currentColor" stroke-width="1.2"/>
        <path d="M7 13h5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M7 17h3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
    """,
    "house painting": """
        <path d="M18 3a3 3 0 0 1 3 3 3 3 0 0 1-3 3 3 3 0 0 1-3-3 3 3 0 0 1 3-3" fill="none" stroke="currentColor" stroke-width="1.4"/>
        <path d="M15 9l-3 3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M9.5 13.5l-6.5 6.5a1.5 1.5 0 0 0 2.1 2.1L11.5 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M8 16l-1.5 1.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
    """,
    "handyman": """
        <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
    """,
    "tree service": """
        <path d="M12 22V12" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M12 12L8 8" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M12 16l4-3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M5 3l14 0" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M5 3C5 3 4 8 8 10c1.5.7 3 .5 4 0" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M19 3C19 3 20 8 16 10c-1.5.7-3 .5-4 0" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M7 10C7 10 5 14 9 16c1.5.6 3 .4 4-.5" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M17 10C17 10 19 14 15 16c-1.5.6-3 .4-4-.5" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
    """,
    "masonry": """
        <rect x="2" y="14" width="8" height="4" rx="0" fill="none" stroke="currentColor" stroke-width="1.4"/>
        <rect x="14" y="14" width="8" height="4" rx="0" fill="none" stroke="currentColor" stroke-width="1.4"/>
        <rect x="8" y="10" width="8" height="4" rx="0" fill="none" stroke="currentColor" stroke-width="1.4"/>
        <rect x="2" y="18" width="8" height="4" rx="0" fill="none" stroke="currentColor" stroke-width="1.4"/>
        <rect x="14" y="18" width="8" height="4" rx="0" fill="none" stroke="currentColor" stroke-width="1.4"/>
        <rect x="4" y="6" width="6" height="4" rx="0" fill="none" stroke="currentColor" stroke-width="1.4"/>
        <rect x="14" y="6" width="6" height="4" rx="0" fill="none" stroke="currentColor" stroke-width="1.4"/>
    """,
    "window cleaning": """
        <rect x="3" y="3" width="18" height="18" rx="1" fill="none" stroke="currentColor" stroke-width="1.4"/>
        <path d="M3 12h18" stroke="currentColor" stroke-width="1.4"/>
        <path d="M12 3v18" stroke="currentColor" stroke-width="1.4"/>
        <path d="M6 7.5l2 2" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
    """,
    "junk removal": """
        <polyline points="3 6 5 6 21 6" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M10 11l.01 6" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M14 11l-.01 6" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
    """,
    "garage door repair": """
        <rect x="2" y="4" width="20" height="16" rx="1" fill="none" stroke="currentColor" stroke-width="1.4"/>
        <path d="M2 10h20" stroke="currentColor" stroke-width="1.4"/>
        <path d="M2 15h20" stroke="currentColor" stroke-width="1.4"/>
        <path d="M8 20v2" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M16 20v2" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M7 7.5h10" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-dasharray="2 2"/>
        <path d="M7 12.5h10" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-dasharray="2 2"/>
    """,
    "locksmith": """
        <rect x="5" y="11" width="14" height="11" rx="2" fill="none" stroke="currentColor" stroke-width="1.4"/>
        <path d="M7 11V7a5 5 0 0 1 10 0v4" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <circle cx="12" cy="16" r="1.5" fill="currentColor"/>
        <path d="M12 17.5v2" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
    """,
    "mobile mechanic": """
        <circle cx="12" cy="12" r="3" fill="none" stroke="currentColor" stroke-width="1.4"/>
        <path d="M12 2v3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M12 19v3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M4.22 4.22l2.12 2.12" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M17.66 17.66l2.12 2.12" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M2 12h3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M19 12h3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M4.22 19.78l2.12-2.12" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M17.66 6.34l2.12-2.12" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
    """,
    "boat detailing": """
        <path d="M3 17l2.5-7H18.5l2.5 7z" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M3 17c0 0 2 2 9 2s9-2 9-2" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M12 10V4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M8 4h8" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
    """,
    "fence installation": """
        <path d="M4 3v18" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M12 3v18" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M20 3v18" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M2 8h20" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M2 16h20" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M4 3l-2-2" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M4 3l2-2" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M12 3l-2-2" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M12 3l2-2" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M20 3l-2-2" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M20 3l2-2" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
    """,
    "gutter service": """
        <path d="M3 4h18v4H3z" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M21 8l-2 10H5L3 8" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M10 18v2" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M14 18v2" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M10 20c0 1-1 1.5-1 1.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
        <path d="M14 20c0 1 1 1.5 1 1.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
    """,
    "drywall repair": """
        <rect x="2" y="3" width="20" height="18" rx="1" fill="none" stroke="currentColor" stroke-width="1.4"/>
        <path d="M9 3v18" stroke="currentColor" stroke-width="1.4" stroke-dasharray="3 2"/>
        <path d="M15 3v18" stroke="currentColor" stroke-width="1.4" stroke-dasharray="3 2"/>
        <path d="M2 9h7" stroke="currentColor" stroke-width="1.4" stroke-dasharray="3 2"/>
        <path d="M15 14h7" stroke="currentColor" stroke-width="1.4" stroke-dasharray="3 2"/>
    """,
    "flooring installation": """
        <rect x="2" y="14" width="5" height="8" fill="none" stroke="currentColor" stroke-width="1.4"/>
        <rect x="9.5" y="14" width="5" height="8" fill="none" stroke="currentColor" stroke-width="1.4"/>
        <rect x="17" y="14" width="5" height="8" fill="none" stroke="currentColor" stroke-width="1.4"/>
        <rect x="5" y="6" width="5" height="8" fill="none" stroke="currentColor" stroke-width="1.4"/>
        <rect x="14" y="6" width="5" height="8" fill="none" stroke="currentColor" stroke-width="1.4"/>
        <rect x="2" y="2" width="8" height="4" fill="none" stroke="currentColor" stroke-width="1.4"/>
        <rect x="14" y="2" width="8" height="4" fill="none" stroke="currentColor" stroke-width="1.4"/>
    """,
    "barbershop": """
        <path d="M6 2v10" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M18 2v10" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M6 12c0 3.31 2.69 6 6 6s6-2.69 6-6" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M12 18v4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M9 22h6" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M6 2c0 0 2 2 6 2s6-2 6-2" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
    """,
    "restaurant": """
        <path d="M3 2v7c0 1.66 1.34 3 3 3h2a3 3 0 0 0 3-3V2" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M7 2v20" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M21 2c0 0 0 8-4 10v10" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
    """,
    "salon": """
        <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
    """,
    "florist": """
        <path d="M12 22V12" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M12 12C8 12 5 9.5 5 6.5A3.5 3.5 0 0 1 12 6a3.5 3.5 0 0 1 7 .5C19 9.5 16 12 12 12z" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M5 22h14" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <path d="M8.5 22c0-3 1.5-5 3.5-5s3.5 2 3.5 5" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
    """,
}

# Fallback for any type not in the dict above
_FALLBACK_ICON = """
    <circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="1.4"/>
    <path d="M12 8v4l3 2" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
"""

# ─── SERVICE-LEVEL ICON SETS ──────────────────────────────────────────────────
# Each business type gets 6 unique per-service icons.
# Indexed to match the order in SERVICES in site_builder.py.

SERVICE_ICONS = {
    "hvac": [
        # AC Installation & Repair
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="6" width="20" height="12" rx="2"/><path d="M6 12h12"/><path d="M8 9l-2 3 2 3"/><path d="M16 9l2 3-2 3"/></svg>',
        # Heating
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M12 2c0 6-6 6-6 12a6 6 0 0 0 12 0c0-6-6-6-6-12z"/><path d="M12 12c0 3-2 3-2 6a2 2 0 0 0 4 0c0-3-2-3-2-6z"/></svg>',
        # Air Quality
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M9.59 4.59A2 2 0 1 1 11 8H2m10.59 11.41A2 2 0 1 0 14 16H2m15.73-8.27A2.5 2.5 0 1 1 19.5 12H2"/></svg>',
        # Emergency
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
        # Maintenance
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>',
        # Duct Cleaning
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><rect x="2" y="9" width="20" height="6" rx="1"/><path d="M7 9V5"/><path d="M12 9V4"/><path d="M17 9V5"/></svg>',
    ],
    "plumber": [
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 7H3a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h18a1 1 0 0 0 1-1V8a1 1 0 0 0-1-1z"/><path d="M7 7V5a1 1 0 0 1 1-1h8a1 1 0 0 1 1 1v2"/><path d="M7 17v2"/><path d="M17 17v2"/></svg>',
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>',
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/><circle cx="12" cy="9" r="2.5"/></svg>',
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><path d="M12 8v4l3 2"/></svg>',
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>',
    ],
    "electrician": [
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="8" height="20" rx="1"/><rect x="14" y="2" width="8" height="20" rx="1"/><path d="M6 7h0"/><path d="M6 12h0"/><path d="M6 17h0"/><path d="M18 7h0"/><path d="M18 12h0"/><path d="M18 17h0"/></svg>',
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8"/><path d="M12 17v4"/></svg>',
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><circle cx="12" cy="12" r="2"/><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>',
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="2" width="14" height="20" rx="2"/><path d="M10 8h4"/><path d="M10 12h4"/><path d="M10 16h2"/></svg>',
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><path d="M9 15l2 2 4-4"/></svg>',
    ],
    "roofer": [
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 9 12 2 21 9"/><rect x="5" y="9" width="14" height="13"/><path d="M9 22V12h6v10"/></svg>',
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>',
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>',
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M9 22V12h6v10"/></svg>',
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><path d="M9 15l2 2 4-4"/></svg>',
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/></svg>',
    ],
    "landscaper": [
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M12 22V12M12 12C8 12 5 9.5 5 6.5A3.5 3.5 0 0 1 12 6a3.5 3.5 0 0 1 7 .5C19 9.5 16 12 12 12z"/><path d="M5 22h14"/></svg>',
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="4" r="2"/><path d="M4 20h16"/><path d="M6 20l2-8h8l2 8"/><path d="M8 12C8 8 10 6 12 4c2 2 4 4 4 8"/></svg>',
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22V12M8 2.5C8 2.5 6 8 10 10c1.4.7 2 .5 2-.5M16 2.5C16 2.5 18 8 14 10c-1.4.7-2 .5-2-.5"/></svg>',
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><circle cx="12" cy="8" r="5"/><path d="M12 13v9"/><path d="M9 22h6"/><path d="M7 10c-1.5 0-3 1-3 3s1.5 3 3 3"/><path d="M17 10c1.5 0 3 1 3 3s-1.5 3-3 3"/></svg>',
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>',
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><path d="M4 22v-7"/></svg>',
    ],
    "barbershop": [
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M20 4L8.12 15.88"/><path d="M14.47 14.48L20 20"/><path d="M8.12 8.12L12 12"/></svg>',
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M6 2v10M18 2v10M6 12c0 3.31 2.69 6 6 6s6-2.69 6-6M12 18v4M9 22h6M6 2c0 0 2 2 6 2s6-2 6-2"/></svg>',
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>',
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z"/><path d="M9 12l2 2 4-4"/></svg>',
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M5 3l14 0M5 3C5 3 4 8 8 10c1.5.7 3 .5 4 0M19 3C19 3 20 8 16 10c-1.5.7-3 .5-4 0M12 10v12M9 22h6"/></svg>',
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><circle cx="12" cy="7" r="4"/><path d="M6 21v-2a6 6 0 0 1 6-6h0a6 6 0 0 1 6 6v2"/></svg>',
    ],
}

# Default 6-icon set used for any business type not listed above
_DEFAULT_SERVICE_ICONS = [
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>',
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>',
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><path d="M12 8v4l3 2"/></svg>',
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>',
]


def get_logo_icon_svg(business_type: str, size: int = 24, css_class: str = "") -> str:
    """
    Return a full <svg> element with the icon for the given business type.

    Args:
        business_type: Canonical key (e.g. 'hvac', 'plumber').
        size: Width/height in px.
        css_class: Optional CSS class string.

    Returns:
        str: Complete <svg> HTML.
    """
    btype = business_type.lower().strip()
    paths = ICONS.get(btype, _FALLBACK_ICON)
    cls = f' class="{css_class}"' if css_class else ""
    return (
        f'<svg{cls} xmlns="http://www.w3.org/2000/svg" '
        f'width="{size}" height="{size}" viewBox="0 0 24 24" '
        f'aria-hidden="true">{paths}</svg>'
    )


def get_logo_html(
    business_name: str,
    business_type: str,
    accent_color: str = "#c9a84c",
    bg_color: str = "#0a0a0a",
    text_color: str = "#f5f5f0",
    icon_size: int = 20,
) -> str:
    """
    Build the complete logo HTML: icon mark + business name wordmark.
    Used in the nav and footer.

    Args:
        business_name: The business display name.
        business_type: Canonical business type key.
        accent_color: Icon background / highlight color.
        bg_color: Dark background (used for icon mark square).
        text_color: Text color for the name.
        icon_size: Icon SVG size in px.

    Returns:
        str: HTML string for the logo block.
    """
    icon_svg = get_logo_icon_svg(business_type, size=icon_size)
    return f"""<span class="logo-mark" style="background:{accent_color};color:{bg_color};">{icon_svg}</span><span class="logo-name" style="color:{text_color};">{business_name}</span>"""


def get_service_icons(business_type: str) -> list:
    """
    Return the list of 6 SVG icon strings for a business type's service cards.

    Args:
        business_type: Canonical key.

    Returns:
        list[str]: List of SVG HTML strings.
    """
    btype = business_type.lower().strip()
    return SERVICE_ICONS.get(btype, _DEFAULT_SERVICE_ICONS)
