import requests
from bs4 import BeautifulSoup
import csv
import os
import subprocess
import shutil
import re
import json
import sys
import random
from dotenv import load_dotenv
from system_logger import log
from logo_generator import get_logo_html, get_service_icons

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME", "el8jefe")
UNSPLASH_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SITES_DIR = os.path.join(SCRIPT_DIR, "sites")
os.makedirs(SITES_DIR, exist_ok=True)

# Unsplash keyword map per business type
UNSPLASH_QUERIES = {
    "hvac": ["HVAC technician working", "air conditioning unit", "heating system installation"],
    "plumber": ["plumber working pipes", "plumbing repair", "water pipe professional"],
    "electrician": ["electrician panel wiring", "electrical work professional", "circuit breaker repair"],
    "roofer": ["roofing contractor shingles", "roof repair worker", "roofing installation crew"],
    "landscaper": ["lawn care professional", "landscaping garden beautiful", "gardener mowing lawn"],
    "pest control": ["pest control professional", "exterminator spraying", "pest inspection home"],
    "auto detailing": ["car detailing professional", "auto detail ceramic coating", "car wash professional polish"],
    "pressure washing": ["pressure washing driveway", "power wash house exterior", "pressure washer professional"],
    "pool service": ["swimming pool maintenance", "pool cleaning professional", "pool water treatment"],
    "carpet cleaning": ["carpet cleaning machine", "professional carpet steam clean", "upholstery cleaning service"],
    "moving company": ["professional movers truck", "moving boxes furniture", "residential moving service"],
    "appliance repair": ["appliance repair technician", "washing machine repair", "refrigerator service professional"],
    "house painting": ["interior house painting", "exterior painting contractor", "professional painter wall"],
    "handyman": ["handyman tools work", "home repair professional", "handyman fixing fixture"],
    "tree service": ["tree removal professional", "arborist cutting tree", "stump grinding service"],
    "masonry": ["concrete masonry work", "brick wall professional", "retaining wall construction"],
    "window cleaning": ["window cleaning professional", "squeegee window clean", "commercial window washing"],
    "junk removal": ["junk removal truck", "cleanout service professional", "debris hauling"],
    "garage door repair": ["garage door repair", "garage door spring replacement", "garage door professional"],
    "locksmith": ["locksmith service professional", "lock rekeying service", "locksmith at work"],
    "mobile mechanic": ["mobile mechanic car repair", "mechanic working engine", "roadside car service"],
    "boat detailing": ["boat detailing professional", "yacht cleaning polish", "marine detailing service"],
    "fence installation": ["fence installation wood", "vinyl fence professional", "fence contractor building"],
    "gutter service": ["gutter cleaning professional", "gutter guard installation", "roof gutter service"],
    "drywall repair": ["drywall repair professional", "drywall patch smooth", "interior wall repair"],
    "flooring installation": ["tile floor installation", "hardwood floor laying professional", "flooring contractor work"],
    "barbershop": ["barber shop interior", "barber cutting hair", "barbershop atmosphere"],
    "restaurant": ["restaurant dining ambiance", "chef cooking kitchen", "food plating restaurant"],
    "salon": ["hair salon interior", "stylist cutting hair", "hair salon professional"],
    "florist": ["florist arranging flowers", "flower shop bouquet", "floral arrangement beautiful"],
}

# Fallback gradient backgrounds per type (used if Unsplash fails)
FALLBACK_GRADIENTS = {
    "hvac": "linear-gradient(135deg, #0d1b2a 0%, #1e3a5f 100%)",
    "plumber": "linear-gradient(135deg, #111827 0%, #1e3a5f 100%)",
    "electrician": "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)",
    "roofer": "linear-gradient(135deg, #1c1917 0%, #3b2a1a 100%)",
    "landscaper": "linear-gradient(135deg, #14532d 0%, #052e16 100%)",
    "pest control": "linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)",
    "auto detailing": "linear-gradient(135deg, #0d1117 0%, #1a1f2e 100%)",
    "pressure washing": "linear-gradient(135deg, #0a1628 0%, #1e3a5f 100%)",
    "pool service": "linear-gradient(135deg, #0a1f2e 0%, #0d3349 100%)",
    "carpet cleaning": "linear-gradient(135deg, #1a0f0f 0%, #2e1a1a 100%)",
    "moving company": "linear-gradient(135deg, #111827 0%, #1f2937 100%)",
    "appliance repair": "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)",
    "house painting": "linear-gradient(135deg, #1a1207 0%, #2e2010 100%)",
    "handyman": "linear-gradient(135deg, #1a1207 0%, #332b14 100%)",
    "tree service": "linear-gradient(135deg, #0a1f0a 0%, #14321a 100%)",
    "masonry": "linear-gradient(135deg, #1a1610 0%, #2e2818 100%)",
    "window cleaning": "linear-gradient(135deg, #0a1628 0%, #162440 100%)",
    "junk removal": "linear-gradient(135deg, #111111 0%, #1f1f1f 100%)",
    "garage door repair": "linear-gradient(135deg, #0f1117 0%, #1a1f2e 100%)",
    "locksmith": "linear-gradient(135deg, #14100a 0%, #241c10 100%)",
    "mobile mechanic": "linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 100%)",
    "boat detailing": "linear-gradient(135deg, #041d2e 0%, #0a3348 100%)",
    "fence installation": "linear-gradient(135deg, #101a0a 0%, #1a2e10 100%)",
    "gutter service": "linear-gradient(135deg, #0f1a28 0%, #1a2e40 100%)",
    "drywall repair": "linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%)",
    "flooring installation": "linear-gradient(135deg, #1a1206 0%, #2e1e0a 100%)",
    "barbershop": "linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%)",
    "restaurant": "linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)",
    "salon": "linear-gradient(135deg, #1c1c1c 0%, #2d2d2d 100%)",
    "florist": "linear-gradient(135deg, #052e16 0%, #14532d 100%)",
}


def fetch_unsplash_images(business_type: str, count: int = 3) -> list:
    """
    Fetch up to `count` images from Unsplash for the given business type.
    Each result is a dict with url, photographer_name, photographer_url, download_location.
    Falls back to empty dicts on any failure.

    Parameters:
        business_type (str): Canonical business type key.
        count (int): Number of images to fetch.

    Returns:
        list: List of image info dicts. Missing images are represented as empty dicts.
    """
    empty = {}

    if not UNSPLASH_KEY or UNSPLASH_KEY in ("your_unsplash_key_here", ""):
        log("unsplash_fetch", "SKIP", "No Unsplash API key configured")
        return [empty] * count

    btype = business_type.lower()
    queries = UNSPLASH_QUERIES.get(btype, UNSPLASH_QUERIES.get("hvac", []))
    results_list = []

    for query in queries[:count]:
        try:
            resp = requests.get(
                "https://api.unsplash.com/search/photos",
                params={
                    "query": query,
                    "per_page": 3,
                    "orientation": "landscape",
                    "content_filter": "high",
                },
                headers={"Authorization": f"Client-ID {UNSPLASH_KEY}"},
                timeout=8,
            )
            results = resp.json().get("results", [])
            if results:
                chosen = random.choice(results[:3])
                img = {
                    "url": chosen["urls"]["regular"],
                    "photographer_name": chosen.get("user", {}).get("name", ""),
                    "photographer_url": chosen.get("user", {}).get("links", {}).get("html", "https://unsplash.com"),
                    "download_location": chosen.get("links", {}).get("download_location", ""),
                }
                results_list.append(img)
                log("unsplash_fetch", "SUCCESS", f"{query} -> {img['url'][:60]}")
            else:
                results_list.append(empty)
        except Exception as e:
            log("unsplash_fetch", "ERROR", str(e))
            results_list.append(empty)

    while len(results_list) < count:
        results_list.append(empty)

    return results_list

TEMPLATES = {
    "barbershop": {
        "bg": "#0a0a0a",
        "text": "#f0ece4",
        "accent": "#c9a84c",
        "accent2": "#1a1a1a",
        "font_heading": "Playfair Display",
        "font_body": "Inter",
        "hero_image": "https://images.unsplash.com/photo-1585747860715-2ba37e788b70?w=1600",
        "hero_tag": "Premium Barbershop",
        "hero_h1": "Sharp Cuts.<br/>Clean Lines.",
        "hero_sub": "Traditional craft meets modern style. Book your appointment today.",
        "cta": "Book Appointment",
        "nav_style": "dark",
    },
    "restaurant": {
        "bg": "#fafaf8",
        "text": "#1a1a2e",
        "accent": "#1a1a2e",
        "accent2": "#f0ece4",
        "font_heading": "Cormorant Garamond",
        "font_body": "Inter",
        "hero_image": "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=1600",
        "hero_tag": "Fine Dining",
        "hero_h1": "An Unforgettable<br/>Experience.",
        "hero_sub": "Exceptional cuisine, warm atmosphere, and memories that last.",
        "cta": "Reserve a Table",
        "nav_style": "light",
    },
    "salon": {
        "bg": "#fdfcfb",
        "text": "#2c2c2c",
        "accent": "#b8896e",
        "accent2": "#f5ede8",
        "font_heading": "Cormorant Garamond",
        "font_body": "Inter",
        "hero_image": "https://images.unsplash.com/photo-1560066984-138dadb4c035?w=1600",
        "hero_tag": "Premium Hair Salon",
        "hero_h1": "Look Good.<br/>Feel Amazing.",
        "hero_sub": "Expert stylists dedicated to bringing out your best look.",
        "cta": "Book Your Visit",
        "nav_style": "light",
    },
    "florist": {
        "bg": "#fdf9f6",
        "text": "#2c2c2c",
        "accent": "#8faa7e",
        "accent2": "#f0ece4",
        "font_heading": "Cormorant Garamond",
        "font_body": "Inter",
        "hero_image": "https://images.unsplash.com/photo-1487530811015-780f3ca3cfe4?w=1600",
        "hero_tag": "Premium Florist",
        "hero_h1": "Beautiful Flowers<br/>For Every Moment.",
        "hero_sub": "Handcrafted arrangements for weddings, events, and everyday beauty.",
        "cta": "Order Now",
        "nav_style": "light",
    },
    "hvac": {
        "bg": "#0d1b2a",
        "text": "#e2e8f0",
        "accent": "#f97316",
        "accent2": "#112236",
        "font_heading": "Playfair Display",
        "font_body": "Inter",
        "hero_image": "https://images.unsplash.com/photo-1504328345606-18bbc8c9d7d1?w=1600",
        "hero_tag": "HVAC Services",
        "hero_h1": "Comfort All<br/>Year Round.",
        "hero_sub": "Heating, cooling, and air quality solutions you can count on. Fast response, licensed technicians.",
        "cta": "Call Now",
        "nav_style": "dark",
    },
    "plumber": {
        "bg": "#111827",
        "text": "#f9fafb",
        "accent": "#3b82f6",
        "accent2": "#1f2937",
        "font_heading": "Playfair Display",
        "font_body": "Inter",
        "hero_image": "https://images.unsplash.com/photo-1585771724684-38269d6639fd?w=1600",
        "hero_tag": "Licensed Plumber",
        "hero_h1": "No Leak Too Big.<br/>No Job Too Small.",
        "hero_sub": "Fast, reliable plumbing service. Available when you need us most.",
        "cta": "Call Now",
        "nav_style": "dark",
    },
    "electrician": {
        "bg": "#0f172a",
        "text": "#f8fafc",
        "accent": "#eab308",
        "accent2": "#1e293b",
        "font_heading": "Playfair Display",
        "font_body": "Inter",
        "hero_image": "https://images.unsplash.com/photo-1621905251918-48416bd8575a?w=1600",
        "hero_tag": "Licensed Electrician",
        "hero_h1": "Powered By<br/>Experience.",
        "hero_sub": "Residential and commercial electrical work done right, done safe, done fast.",
        "cta": "Get a Quote",
        "nav_style": "dark",
    },
    "roofer": {
        "bg": "#1c1917",
        "text": "#f5f5f4",
        "accent": "#ef4444",
        "accent2": "#292524",
        "font_heading": "Playfair Display",
        "font_body": "Inter",
        "hero_image": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=1600",
        "hero_tag": "Roofing Contractor",
        "hero_h1": "Built to Last.<br/>Built to Protect.",
        "hero_sub": "Quality roofing installations, repairs, and inspections. Protecting homes and businesses.",
        "cta": "Free Estimate",
        "nav_style": "dark",
    },
    "landscaper": {
        "bg": "#14532d",
        "text": "#f0fdf4",
        "accent": "#22c55e",
        "accent2": "#166534",
        "font_heading": "Playfair Display",
        "font_body": "Inter",
        "hero_image": "https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=1600",
        "hero_tag": "Landscaping Services",
        "hero_h1": "Your Yard.<br/>Our Pride.",
        "hero_sub": "Professional lawn care, landscaping, and maintenance. Making your property shine.",
        "cta": "Get a Quote",
        "nav_style": "dark",
    },
}


SERVICES = {
    "hvac": [
        ("AC Installation & Repair", "Full system installs, tune-ups, and same-day emergency repairs to keep you cool all summer."),
        ("Heating Systems", "Furnace, heat pump, and boiler service for all makes and models."),
        ("Air Quality", "Filtration, humidifiers, and ventilation solutions for a healthier home."),
        ("Emergency Service", "24/7 availability — when your system fails, we respond fast."),
        ("Maintenance Plans", "Seasonal tune-ups that prevent costly breakdowns before they happen."),
        ("Duct Cleaning", "Improve airflow and indoor air quality with professional duct cleaning."),
    ],
    "plumber": [
        ("Drain Cleaning", "Clogged drains cleared fast with hydro-jetting and professional snaking."),
        ("Pipe Repair & Replace", "Burst pipes, corroded lines, and full repiping handled right."),
        ("Water Heater Service", "Tank and tankless installation, repair, and maintenance."),
        ("Emergency Plumbing", "Around-the-clock response for leaks, floods, and failures."),
        ("Sewer Line Repair", "Camera inspection, trenchless repair, and full replacements."),
        ("Leak Detection", "Non-invasive detection to find hidden leaks before they cause damage."),
    ],
    "electrician": [
        ("Panel Upgrades", "200-amp upgrades, breaker replacements, and load balancing."),
        ("Wiring & Rewiring", "New construction wiring and full home rewiring done to code."),
        ("Outlet & Switch Install", "GFCI outlets, USB ports, smart switches, and dimmer installs."),
        ("EV Charger Install", "Level 2 home charger installation for all EV makes and models."),
        ("Emergency Service", "24/7 response for electrical failures and safety hazards."),
        ("Home Inspections", "Full electrical inspection reports for buyers and sellers."),
    ],
    "roofer": [
        ("Roof Installation", "Full tear-off and installation with premium shingles and materials."),
        ("Roof Repair", "Leak patches, flashing repairs, and shingle replacement done fast."),
        ("Storm Damage", "Insurance claim assistance and rapid storm damage restoration."),
        ("Gutter Systems", "Seamless gutter installation, cleaning, and guard systems."),
        ("Roof Inspection", "Detailed inspection reports for insurance and peace of mind."),
        ("Commercial Roofing", "Flat roof systems, TPO, EPDM, and metal roofing solutions."),
    ],
    "landscaper": [
        ("Lawn Maintenance", "Weekly mowing, edging, blowing, and seasonal clean-ups."),
        ("Landscape Design", "Custom design plans that transform your outdoor space."),
        ("Tree & Shrub Care", "Trimming, shaping, removal, and stump grinding."),
        ("Irrigation Systems", "Design, installation, and repair of sprinkler systems."),
        ("Hardscaping", "Patios, walkways, retaining walls, and outdoor living spaces."),
        ("Seasonal Clean-Up", "Spring and fall clean-ups to keep your property looking sharp."),
    ],
    "barbershop": [
        ("Precision Cuts", "Classic and modern cuts tailored to your style and face shape."),
        ("Beard Trim & Shape", "Lineup, sculpt, and shape for a clean, defined look."),
        ("Hot Towel Shave", "Traditional straight razor shave with hot towel treatment."),
        ("Hair Treatment", "Deep conditioning and scalp treatments for healthy hair."),
        ("Fade & Taper", "Skin fades, tapers, and blends executed with expert precision."),
        ("Kids Cuts", "Patient, fun cuts for the little ones in a welcoming environment."),
    ],
    "restaurant": [
        ("Dine In", "An elevated dining experience in a warm, inviting atmosphere."),
        ("Private Events", "Custom menus and dedicated service for your special occasions."),
        ("Catering", "Full-service catering for corporate and private events."),
        ("Takeout", "Your favorite dishes ready for pick-up whenever you need them."),
        ("Weekend Brunch", "A beloved weekend tradition with fresh seasonal specials."),
        ("Chef's Menu", "A rotating tasting menu showcasing the best seasonal ingredients."),
    ],
    "salon": [
        ("Haircut & Style", "Precision cuts and blowouts for every hair type and length."),
        ("Color & Highlights", "Balayage, highlights, and full color by expert colorists."),
        ("Keratin Treatment", "Smoothing treatments for frizz-free, manageable hair."),
        ("Blowout", "A salon-quality blowout that keeps you looking great all week."),
        ("Extensions", "Tape-in, sew-in, and clip-in extensions using premium hair."),
        ("Scalp Treatments", "Deep conditioning and scalp therapy for healthy hair growth."),
    ],
    "florist": [
        ("Wedding Flowers", "Bouquets, centerpieces, and full floral design for your big day."),
        ("Custom Arrangements", "Bespoke designs crafted fresh for any occasion."),
        ("Same Day Delivery", "Fresh arrangements delivered the same day you order."),
        ("Corporate Flowers", "Weekly office arrangements and event florals for businesses."),
        ("Event Design", "Large-scale floral installations for galas and special events."),
        ("Sympathy Flowers", "Thoughtful arrangements to express your condolences with care."),
    ],
    "pest control": [
        ("Residential Pest Control", "Full-property treatment for ants, roaches, rodents, and more."),
        ("Termite Inspection", "Thorough inspection and treatment to protect your home's structure."),
        ("Bed Bug Treatment", "Heat and chemical treatments that eliminate infestations completely."),
    ],
    "auto detailing": [
        ("Full Detail", "Interior and exterior deep clean, polished to showroom condition."),
        ("Paint Correction", "Remove swirls, scratches, and oxidation with professional-grade polishing."),
        ("Ceramic Coating", "Long-lasting hydrophobic protection that keeps your car looking new."),
    ],
    "pressure washing": [
        ("Driveway Cleaning", "Blast away oil stains, grime, and years of buildup from concrete."),
        ("House Washing", "Safe soft-wash treatment for siding, brick, and painted surfaces."),
        ("Deck Restoration", "Clean, brighten, and restore wood and composite decking."),
    ],
    "pool service": [
        ("Weekly Maintenance", "Consistent chemical balancing, skimming, and equipment checks."),
        ("Chemical Balancing", "Precise pH and sanitizer adjustment for safe, clear water."),
        ("Equipment Repair", "Pump, filter, and heater diagnosis and repair by certified technicians."),
    ],
    "carpet cleaning": [
        ("Steam Cleaning", "Hot water extraction removes deep-set dirt and allergens from carpets."),
        ("Stain Removal", "Targeted treatment for pet stains, wine, coffee, and tough spots."),
        ("Upholstery Cleaning", "Sofas, chairs, and fabric surfaces cleaned and refreshed."),
    ],
    "moving company": [
        ("Local Moving", "Efficient door-to-door moves handled with care by experienced crews."),
        ("Packing Services", "Professional packing with quality materials to protect every item."),
        ("Storage Solutions", "Secure short-term and long-term storage for your belongings."),
    ],
    "appliance repair": [
        ("Washer and Dryer Repair", "Same-day diagnosis and repair for all major brands."),
        ("Refrigerator Service", "Cooling issues, ice maker repairs, and compressor service."),
        ("Dishwasher Fix", "Leak detection, spray arm replacement, and electrical diagnosis."),
    ],
    "house painting": [
        ("Interior Painting", "Clean, precise interior work with minimal disruption to your home."),
        ("Exterior Painting", "Weather-resistant coating that protects and transforms your curb appeal."),
        ("Cabinet Refinishing", "Restore kitchen and bathroom cabinets without a full replacement."),
    ],
    "handyman": [
        ("General Repairs", "Doors, drywall, faucets, and fixtures repaired the right way."),
        ("Furniture Assembly", "Fast, accurate assembly for flat-pack and custom furniture."),
        ("Fixture Installation", "Light fixtures, ceiling fans, shelving, and hardware installed."),
    ],
    "tree service": [
        ("Tree Removal", "Safe, efficient removal of hazardous or unwanted trees."),
        ("Stump Grinding", "Complete stump elimination down to the root line."),
        ("Storm Emergency Response", "24-hour emergency service for fallen trees and storm damage."),
    ],
    "masonry": [
        ("Concrete Pouring", "Driveways, patios, foundations, and flatwork poured to spec."),
        ("Brick Repair", "Tuckpointing, rebuild, and mortar repair for chimneys and walls."),
        ("Retaining Walls", "Engineered walls that hold grade and enhance your landscape."),
    ],
    "window cleaning": [
        ("Residential Windows", "Interior and exterior window cleaning for homes of all sizes."),
        ("Commercial Buildings", "High-rise and storefront window cleaning with professional equipment."),
        ("Screen Cleaning", "Remove, clean, and reinstall screens for a complete job."),
    ],
    "junk removal": [
        ("Full Property Cleanout", "Estate, garage, basement, and attic cleanouts handled completely."),
        ("Furniture Hauling", "Pick up and responsible disposal of old furniture and appliances."),
        ("Construction Debris", "Job site cleanup and dumpster-free debris removal."),
    ],
    "garage door repair": [
        ("Spring Replacement", "Torsion and extension spring replacement done safely by trained technicians."),
        ("New Installation", "Full garage door and opener installation for all styles."),
        ("Opener Repair", "Belt drive, chain drive, and smart opener diagnosis and repair."),
    ],
    "locksmith": [
        ("Lockout Service", "Fast response to get you back in your home, car, or business."),
        ("Rekeying", "Change your locks without replacing them — fast, affordable security."),
        ("Lock Installation", "Deadbolts, smart locks, and commercial-grade hardware installed."),
    ],
    "mobile mechanic": [
        ("Oil Change", "Full synthetic oil change with filter replacement at your location."),
        ("Brake Service", "Pad and rotor replacement, inspection, and fluid flush on-site."),
        ("On-Site Diagnostics", "OBD scan and full diagnostic report wherever your car is."),
    ],
    "boat detailing": [
        ("Hull Cleaning", "Oxidation removal, compounding, and polishing for fiberglass and gelcoat."),
        ("Interior Detail", "Upholstery, carpet, and surface cleaning throughout the cabin."),
        ("Wax and Polish", "Marine-grade wax protection that lasts through the season."),
    ],
    "fence installation": [
        ("Wood Fence", "Custom wood fence design and installation for privacy and curb appeal."),
        ("Vinyl Fence", "Low-maintenance vinyl fencing in multiple styles and heights."),
        ("Chain Link", "Commercial and residential chain link installation with post setting."),
    ],
    "gutter service": [
        ("Gutter Cleaning", "Full debris removal and flush to protect your foundation and roof."),
        ("Guard Installation", "Leaf guards that eliminate future buildup and reduce maintenance."),
        ("Repair", "Sealing, realignment, and section replacement for leaking gutters."),
    ],
    "drywall repair": [
        ("Patch and Repair", "Seamless patching for holes, cracks, and water-damaged areas."),
        ("Full Install", "New drywall hanging, taping, and finishing for any room."),
        ("Texture Matching", "Match existing wall and ceiling texture with precision."),
    ],
    "flooring installation": [
        ("Tile Installation", "Ceramic, porcelain, and natural stone tile set and grouted to spec."),
        ("LVP Installation", "Luxury vinyl plank installation over any subfloor type."),
        ("Grout Cleaning", "Deep grout cleaning and resealing to restore your tile floor."),
    ],
}

REVIEWS = {
    "hvac": [
        ("Came out same day, fixed our AC in under 2 hours. Honest pricing with zero upselling. Will absolutely call them again.", "Michael T."),
        ("Our furnace died on the coldest night of the year. They were here within an hour and had heat back on by midnight. Incredible.", "Sarah K."),
        ("Finally found an HVAC company that explains what they're doing without making you feel pressured. Fair prices, great work.", "James R."),
    ],
    "plumber": [
        ("Had a burst pipe at 11pm and they were here in 45 minutes. Fixed everything cleanly and the price was more than fair.", "David M."),
        ("Replaced our water heater quickly and efficiently. Cleaned up after themselves and walked us through everything. Highly recommend.", "Linda P."),
        ("Finally an honest plumber. No inflated quotes, no drama. Just solid work at a fair price.", "Tony B."),
    ],
    "electrician": [
        ("Upgraded our entire panel and installed EV chargers in the garage. Clean work, on time, priced right. Couldn't ask for more.", "Greg H."),
        ("Had them rewire a room addition. Professional, thorough, and passed inspection first try. Will definitely use them again.", "Amanda C."),
        ("Fast response for an emergency at my business. They had everything back up and running same day. Real pros.", "Frank D."),
    ],
    "roofer": [
        ("New roof looks fantastic and the crew cleaned up the yard better than they found it. Finished on time and on budget.", "Patricia N."),
        ("They handled everything with our insurance claim. Got a full replacement approved and the work was flawless.", "Robert S."),
        ("Got 4 quotes and they were competitive AND the most professional. No leaks after the big storm.", "Karen W."),
    ],
    "landscaper": [
        ("My yard has never looked better. They transformed a patchy mess into a lawn I'm actually proud of. Worth every penny.", "Nicole F."),
        ("Reliable, professional, and they actually care about the quality of their work. My neighbors have already asked for their number.", "Brian L."),
        ("Designed and built our backyard patio and garden beds. The whole project came out better than I imagined.", "Christina M."),
    ],
    "barbershop": [
        ("Best fade in the city. Been coming here for two years and never once been disappointed. The whole vibe is top notch.", "Marcus J."),
        ("Walked in without an appointment and was treated like a regular. Left looking sharp. This is my spot now.", "Derek A."),
        ("Brought my son for his first real haircut. The barber was patient and made him feel at ease. We'll be back every month.", "Carlos V."),
    ],
    "restaurant": [
        ("Every dish was extraordinary. The service matched the food — attentive without being overbearing. A true dining experience.", "Elizabeth B."),
        ("Took my wife here for our anniversary and it exceeded every expectation. The chef came out to greet the table. Unforgettable.", "William G."),
        ("The best meal I've had in years. Ingredients you can taste the quality in, presentation that felt like art.", "Rachel T."),
    ],
    "salon": [
        ("Best color I've ever had. She listened to exactly what I wanted and delivered beyond what I pictured. I'm obsessed.", "Megan O."),
        ("Finally found my person. Great cut, great conversation, and my hair feels healthier than it has in years.", "Tiffany R."),
        ("Walked in feeling blah and walked out feeling like a completely different person. Worth every dollar.", "Stephanie N."),
    ],
    "florist": [
        ("Did the flowers for our wedding and every single arrangement was breathtaking. Multiple guests asked for their card.", "Jennifer L."),
        ("I order from here every week for our office and it always brightens the whole team's mood. Creative and fresh every time.", "Mark D."),
        ("Sent a same-day arrangement for a difficult time in our family. The care and thought in the design meant everything.", "Susan K."),
    ],
    "pest control": [
        ("Had a major ant problem that two other companies couldn't solve. They came in, identified the source, and it's been gone for months.", "Kevin B."),
        ("Very professional and thorough. They explained exactly what they were treating and why. No hard sell, just solid work.", "Maria H."),
        ("Used them for a termite inspection before closing on our house. Fast turnaround, detailed report. Highly recommend.", "Peter J."),
    ],
    "auto detailing": [
        ("My car looks better than when I drove it off the lot. The ceramic coating they applied is unbelievable — water beads right off.", "Jason M."),
        ("Paint correction on my black car. Every swirl and scratch gone. Worth every dollar.", "Danielle F."),
        ("Full interior detail on a car my dog had destroyed. They made it look completely new. Incredible work.", "Chris T."),
    ],
    "pressure washing": [
        ("Our driveway was black with oil and grime. After they were done it looked brand new. Couldn't believe the difference.", "Paul R."),
        ("Soft washed the whole house exterior. No damage to the siding, no streaks. House looks like it was just painted.", "Sandra K."),
        ("Fast, professional, and reasonable price. Did the deck and the driveway same day. Will be calling every spring.", "Greg N."),
    ],
    "pool service": [
        ("They took over from our last service and immediately fixed issues we didn't even know we had. Water is crystal clear now.", "Barbara M."),
        ("Weekly service is consistent and reliable. They show up, get it done, and leave everything better than they found it.", "Andrew P."),
        ("Our pump was failing and they had a replacement installed within 48 hours. Really saved our summer.", "Lori S."),
    ],
    "carpet cleaning": [
        ("Pet stains that had been there for years came out completely. I don't know how they did it but the carpet looks new.", "Michelle T."),
        ("Steam cleaned three bedrooms and the living room. Dried faster than I expected and smells fresh.", "Robert A."),
        ("Did the upholstery on our sectional at the same time as the carpets. Everything looks and smells incredible.", "Lisa G."),
    ],
    "moving company": [
        ("Moved a three-bedroom house in under five hours. Not a single thing was damaged. These guys are pros.", "David K."),
        ("They packed our entire kitchen and it was done better than I could have done it myself. Nothing broke.", "Amy W."),
        ("Second time using them. Same great experience. On time, efficient, careful. Will not use anyone else.", "Mark H."),
    ],
    "appliance repair": [
        ("Fixed our refrigerator same day. Saved us from losing hundreds in food. Honest diagnosis and fair price.", "Carol B."),
        ("Washer was making a terrible noise. They diagnosed it on the spot and had it fixed in an hour. Great service.", "Tom S."),
        ("Dishwasher repair that another company said couldn't be done. They fixed it in 45 minutes. Highly recommend.", "Nancy P."),
    ],
    "house painting": [
        ("Exterior repaint on our colonial. Clean lines, no drips, no mess. Neighbors keep stopping to compliment it.", "James L."),
        ("Cabinet refinishing saved us from a full kitchen remodel. Looks like brand new cabinets at a fraction of the cost.", "Helen M."),
        ("Painted three rooms in a day. The prep work was exceptional and the finish is flawless.", "Richard A."),
    ],
    "handyman": [
        ("Fixed three things in two hours that had been sitting on my list for months. Fair price and no upselling.", "Scott T."),
        ("Assembled furniture, hung shelves, replaced fixtures. All in one visit. This is exactly what I needed.", "Kim R."),
        ("Quick response, showed up on time, and fixed the door that no one else could figure out. Will definitely call again.", "Dan N."),
    ],
    "tree service": [
        ("Removed a massive oak that was threatening our roof. Crew was professional, safe, and cleaned up everything.", "George P."),
        ("Storm took down a big limb and they had it cleared and chipped within hours of calling. Emergency response was excellent.", "Patricia H."),
        ("Stump grinding done same week I called. They went deep and the area was level when they left.", "Frank M."),
    ],
    "masonry": [
        ("Rebuilt our crumbling brick chimney and matched the original mortar perfectly. Couldn't tell it was ever repaired.", "Thomas K."),
        ("Retaining wall project came out better than the design. Solid construction and they cleaned up every day.", "Anne S."),
        ("Concrete patio looks beautiful and is perfectly level. They took the time to do it right.", "Charles B."),
    ],
    "window cleaning": [
        ("Did the whole house inside and out. Windows are crystal clear. Makes such a difference in how the rooms feel.", "Evelyn T."),
        ("Commercial storefront windows. They come monthly and they are always perfect. Reliable and professional.", "Joseph M."),
        ("Removed years of hard water buildup that I thought was permanent. The glass looks brand new.", "Diane R."),
    ],
    "junk removal": [
        ("Full garage cleanout in three hours. They hauled everything, swept the floor, and left nothing behind.", "Victor H."),
        ("Estate cleanout after my mother passed. They were respectful, efficient, and handled everything with care.", "Louise A."),
        ("Got rid of old furniture, appliances, and construction debris in one trip. Pricing was very fair.", "Benjamin K."),
    ],
    "garage door repair": [
        ("Spring snapped at 7am and they were here by 9am. Fixed and working perfectly before I left for work.", "Tony M."),
        ("Installed a new smart opener and two new doors. Installation was flawless and they walked me through everything.", "Wendy S."),
        ("Diagnosed the problem with my opener that the manufacturer couldn't figure out. Fixed on the first visit.", "Harold B."),
    ],
    "locksmith": [
        ("Locked out at midnight and they arrived in 25 minutes. Professional, no damage to the door.", "Cynthia R."),
        ("Rekeyed all the locks when we moved in. Fast, affordable, and I feel much safer now.", "Douglas T."),
        ("Installed a smart lock on our front door. They explained the setup clearly and made sure everything worked before leaving.", "Joyce K."),
    ],
    "mobile mechanic": [
        ("Diagnosed my car in my driveway and fixed the problem on the spot. Saved me a tow and a dealership visit.", "Aaron M."),
        ("Brakes done in my parking lot at work. No need to take time off. Price was better than the shop.", "Carmen P."),
        ("Battery and alternator replaced on site. They had the parts with them and it was done in two hours.", "Steven W."),
    ],
    "boat detailing": [
        ("Hull looked like it had never been polished. After they were done it was gleaming. Best condition the boat has ever been in.", "Warren N."),
        ("Interior detail removed smells I thought were permanent. The upholstery looks like new and the carpets are spotless.", "Tina H."),
        ("Full detail before the season started. Ceramic coating on the hull. Worth every penny for the protection alone.", "Bruce A."),
    ],
    "fence installation": [
        ("Cedar fence installed along our entire property line. Posts are perfectly plumb and the finish is excellent.", "Raymond T."),
        ("Vinyl fence with three gates. Clean installation, strong posts, and they finished in two days.", "Gloria M."),
        ("Replaced chain link with a wood privacy fence. The project came in on time and under budget.", "Stanley B."),
    ],
    "gutter service": [
        ("Cleaned and flushed gutters we hadn't touched in years. They showed us photos of what they found and removed.", "Edna W."),
        ("Installed leaf guards on the whole house. First heavy rain and not a drop of overflow. Excellent work.", "Harold S."),
        ("Repaired two sections that were pulling away from the fascia. Solid repair and cleaned everything up after.", "Betty P."),
    ],
    "drywall repair": [
        ("Patched and textured a hole from a pipe repair. Matched the existing texture so well you cannot tell anything happened.", "Irene T."),
        ("Full drywall install in a basement room. Perfectly smooth, no seams showing, ready to paint.", "Eugene H."),
        ("Fixed water-damaged ceiling in two visits. Dried, patched, textured, and it looks perfect.", "Mildred K."),
    ],
    "flooring installation": [
        ("LVP installed throughout the first floor. Perfectly flat, no gaps, and they moved all the furniture themselves.", "Norma B."),
        ("Tile work in the master bath is beautiful. Grout lines are perfectly even and the patterns were cut exactly as designed.", "Leonard T."),
        ("Grout cleaning and resealing made our ten-year-old tile floor look new again. Remarkable transformation.", "Stella M."),
    ],
}


def get_business_key(business_type: str) -> str:
    """
    Normalize a business_type string to the canonical key used in SERVICES, REVIEWS, etc.

    Parameters:
        business_type (str): Raw business type from the lead record.

    Returns:
        str: Canonical key. Falls back to 'hvac' if unrecognized.
    """
    btype = business_type.lower().strip()
    # Direct match first
    all_keys = list(SERVICES.keys())
    if btype in all_keys:
        return btype
    # Partial match
    for key in all_keys:
        if key in btype or btype in key:
            return key
    return "hvac"


def get_template(business_type):
    """Legacy: return (template_dict, key) for old-style templates."""
    btype = business_type.lower().strip()
    for key in TEMPLATES:
        if key in btype:
            return TEMPLATES[key], key
    return TEMPLATES["hvac"], "hvac"


def scrape_website(url):
    print(f"Visiting: {url}")
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(separator=" ", strip=True)

        phone = "N/A"
        phone_pattern = re.findall(r'\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}', text)
        if phone_pattern:
            phone = phone_pattern[0]

        address = "N/A"
        address_patterns = re.findall(r'\d+\s+[A-Za-z\s]+(?:Ave|St|Rd|Blvd|Dr|Ln|Way|Court|Ct)[.,]?\s*[A-Za-z\s]+,\s*[A-Z]{2}\s*\d{5}', text)
        if address_patterns:
            address = address_patterns[0]

        title = soup.find("title")
        business_name = title.get_text(strip=True) if title else "Business"

        print(f"Found: {business_name} | Phone: {phone}")
        return {"name": business_name, "phone": phone, "address": address}
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None


def _svg_phone() -> str:
    """Inline SVG phone icon."""
    return '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 12 19.79 19.79 0 0 1 1.6 3.4 2 2 0 0 1 3.6 1.18h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L7.91 8.91a16 16 0 0 0 6.18 6.18l.95-.95a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path></svg>'


def _svg_check() -> str:
    """Inline SVG checkmark icon."""
    return '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="20 6 9 17 4 12"></polyline></svg>'


def _svg_star() -> str:
    """Inline SVG five-pointed star path."""
    return '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="#c9a84c" stroke="none" aria-hidden="true"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>'


def _photo_credit(img: dict) -> str:
    """
    Build the required Unsplash attribution HTML for an image.

    Parameters:
        img (dict): Image info dict from fetch_unsplash_images.

    Returns:
        str: Attribution HTML block, or empty string if no attribution data.
    """
    if not img or not img.get("photographer_name"):
        return ""
    name = img["photographer_name"]
    profile = img.get("photographer_url", "https://unsplash.com")
    utm = "?utm_source=forge_web_studio&utm_medium=referral"
    return (
        f'<p class="photo-credit">Photo by '
        f'<a href="{profile}{utm}" target="_blank" rel="noopener">{name}</a>'
        f' on <a href="https://unsplash.com/{utm}" target="_blank" rel="noopener">Unsplash</a></p>'
    )


def _download_triggers_js(images: list) -> str:
    """
    Build JS that triggers Unsplash download events on page load.

    Parameters:
        images (list): List of image info dicts.

    Returns:
        str: JavaScript snippet.
    """
    locations = [img.get("download_location", "") for img in images if img and img.get("download_location")]
    if not locations:
        return ""
    lines = []
    for loc in locations:
        lines.append(
            f'  fetch("{loc}", {{headers:{{"Authorization":"Client-ID {UNSPLASH_KEY}"}}}}).catch(function(){{}});'
        )
    return "window.addEventListener('load', function() {{\n" + "\n".join(lines) + "\n}});"


def build_demo_site(info, lead, t, tkey):
    """
    Build the HTML demo site for a lead.
    HOT leads get Unsplash hero photos. WARM leads use CSS gradients.
    All sites use per-type SVG logos, per-type icons, AI section, trust bar.
    """
    name = (lead.get("business_name") or lead.get("name") or info.get("name", "Business")).strip()
    phone = (lead.get("phone") or info.get("phone", "")).strip()
    city = lead.get("city", "") or lead.get("location", "")
    state = lead.get("state", "")
    location = f"{city}, {state}".strip(", ") if (city or state) else info.get("address", "")

    bkey = get_business_key(tkey)
    tmpl = TEMPLATES.get(bkey, TEMPLATES["hvac"])
    lead_tier = (lead.get("lead_tier") or "WARM").upper()
    is_premium = (lead_tier == "HOT")

    repo_name = re.sub(r'[^a-z0-9-]', '', name.lower().replace(" ", "-").replace("'", "").replace(",", ""))

    # Colors from per-type template
    c_bg     = tmpl["bg"]
    c_text   = tmpl["text"]
    c_accent = tmpl["accent"]
    c_card   = tmpl["accent2"]
    c_muted  = "rgba(255,255,255,0.5)" if c_bg.startswith("#0") or c_bg.startswith("#1") else "rgba(0,0,0,0.45)"
    c_border = "rgba(255,255,255,0.08)" if c_bg.startswith("#0") or c_bg.startswith("#1") else "rgba(0,0,0,0.1)"

    fallback = FALLBACK_GRADIENTS.get(bkey, f"linear-gradient(135deg,{c_bg} 0%,{c_card} 100%)")

    # Fetch images
    unsplash_imgs = fetch_unsplash_images(bkey, 2) if is_premium else [{}, {}]
    hero_img  = unsplash_imgs[0] if unsplash_imgs else {}
    about_img = unsplash_imgs[1] if len(unsplash_imgs) > 1 else {}

    hero_bg_css  = f"background:url('{hero_img['url']}') center/cover no-repeat;" if (is_premium and hero_img.get("url")) else f"background:{fallback};"
    hero_credit  = _photo_credit(hero_img) if (is_premium and hero_img.get("url")) else ""
    download_js  = _download_triggers_js(unsplash_imgs) if is_premium else ""

    about_img_block = ""
    if is_premium and about_img.get("url"):
        about_credit = _photo_credit(about_img)
        about_img_block = f'<div class="about-img" style="background:url(\'{about_img["url"]}\') center/cover no-repeat;">{about_credit}</div>'

    # Logo HTML (SVG icon + name wordmark, no emojis, no letters)
    logo_html = get_logo_html(name, bkey, accent_color=c_accent, bg_color=c_bg, text_color=c_text, icon_size=18)

    # Per-type service icons
    svc_icons = get_service_icons(bkey)
    service_list = SERVICES.get(bkey, SERVICES.get("hvac", []))[:6]
    cards_html = ""
    for i, (sname, sdesc) in enumerate(service_list):
        icon = svc_icons[i % len(svc_icons)]
        cards_html += (
            f'<div class="service-card">'
            f'<div class="service-icon">{icon}</div>'
            f'<h3 class="service-name">{sname}</h3>'
            f'<p class="service-desc">{sdesc}</p>'
            f'</div>\n'
        )

    # Reviews
    stars_svg = "".join([_svg_star()] * 5)
    review_list = REVIEWS.get(bkey, [
        ("Professional, responsive, and delivered exactly what they promised. Highly recommend.", "Client"),
        ("Called in the morning and they were here by afternoon. Problem solved, fair price.", "Local Resident"),
        ("Best in the area. Quality work and the crew respects your property every time.", "Homeowner"),
    ])
    reviews_html = ""
    for rtext, rauthor in review_list[:3]:
        reviews_html += (
            f'<div class="review-card">'
            f'<div class="review-stars">{stars_svg}</div>'
            f'<p class="review-text">&ldquo;{rtext}&rdquo;</p>'
            f'<div class="review-author">&mdash; {rauthor}</div>'
            f'</div>\n'
        )

    form_options = "".join(f'<option>{sn}</option>' for sn, _ in service_list)

    # Hero copy from template
    hero_h1  = tmpl.get("hero_h1", name)
    hero_sub = tmpl.get("hero_sub", f"Serving {location}. Licensed, insured, and ready to help.")
    hero_tag = tmpl.get("hero_tag", bkey.title())
    cta_text = tmpl.get("cta", "Call Now")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{name} &mdash; {location}</title>
  <meta name="description" content="Professional {bkey} in {location}. {hero_sub}"/>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
  <link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600&display=swap" rel="stylesheet"/>
  <style>
    :root {{
      --bg:      {c_bg};
      --text:    {c_text};
      --accent:  {c_accent};
      --card:    {c_card};
      --muted:   {c_muted};
      --border:  {c_border};
      --max-w:   1160px;
    }}
    *, *::before, *::after {{ margin:0; padding:0; box-sizing:border-box; }}
    html {{ scroll-behavior:smooth; font-size:16px; }}
    body {{ font-family:'DM Sans',system-ui,sans-serif; background:var(--bg); color:var(--text); overflow-x:hidden; -webkit-font-smoothing:antialiased; }}

    /* ── NAV ── */
    nav {{
      position:fixed; top:0; width:100%; z-index:1000;
      padding:20px 5%; display:flex; align-items:center; justify-content:space-between;
      transition:background 0.3s, border-bottom 0.3s;
    }}
    nav.scrolled {{
      background:color-mix(in srgb, var(--bg) 94%, transparent);
      border-bottom:1px solid var(--border);
      backdrop-filter:blur(12px); -webkit-backdrop-filter:blur(12px);
    }}
    .nav-logo {{ display:flex; align-items:center; gap:11px; text-decoration:none; }}
    .logo-mark {{
      width:34px; height:34px; display:flex; align-items:center; justify-content:center;
      flex-shrink:0;
    }}
    .logo-name {{
      font-family:'DM Serif Display',serif; font-size:1rem; font-weight:400;
      letter-spacing:0.015em; white-space:nowrap;
    }}
    .nav-cta {{
      font-size:0.72rem; font-weight:600; letter-spacing:0.1em; text-transform:uppercase;
      color:var(--text); text-decoration:none;
      border:1px solid var(--border); padding:9px 20px;
      display:inline-flex; align-items:center; gap:8px;
      transition:border-color 0.2s, color 0.2s;
    }}
    .nav-cta:hover {{ border-color:var(--accent); color:var(--accent); }}
    @media(max-width:600px) {{ .nav-cta-text {{ display:none; }} }}
    @media(min-width:601px) {{ .nav-cta-icon {{ display:none; }} }}

    /* ── HERO ── */
    .hero {{
      position:relative; height:100svh; min-height:600px;
      display:flex; align-items:flex-end; padding:0 10% 10%;
      overflow:hidden;
    }}
    .hero-bg {{ position:absolute; inset:0; {hero_bg_css} will-change:transform; }}
    .hero-overlay {{
      position:absolute; inset:0;
      background:linear-gradient(to top, rgba(0,0,0,0.82) 0%, rgba(0,0,0,0.38) 60%, rgba(0,0,0,0.1) 100%);
    }}
    .hero-content {{ position:relative; z-index:2; max-width:680px; }}
    .hero-tag {{
      display:inline-flex; align-items:center; gap:8px;
      font-size:0.65rem; letter-spacing:0.2em; text-transform:uppercase;
      color:var(--accent); font-weight:600; margin-bottom:22px;
    }}
    .hero-tag-dot {{ width:6px; height:6px; border-radius:50%; background:var(--accent); flex-shrink:0; }}
    .hero h1 {{
      font-family:'DM Serif Display',serif;
      font-size:clamp(3rem, 6.5vw, 6rem);
      line-height:1.02; color:#fff; font-weight:400;
      margin-bottom:24px;
      opacity:0; animation:fadeUp 0.65s ease 0.15s forwards;
    }}
    .hero-name {{
      font-size:clamp(0.8rem, 1.1vw, 0.95rem);
      color:rgba(255,255,255,0.5); letter-spacing:0.12em;
      text-transform:uppercase; font-weight:500; margin-bottom:10px;
    }}
    .hero-sub {{
      font-size:clamp(0.95rem, 1.2vw, 1.05rem);
      color:rgba(255,255,255,0.62); line-height:1.78;
      max-width:480px; margin-bottom:38px; font-weight:300;
    }}
    .hero-actions {{ display:flex; gap:12px; flex-wrap:wrap; }}
    .btn-primary {{
      background:var(--accent); color:var(--bg);
      padding:14px 34px; text-decoration:none;
      font-size:0.72rem; font-weight:700; letter-spacing:0.1em; text-transform:uppercase;
      display:inline-flex; align-items:center; gap:8px;
      transition:opacity 0.18s;
    }}
    .btn-primary:hover {{ opacity:0.82; }}
    .btn-ghost {{
      background:transparent; color:rgba(255,255,255,0.75);
      padding:13px 34px; text-decoration:none;
      font-size:0.72rem; font-weight:500; letter-spacing:0.1em; text-transform:uppercase;
      border:1px solid rgba(255,255,255,0.22); display:inline-block;
      transition:border-color 0.18s, color 0.18s;
    }}
    .btn-ghost:hover {{ border-color:rgba(255,255,255,0.55); color:#fff; }}
    .hero-credit {{ position:absolute; bottom:14px; right:18px; z-index:2; }}
    @media(max-width:768px) {{
      .hero {{ padding:0 6% 8%; }}
      .hero-actions {{ flex-direction:column; align-items:flex-start; }}
    }}

    /* ── TRUST BAR ── */
    .trust-bar {{
      border-top:1px solid var(--border); border-bottom:1px solid var(--border);
      padding:26px 10%;
    }}
    .trust-inner {{
      max-width:var(--max-w); margin:0 auto;
      display:flex; align-items:center; justify-content:space-between;
      gap:24px; flex-wrap:wrap;
    }}
    .trust-item {{
      display:flex; align-items:center; gap:10px;
      font-size:0.78rem; font-weight:500; letter-spacing:0.06em; text-transform:uppercase;
      color:var(--muted);
    }}
    .trust-icon {{ color:var(--accent); flex-shrink:0; }}

    /* ── SECTIONS ── */
    .section {{ padding:96px 10%; }}
    .section-inner {{ max-width:var(--max-w); margin:0 auto; }}
    .eyebrow {{
      font-size:0.63rem; letter-spacing:0.22em; text-transform:uppercase;
      color:var(--accent); font-weight:600; margin-bottom:12px; display:block;
    }}
    .section-title {{
      font-family:'DM Serif Display',serif;
      font-size:clamp(1.9rem, 3.5vw, 2.9rem);
      line-height:1.12; font-weight:400; margin-bottom:14px;
    }}
    .section-sub {{
      font-size:0.93rem; line-height:1.8; color:var(--muted);
      max-width:460px; margin-bottom:48px;
    }}
    @media(max-width:768px) {{ .section {{ padding:60px 6%; }} }}

    /* ── SERVICES ── */
    .services-grid {{
      display:grid; grid-template-columns:repeat(auto-fit, minmax(260px, 1fr));
      gap:1px; border:1px solid var(--border);
    }}
    .service-card {{
      background:rgba(255,255,255,0.025); padding:40px 34px;
      transition:background 0.22s;
      opacity:0; transform:translateY(18px);
    }}
    .service-card.visible {{
      opacity:1; transform:translateY(0);
      transition:opacity 0.45s ease, transform 0.45s ease, background 0.22s;
    }}
    .service-card:hover {{ background:rgba(255,255,255,0.05); }}
    .service-icon {{
      width:40px; height:40px; color:var(--accent);
      margin-bottom:18px; display:flex; align-items:center;
    }}
    .service-icon svg {{ width:26px; height:26px; }}
    .service-name {{
      font-family:'DM Serif Display',serif;
      font-size:1.15rem; font-weight:400; margin-bottom:10px;
    }}
    .service-desc {{ font-size:0.85rem; line-height:1.74; color:var(--muted); }}

    /* ── AI SECTION ── */
    .ai-section {{
      padding:96px 10%;
      background:var(--card);
      border-top:1px solid var(--border);
      border-bottom:1px solid var(--border);
    }}
    .ai-grid {{
      max-width:var(--max-w); margin:0 auto;
      display:grid; grid-template-columns:1fr 1fr; gap:72px; align-items:center;
    }}
    .ai-feature-list {{ display:flex; flex-direction:column; gap:24px; margin-top:36px; }}
    .ai-feature {{
      display:flex; align-items:flex-start; gap:16px;
      padding:22px 24px; border:1px solid var(--border);
      background:rgba(0,0,0,0.15);
    }}
    .ai-feature-icon {{
      width:36px; height:36px; background:var(--accent);
      color:var(--bg); display:flex; align-items:center; justify-content:center;
      flex-shrink:0; margin-top:2px;
    }}
    .ai-feature-icon svg {{ width:16px; height:16px; }}
    .ai-feature-title {{
      font-family:'DM Serif Display',serif; font-size:1.05rem;
      font-weight:400; margin-bottom:5px;
    }}
    .ai-feature-desc {{ font-size:0.82rem; line-height:1.7; color:var(--muted); }}
    .ai-chat-demo {{
      border:1px solid var(--border); background:rgba(0,0,0,0.25);
      padding:28px; display:flex; flex-direction:column; gap:14px;
    }}
    .ai-chat-header {{
      display:flex; align-items:center; gap:10px;
      padding-bottom:16px; border-bottom:1px solid var(--border);
    }}
    .ai-chat-dot {{
      width:8px; height:8px; border-radius:50%; background:var(--accent);
      animation:pulse 2s ease infinite;
    }}
    .ai-chat-label {{
      font-size:0.72rem; font-weight:600; letter-spacing:0.1em;
      text-transform:uppercase; color:var(--muted);
    }}
    .chat-msg {{ display:flex; flex-direction:column; gap:4px; max-width:82%; }}
    .chat-msg.incoming {{ align-self:flex-start; }}
    .chat-msg.outgoing {{ align-self:flex-end; }}
    .chat-bubble {{
      padding:11px 15px; font-size:0.84rem; line-height:1.55;
      border-radius:2px;
    }}
    .chat-msg.incoming .chat-bubble {{
      background:rgba(255,255,255,0.07); color:var(--text);
    }}
    .chat-msg.outgoing .chat-bubble {{
      background:var(--accent); color:var(--bg);
    }}
    .chat-time {{ font-size:0.63rem; color:var(--muted); }}
    .chat-msg.outgoing .chat-time {{ align-self:flex-end; }}
    .ai-chat-typing {{
      display:flex; align-items:center; gap:5px;
      padding:10px 0; color:var(--muted); font-size:0.78rem;
    }}
    .typing-dots {{ display:flex; gap:4px; }}
    .typing-dot {{
      width:5px; height:5px; border-radius:50%; background:var(--accent);
      animation:bounce 1.2s ease infinite;
    }}
    .typing-dot:nth-child(2) {{ animation-delay:0.2s; }}
    .typing-dot:nth-child(3) {{ animation-delay:0.4s; }}
    @media(max-width:900px) {{
      .ai-grid {{ grid-template-columns:1fr; gap:40px; }}
    }}

    /* ── TESTIMONIALS ── */
    .testimonials-section {{
      background:rgba(255,255,255,0.02);
      border-top:1px solid var(--border); border-bottom:1px solid var(--border);
      padding:96px 10%;
    }}
    .reviews-grid {{
      display:grid; grid-template-columns:repeat(auto-fit, minmax(260px, 1fr));
      gap:1px; border:1px solid var(--border); margin-top:44px;
    }}
    .review-card {{
      padding:34px; border:none; background:rgba(255,255,255,0.02);
      opacity:0; transform:translateY(16px);
    }}
    .review-card.visible {{
      opacity:1; transform:translateY(0);
      transition:opacity 0.45s ease, transform 0.45s ease;
    }}
    .review-stars {{ display:flex; gap:3px; margin-bottom:14px; }}
    .review-text {{
      font-size:0.9rem; line-height:1.8;
      color:rgba(255,255,255,0.7); margin-bottom:16px; font-style:italic;
    }}
    .review-author {{
      font-size:0.68rem; font-weight:600; letter-spacing:0.12em;
      text-transform:uppercase; color:var(--muted);
    }}
    @media(max-width:768px) {{
      .testimonials-section {{ padding:60px 6%; }}
      .reviews-grid {{ grid-template-columns:1fr; }}
    }}

    /* ── ABOUT ── */
    .about-grid {{
      display:grid; grid-template-columns:1fr 1fr; gap:64px;
      align-items:center; max-width:var(--max-w); margin:0 auto;
    }}
    .about-img {{ min-height:360px; position:relative; }}
    .about-badges {{ display:flex; gap:10px; flex-wrap:wrap; margin-top:30px; }}
    .badge {{
      font-size:0.65rem; font-weight:600; letter-spacing:0.12em; text-transform:uppercase;
      color:var(--accent); border:1px solid var(--accent);
      padding:6px 14px; display:inline-block;
    }}
    @media(max-width:900px) {{
      .about-grid {{ grid-template-columns:1fr; gap:36px; }}
      .about-img {{ min-height:220px; order:-1; }}
    }}

    /* ── CONTACT ── */
    .contact-grid {{
      display:grid; grid-template-columns:1fr 1fr; gap:72px;
      align-items:start; max-width:var(--max-w); margin:0 auto;
    }}
    .contact-phone {{
      font-family:'DM Serif Display',serif;
      font-size:clamp(1.6rem, 3vw, 2.4rem);
      color:var(--text); text-decoration:none; display:block;
      margin:18px 0 24px; transition:color 0.2s;
    }}
    .contact-phone:hover {{ color:var(--accent); }}
    .contact-info {{ font-size:0.9rem; color:var(--muted); margin-bottom:6px; }}
    .contact-form {{ display:flex; flex-direction:column; gap:13px; }}
    .form-row {{ display:grid; grid-template-columns:1fr 1fr; gap:13px; }}
    .form-field {{ display:flex; flex-direction:column; gap:5px; }}
    .form-label {{
      font-size:0.62rem; letter-spacing:0.16em; text-transform:uppercase;
      font-weight:600; color:var(--muted);
    }}
    .form-field input,
    .form-field textarea,
    .form-field select {{
      background:rgba(255,255,255,0.04); border:1px solid var(--border);
      color:var(--text); padding:12px 15px;
      font-family:'DM Sans',sans-serif; font-size:0.88rem;
      outline:none; width:100%; transition:border-color 0.2s;
      -webkit-appearance:none;
    }}
    .form-field input:focus,
    .form-field textarea:focus,
    .form-field select:focus {{ border-color:var(--accent); }}
    .form-field textarea {{ resize:vertical; min-height:100px; }}
    .form-submit {{
      background:var(--accent); color:var(--bg);
      padding:14px 34px; border:none; cursor:pointer;
      font-family:'DM Sans',sans-serif; font-size:0.72rem;
      font-weight:700; letter-spacing:0.1em; text-transform:uppercase;
      align-self:flex-start; transition:opacity 0.18s;
    }}
    .form-submit:hover {{ opacity:0.82; }}
    @media(max-width:900px) {{
      .contact-grid {{ grid-template-columns:1fr; gap:44px; }}
      .form-row {{ grid-template-columns:1fr; }}
    }}

    /* ── FOOTER ── */
    footer {{
      border-top:1px solid var(--border); padding:42px 10%;
    }}
    .footer-inner {{
      max-width:var(--max-w); margin:0 auto;
      display:flex; justify-content:space-between; align-items:center;
      flex-wrap:wrap; gap:16px;
    }}
    .footer-logo {{ display:flex; align-items:center; gap:10px; text-decoration:none; }}
    .footer-meta {{
      font-size:0.75rem; color:var(--muted);
      margin-top:6px; line-height:1.6;
    }}
    .footer-right {{ font-size:0.72rem; color:var(--muted); text-align:right; }}
    .footer-credit {{ color:var(--muted); text-decoration:none; transition:color 0.2s; }}
    .footer-credit:hover {{ color:var(--text); }}

    /* ── PHOTO CREDIT ── */
    .photo-credit {{ font-size:0.62rem; color:rgba(255,255,255,0.38); padding:5px 10px; }}
    .photo-credit a {{ color:rgba(255,255,255,0.48); text-decoration:none; }}
    .photo-credit a:hover {{ color:var(--accent); }}

    /* ── ANIMATIONS ── */
    @keyframes fadeUp {{ from {{ opacity:0; transform:translateY(20px); }} to {{ opacity:1; transform:translateY(0); }} }}
    @keyframes pulse {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:0.4; }} }}
    @keyframes bounce {{ 0%,100% {{ transform:translateY(0); }} 50% {{ transform:translateY(-4px); }} }}
  </style>
</head>
<body>

<!-- ── NAV ── -->
<nav id="nav">
  <a href="#" class="nav-logo" aria-label="{name}">
    {logo_html}
  </a>
  <a href="tel:{phone}" class="nav-cta" aria-label="Call {name}">
    <span class="nav-cta-text">{phone}</span>
    <span class="nav-cta-icon">{_svg_phone()}</span>
  </a>
</nav>

<!-- ── HERO ── -->
<section class="hero">
  <div class="hero-bg" id="heroBg"></div>
  <div class="hero-overlay"></div>
  <div class="hero-content">
    <p class="hero-name">{name} &nbsp;&mdash;&nbsp; {location}</p>
    <div class="hero-tag"><span class="hero-tag-dot"></span>{hero_tag}</div>
    <h1>{hero_h1}</h1>
    <p class="hero-sub">{hero_sub}</p>
    <div class="hero-actions">
      <a href="tel:{phone}" class="btn-primary">{_svg_phone()} {cta_text}</a>
      <a href="#contact" class="btn-ghost">Get a Free Quote</a>
    </div>
  </div>
  {f'<div class="hero-credit">{hero_credit}</div>' if hero_credit else ''}
</section>

<!-- ── TRUST BAR ── -->
<div class="trust-bar">
  <div class="trust-inner">
    <div class="trust-item">
      <span class="trust-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg></span>
      Licensed &amp; Insured
    </div>
    <div class="trust-item">
      <span class="trust-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg></span>
      24/7 Emergency Service
    </div>
    <div class="trust-item">
      <span class="trust-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg></span>
      Locally Owned
    </div>
    <div class="trust-item">
      <span class="trust-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg></span>
      5-Star Rated
    </div>
    <div class="trust-item">
      <span class="trust-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg></span>
      Free Estimates
    </div>
  </div>
</div>

<!-- ── SERVICES ── -->
<section id="services" class="section">
  <div class="section-inner">
    <span class="eyebrow">What We Do</span>
    <h2 class="section-title">Our Services</h2>
    <p class="section-sub">Every job done right the first time, by licensed professionals who stand behind their work.</p>
    <div class="services-grid">
      {cards_html}
    </div>
  </div>
</section>

<!-- ── AI SECTION ── -->
<section id="ai-booking" class="ai-section">
  <div class="ai-grid">
    <div>
      <span class="eyebrow">Powered by AI</span>
      <h2 class="section-title">Never Miss a Call Again.</h2>
      <p class="section-sub" style="margin-bottom:0;">Our AI booking assistant answers instantly, 24/7 — scheduling jobs, answering questions, and qualifying leads while you work.</p>
      <div class="ai-feature-list">
        <div class="ai-feature">
          <div class="ai-feature-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
          </div>
          <div>
            <div class="ai-feature-title">24/7 Instant Response</div>
            <div class="ai-feature-desc">Every inquiry answered in seconds — even at midnight. No more missed leads from unanswered calls.</div>
          </div>
        </div>
        <div class="ai-feature">
          <div class="ai-feature-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
          </div>
          <div>
            <div class="ai-feature-title">Auto-Schedule Jobs</div>
            <div class="ai-feature-desc">Customers book directly into your calendar. The AI confirms, collects job details, and sends reminders.</div>
          </div>
        </div>
        <div class="ai-feature">
          <div class="ai-feature-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2A19.79 19.79 0 0 1 11.69 19 19.5 19.5 0 0 1 4.69 12 19.79 19.79 0 0 1 2 3.4 2 2 0 0 1 3.6 1.18h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L7.91 8.91a16 16 0 0 0 6.18 6.18l.95-.95a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
          </div>
          <div>
            <div class="ai-feature-title">SMS &amp; Phone Handoff</div>
            <div class="ai-feature-desc">When a job is ready, you get a text with everything — name, address, issue, best callback time.</div>
          </div>
        </div>
      </div>
    </div>
    <div class="ai-chat-demo" aria-label="AI booking assistant demo">
      <div class="ai-chat-header">
        <div class="ai-chat-dot"></div>
        <div class="ai-chat-label">AI Booking Assistant &mdash; Live</div>
      </div>
      <div class="chat-msg incoming">
        <div class="chat-bubble">Hi! I&rsquo;m {name}&rsquo;s booking assistant. How can I help you today?</div>
        <div class="chat-time">just now</div>
      </div>
      <div class="chat-msg outgoing">
        <div class="chat-bubble">My AC stopped working and it&rsquo;s 95 degrees outside</div>
        <div class="chat-time">just now</div>
      </div>
      <div class="chat-msg incoming">
        <div class="chat-bubble">I&rsquo;m sorry to hear that &mdash; we can get someone out to you today. Can I get your address and a good callback number?</div>
        <div class="chat-time">just now</div>
      </div>
      <div class="chat-msg outgoing">
        <div class="chat-bubble">123 Oak St, same number I messaged from</div>
        <div class="chat-time">just now</div>
      </div>
      <div class="ai-chat-typing">
        <div class="typing-dots">
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
        </div>
        &nbsp;Checking availability&hellip;
      </div>
    </div>
  </div>
</section>

<!-- ── TESTIMONIALS ── -->
<section id="reviews" class="testimonials-section">
  <div class="section-inner">
    <span class="eyebrow">What Clients Say</span>
    <h2 class="section-title">Trusted by Homeowners<br/>Across {location.split(",")[0] if "," in location else location}.</h2>
    <div class="reviews-grid">
      {reviews_html}
    </div>
  </div>
</section>

<!-- ── ABOUT ── -->
<section id="about" class="section">
  <div class="about-grid">
    <div>
      <span class="eyebrow">About Us</span>
      <h2 class="section-title">{name}</h2>
      <p style="font-size:0.97rem;line-height:1.84;color:var(--muted);margin-bottom:18px;">
        We are {name}, a trusted {bkey} team serving {location} and the surrounding communities.
        Every job we take on gets the same attention — no shortcuts, no pressure, no surprise charges.
      </p>
      <p style="font-size:0.9rem;line-height:1.84;color:var(--muted);">
        We are licensed, fully insured, and proud to be part of the communities we serve.
        Whether it&rsquo;s a routine service call or an emergency at 2 AM, we show up.
      </p>
      <div class="about-badges">
        <span class="badge">Licensed</span>
        <span class="badge">Insured</span>
        <span class="badge">Background Checked</span>
        <span class="badge">5-Star Rated</span>
      </div>
    </div>
    {about_img_block if about_img_block else f'<div class="about-img" style="background:{fallback};"></div>'}
  </div>
</section>

<!-- ── CONTACT ── -->
<section id="contact" class="section">
  <div class="contact-grid">
    <div>
      <span class="eyebrow">Get In Touch</span>
      <h2 class="section-title">Let&rsquo;s Talk.</h2>
      <p style="font-size:0.92rem;line-height:1.76;color:var(--muted);margin-bottom:4px;">Call or text us directly:</p>
      <a href="tel:{phone}" class="contact-phone">{phone if phone else "Call Us"}</a>
      <p class="contact-info">{name}</p>
      <p class="contact-info">{location}</p>
      <p style="font-size:0.8rem;color:var(--muted);margin-top:20px;">Or use the form and we&rsquo;ll get back to you within the hour.</p>
    </div>
    <form class="contact-form" onsubmit="return false;">
      <div class="form-row">
        <div class="form-field">
          <label class="form-label">Name</label>
          <input type="text" placeholder="Your name"/>
        </div>
        <div class="form-field">
          <label class="form-label">Phone</label>
          <input type="tel" placeholder="(555) 000-0000"/>
        </div>
      </div>
      <div class="form-field">
        <label class="form-label">Email</label>
        <input type="email" placeholder="you@email.com"/>
      </div>
      <div class="form-field">
        <label class="form-label">Service Needed</label>
        <select>
          <option value="">Select a service</option>
          {form_options}
        </select>
      </div>
      <div class="form-field">
        <label class="form-label">Tell Us About Your Project</label>
        <textarea placeholder="What&rsquo;s the issue or what do you need done?"></textarea>
      </div>
      <button type="submit" class="form-submit">Send Message</button>
    </form>
  </div>
</section>

<!-- ── FOOTER ── -->
<footer>
  <div class="footer-inner">
    <div>
      <a href="#" class="footer-logo" aria-label="{name}">
        {logo_html}
      </a>
      <div class="footer-meta">
        {phone}&nbsp;&nbsp;&bull;&nbsp;&nbsp;{location}<br/>
        Licensed &amp; Insured &nbsp;&bull;&nbsp; Serving {location.split(",")[0] if "," in location else location} and surrounding areas
      </div>
    </div>
    <div class="footer-right">
      <div id="footer-copy"></div>
      <a href="#" class="footer-credit">Built by Forge</a>
    </div>
  </div>
</footer>

<script>
  var nav = document.getElementById('nav');
  window.addEventListener('scroll', function() {{
    nav.classList.toggle('scrolled', window.scrollY > 50);
    var bg = document.getElementById('heroBg');
    if (bg) bg.style.transform = 'translateY(' + (window.scrollY * 0.3) + 'px)';
  }}, {{ passive: true }});

  document.getElementById('footer-copy').textContent =
    '\u00a9 ' + new Date().getFullYear() + ' ' + '{name}. All rights reserved.';

  var io = new IntersectionObserver(function(entries) {{
    entries.forEach(function(e, i) {{
      if (e.isIntersecting) {{
        setTimeout(function() {{ e.target.classList.add('visible'); }}, i * 70);
        io.unobserve(e.target);
      }}
    }});
  }}, {{ threshold: 0.08 }});
  document.querySelectorAll('.service-card, .review-card').forEach(function(el) {{ io.observe(el); }});

  {download_js}
</script>
</body>
</html>"""

    # Save to /tmp/ for GitHub push
    folder = f"/tmp/{repo_name}"
    if os.path.exists(folder):
        shutil.rmtree(folder)
    os.makedirs(folder)
    with open(f"{folder}/index.html", "w") as f:
        f.write(html)

    # Save to /sites/ for local review
    city_slug = re.sub(r'[^a-z0-9]', '', city.lower()) if city else ""
    sites_filename = f"{city_slug}_{repo_name}.html" if city_slug else f"{repo_name}.html"
    sites_path = os.path.join(SITES_DIR, sites_filename)
    with open(sites_path, "w") as f:
        f.write(html)

    print(f"Site built: {folder}/index.html | Local: {sites_path}")
    log("build_demo_site", "SUCCESS", f"{name} → {sites_path}")
    return folder, repo_name


def push_to_github(folder: str, repo_name: str):
    """
    Create a GitHub repository, push the site, and enable GitHub Pages.

    Parameters:
        folder (str): Local folder path containing index.html.
        repo_name (str): Repository slug.

    Returns:
        str or None: Live GitHub Pages URL on success, None on failure.
    """
    print(f"Pushing {repo_name} to GitHub...")
    try:
        requests.post(
            "https://api.github.com/user/repos",
            headers={"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"},
            json={"name": repo_name, "public": True, "auto_init": False},
            timeout=10,
        )
        subprocess.run(["git", "init"], cwd=folder, check=True, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=folder, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", f"Demo site for {repo_name}"], cwd=folder, check=True, capture_output=True)
        subprocess.run(["git", "branch", "-M", "main"], cwd=folder, check=True, capture_output=True)
        remote = f"https://{GITHUB_TOKEN}@github.com/{GITHUB_USERNAME}/{repo_name}.git"
        subprocess.run(["git", "remote", "add", "origin", remote], cwd=folder, check=True, capture_output=True)
        result = subprocess.run(["git", "push", "-u", "origin", "main", "--force"], cwd=folder, capture_output=True, text=True)
        if result.returncode == 0:
            requests.post(
                f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/pages",
                headers={"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"},
                json={"source": {"branch": "main", "path": "/"}},
                timeout=10,
            )
            demo_url = f"https://{GITHUB_USERNAME}.github.io/{repo_name}"
            print(f"Live at: {demo_url}")
            return demo_url
        else:
            log("push_to_github", "ERROR", f"{repo_name} push failed: {result.stderr[:120]}")
            return None
    except Exception as e:
        log("push_to_github", "ERROR", str(e))
        return None


def _parse_location(location: str) -> tuple:
    """Split 'Denver, CO' into (city, state)."""
    parts = [p.strip() for p in (location or "").split(",", 1)]
    city = parts[0] if parts else ""
    state = parts[1] if len(parts) > 1 else ""
    return city, state


def _infer_business_type(name: str) -> str:
    try:
        from scraper import get_business_type
        return get_business_type(name, "")
    except Exception:
        return "hvac"


def _read_built_html(city: str, repo_name: str) -> str:
    city_slug = re.sub(r"[^a-z0-9]", "", city.lower()) if city else ""
    sites_filename = f"{city_slug}_{repo_name}.html" if city_slug else f"{repo_name}.html"
    sites_path = os.path.join(SITES_DIR, sites_filename)
    if os.path.exists(sites_path):
        with open(sites_path, encoding="utf-8") as f:
            return f.read()
    return ""


def build_site_for_api(
    name: str,
    location: str,
    *,
    website: str = "",
    business_type: str = "",
    deploy: bool = False,
    lead_tier: str = "WARM",
) -> dict:
    """
    Build a demo site for the TradeBuilt / FORGE API (Phase 4 canonical generator).

    Parameters:
        name: Business name.
        location: City and optional state, e.g. 'Denver, CO'.
        website: Optional existing website URL to scrape.
        business_type: Trade type override (hvac, plumber, etc.).
        deploy: When True, push to GitHub Pages via process_lead.
        lead_tier: HOT or WARM — affects Unsplash hero usage.

    Returns:
        dict with html, demo_url, business_name, city, state, business_type, lead_tier, phone.
    """
    city, state = _parse_location(location)
    btype = (business_type or _infer_business_type(name)).strip() or "hvac"
    lead = {
        "business_name": name.strip(),
        "city": city,
        "state": state,
        "website_url": (website or "").strip(),
        "business_type": btype,
        "lead_tier": (lead_tier or "WARM").upper(),
    }

    if deploy:
        demo_url = process_lead(lead)
        repo_name = re.sub(
            r"[^a-z0-9-]", "", name.lower().replace(" ", "-").replace("'", "").replace(",", "")
        )
        html = _read_built_html(city, repo_name)
        return {
            "html": html,
            "demo_url": demo_url,
            "business_name": name.strip(),
            "city": city,
            "state": state,
            "business_type": btype,
            "lead_tier": lead.get("lead_tier", "WARM"),
            "phone": lead.get("phone", ""),
        }

    website_url = lead.get("website_url", "")
    if website_url:
        info = scrape_website(website_url)
    else:
        info = None

    if not info:
        info = {
            "name": name.strip(),
            "phone": "",
            "address": f"{city}, {state}".strip(", "),
        }

    t, tkey = get_template(btype)
    folder, repo_name = build_demo_site(info, lead, t, tkey)
    with open(os.path.join(folder, "index.html"), encoding="utf-8") as f:
        html = f.read()

    return {
        "html": html,
        "demo_url": None,
        "business_name": name.strip(),
        "city": city,
        "state": state,
        "business_type": tkey,
        "lead_tier": lead.get("lead_tier", "WARM"),
        "phone": (info.get("phone") or "").strip(),
    }


def process_lead(lead: dict):
    """
    Full pipeline for one lead: scrape site info, build demo, push to GitHub.

    Parameters:
        lead (dict): Lead record from leads.csv.

    Returns:
        str or None: Live demo URL, or None if GitHub push failed.
    """
    website = (lead.get("website_url") or lead.get("website", "")).strip()
    name = (lead.get("business_name") or lead.get("name", "")).strip()

    print(f"\n{'='*50}")
    print(f"Processing: {name}")

    if website:
        info = scrape_website(website)
    else:
        info = None

    if not info:
        info = {
            "name": name,
            "phone": lead.get("phone", ""),
            "address": lead.get("city", "") or lead.get("location", ""),
        }

    btype = lead.get("business_type", "hvac")
    t, tkey = get_template(btype)
    print(f"Type: {tkey} | Tier: {lead.get('lead_tier', 'WARM')}")

    folder, repo_name = build_demo_site(info, lead, t, tkey)
    demo_url = push_to_github(folder, repo_name)

    if demo_url:
        print(f"Done: {demo_url}")
        log("process_lead", "SUCCESS", f"{name} -> {demo_url}")
    else:
        log("process_lead", "ERROR", f"{name} — GitHub push failed")

    return demo_url


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, "leads.csv")

    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        leads = list(reader)

    for lead in leads:
        process_lead(lead)


if __name__ == "__main__":
    if "--single" in sys.argv:
        idx = sys.argv.index("--single")
        lead_path = sys.argv[idx + 1]
        with open(lead_path, "r") as f:
            lead = json.load(f)
        process_lead(lead)
    else:
        main()