"""
agent.py — FORGE Autonomous Agent
Orchestrates: scrape → score → build sites → send emails
Runs on a 6-hour schedule with self-healing retry logic.
"""

import csv
import os
import json
import subprocess
import datetime
import time
import schedule
from dotenv import load_dotenv

from system_logger import log, check_for_failures
from scraper import run_scraper
from site_builder import process_lead
from emailer import send_batch, get_today_count, get_daily_limit, send_summary_email
from notifications import fire_notification
from storage.leads_storage import save_leads, load_all_leads, update_lead
from storage.outreach_storage import log_sent, load_already_contacted, sync_demos_from_log

load_dotenv()

SCRIPT_DIR    = os.path.dirname(os.path.abspath(__file__))
APPROVAL_MODE = os.getenv("APPROVAL_MODE", "false").lower() == "true"
RETRY_QUEUE_FILE = os.path.join(SCRIPT_DIR, "demo_retry_queue.json")
READY_TO_SEND_REPORT = os.path.join(SCRIPT_DIR, "ready_to_send.csv")
from config import settings as _settings
TEST_MODE = _settings.test_mode
MAX_RETRIES = 3


# ─── UTILITIES ────────────────────────────────────────────────────────────────

def load_retry_queue() -> dict:
    """Load persisted demo build retry queue."""
    if not os.path.exists(RETRY_QUEUE_FILE):
        return {}
    try:
        with open(RETRY_QUEUE_FILE, "r") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_retry_queue(queue: dict):
    """Persist demo build retry queue."""
    with open(RETRY_QUEUE_FILE, "w") as f:
        json.dump(queue, f, indent=2)


def is_suppressed(lead: dict) -> bool:
    """Return True when lead should not receive email outreach."""
    status = (lead.get("reply_status") or "").strip().lower()
    suppressed = {"bounced", "stop", "stopped", "unsubscribe", "unsubscribed", "do_not_contact"}
    return status in suppressed


def write_ready_to_send_report(leads: list, demo_urls: dict):
    """
    Export a QA report with send readiness reasons.
    """
    fieldnames = [
        "business_name", "email", "lead_tier", "owner_name", "owner_confidence",
        "owner_source", "demo_url", "ready", "reason",
    ]
    rows = []
    for lead in leads:
        name = (lead.get("business_name") or "").strip()
        demo_url = (demo_urls.get(name) or "").strip()
        email = (lead.get("email") or "").strip()
        if is_suppressed(lead):
            reason = "suppressed"
            ready = "false"
        elif not email:
            reason = "missing_email"
            ready = "false"
        elif not demo_url:
            reason = "missing_demo_url"
            ready = "false"
        else:
            reason = "ok"
            ready = "true"

        rows.append({
            "business_name": name,
            "email": email,
            "lead_tier": lead.get("lead_tier", ""),
            "owner_name": lead.get("owner_name", ""),
            "owner_confidence": lead.get("owner_confidence", ""),
            "owner_source": lead.get("owner_source", ""),
            "demo_url": demo_url,
            "ready": ready,
            "reason": reason,
        })

    with open(READY_TO_SEND_REPORT, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def print_banner(lead_count: int, emails_today: int):
    """Print the cycle start banner to stdout."""
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("\n" + "=" * 47)
    print("  FORGE AGENT — CYCLE STARTED")
    print(f"  Time: {ts}")
    print(f"  Lead count: {lead_count} | Emails sent today: {emails_today}")
    print("=" * 47 + "\n")


def print_summary(scraped: int, hot: int, warm: int, sites_built: int, emails_sent: int):
    """Print the cycle completion summary to stdout."""
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("\n" + "=" * 47)
    print("  FORGE AGENT — CYCLE COMPLETE")
    print(f"  Time: {ts}")
    print(f"  Scraped: {scraped} | HOT: {hot} | WARM: {warm}")
    print(f"  Sites built: {sites_built} | Emails sent: {emails_sent}")
    print("=" * 47 + "\n")


# ─── PIPELINE STEPS (with retry) ──────────────────────────────────────────────

def step_with_retry(step_name: str, fn, *args, **kwargs):
    """
    Run fn(*args, **kwargs) up to MAX_RETRIES times.
    Returns result on success, None on final failure.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            result = fn(*args, **kwargs)
            log(step_name, "SUCCESS", f"attempt {attempt}")
            return result
        except Exception as e:
            log(step_name, "ERROR", f"attempt {attempt}/{MAX_RETRIES} — {e}")
            print(f"  {step_name} failed (attempt {attempt}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES:
                time.sleep(5)
    log(step_name, "CRITICAL", f"All {MAX_RETRIES} retries failed — skipping")
    fire_notification(f"CRITICAL: {step_name} failed after {MAX_RETRIES} retries", level="critical")
    return None


# ─── MAIN PIPELINE CYCLE ──────────────────────────────────────────────────────

def run_pipeline_cycle():
    cycle_start = datetime.datetime.now()
    log("pipeline_cycle", "INFO", "Starting new cycle")

    all_leads = load_all_leads()
    emails_today = get_today_count()
    print_banner(len(all_leads), emails_today)

    # ── STEP 1: Scrape new leads ──────────────────────────────────────────────
    print("STEP 1: Scraping new leads...")
    result = step_with_retry("scrape_leads", run_scraper)
    if result is None:
        email_leads, call_leads = [], []
    else:
        email_leads, call_leads = result
        if email_leads or call_leads:
            save_leads(email_leads, call_leads)

    scraped_count = len(email_leads) + len(call_leads)

    # ── STEP 2: Score & rank (already done inside run_scraper) ───────────────
    print(f"\nSTEP 2: Scored {scraped_count} new leads")
    hot_new = [l for l in email_leads if l.get("lead_tier") == "HOT"]
    warm_new = [l for l in email_leads if l.get("lead_tier") == "WARM"]
    if hot_new:
        fire_notification(f"{len(hot_new)} new HOT leads found!", level="info")
    log("score_leads", "SUCCESS", f"hot={len(hot_new)} warm={len(warm_new)}")

    # ── STEP 3: Build demo sites ──────────────────────────────────────────────
    print("\nSTEP 3: Building demo sites...")
    sync_demos_from_log()  # rescue demo URLs from previously failed send attempts
    contacted = load_already_contacted()
    all_current = load_all_leads()
    by_name = {(l.get("business_name") or "").strip().lower(): l for l in all_current}
    retry_queue = load_retry_queue()

    # Newly scraped leads that haven't been contacted yet
    to_build = [l for l in hot_new + warm_new if (l.get("business_name") or "").lower() not in contacted]

    # Existing leads in leads.csv that have an email but no demo yet — unblock them every cycle
    existing_need_demo = [
        l for l in all_current
        if (l.get("email") or "").strip()
        and not (l.get("demo_site_path") or "").strip()
        and (l.get("email_sent") or "").strip().lower() != "true"
        and not is_suppressed(l)
        and (l.get("business_name") or "").lower() not in contacted
    ]
    current_build_names = {(l.get("business_name") or "").lower() for l in to_build}
    for l in existing_need_demo:
        if (l.get("business_name") or "").lower() not in current_build_names:
            to_build.append(l)

    # Retry queue (up to 3 attempts for previously failed builds)
    for queued_name, meta in retry_queue.items():
        if int(meta.get("attempts", 0)) >= 3:
            continue
        if queued_name in by_name and queued_name not in {(l.get("business_name") or "").strip().lower() for l in to_build}:
            lead = by_name[queued_name]
            if not is_suppressed(lead) and (lead.get("email_sent") or "").strip().lower() != "true":
                to_build.append(lead)

    demo_urls = {}
    sites_built = 0

    for lead in to_build:
        name = (lead.get("business_name") or "").strip()
        demo_url = step_with_retry(f"build_site_{name[:20]}", process_lead, lead)
        if demo_url:
            demo_urls[name] = demo_url
            update_lead(name, {"demo_site_path": demo_url})
            sites_built += 1
            retry_queue.pop(name.lower(), None)
        else:
            existing_demo = (lead.get("demo_site_path") or "").strip()
            if existing_demo:
                demo_urls[name] = existing_demo
            else:
                log("build_sites", "WARNING", f"{name} — demo build failed, skipping send")
                q = retry_queue.get(name.lower(), {"business_name": name, "attempts": 0})
                q["attempts"] = int(q.get("attempts", 0)) + 1
                q["last_attempt_at"] = datetime.datetime.now().isoformat()
                retry_queue[name.lower()] = q

    save_retry_queue(retry_queue)

    # Pull demo URLs from leads.csv for leads that already had demos before this cycle
    all_current = load_all_leads()
    for lead in all_current:
        name = (lead.get("business_name") or "").strip()
        if name not in demo_urls and (lead.get("demo_site_path") or "").strip():
            demo_urls[name] = lead["demo_site_path"].strip()

    log("build_sites", "SUCCESS", f"Built {sites_built} new sites | {len(demo_urls)} total with demos")

    # ── STEP 4: Send emails — ALL ready leads in leads.csv, HOT first ─────────
    print("\nSTEP 4: Sending emails...")

    # Use the full leads.csv as the send pool, not just leads built this cycle
    # When APPROVAL_MODE=true, only send leads explicitly approved via the dashboard
    ready_to_email = [
        l for l in all_current
        if (l.get("email") or "").strip()
        and demo_urls.get((l.get("business_name") or "").strip())
        and not is_suppressed(l)
        and (l.get("email_sent") or "").strip().lower() != "true"
        and (l.get("business_name") or "").lower() not in contacted
        and (not APPROVAL_MODE or (l.get("approved") or "").strip().lower() == "true")
    ]
    if APPROVAL_MODE:
        approved_count = sum(1 for l in ready_to_email)
        print(f"  Approval mode ON — {approved_count} approved leads in queue")
    write_ready_to_send_report(all_current, demo_urls)

    hot_to_send = [l for l in ready_to_email if l.get("lead_tier") == "HOT"]
    warm_to_send = [l for l in ready_to_email if l.get("lead_tier") == "WARM"]

    sent_count = 0
    for batch, label in [(hot_to_send, "HOT"), (warm_to_send, "WARM")]:
        if not batch:
            continue
        if get_today_count() >= get_daily_limit():
            log("send_emails", "WARNING", "Daily limit reached")
            break
        print(f"  Sending to {len(batch)} {label} leads...")
        s, f, sent_names = send_batch(batch, demo_urls, stagger=True)
        sent_count += s
        sent_name_set = {n.lower() for n in sent_names}
        for lead in batch:
            name = (lead.get("business_name") or "").strip()
            if name.lower() not in sent_name_set:
                continue
            log_sent(lead, demo_urls.get(name, ""))
            update_lead(name, {
                "email_sent": "true",
                "email_sent_date": datetime.datetime.now().strftime("%Y-%m-%d"),
            })

    log("send_emails", "SUCCESS", f"Sent {sent_count} emails this cycle")

    # ── STEP 5: Update leads.csv (already done above) ────────────────────────
    print("\nSTEP 5: leads.csv updated")

    # ── STEP 6: Self-review ───────────────────────────────────────────────────
    print("\nSTEP 6: Self-review...")
    failures = check_for_failures()
    if failures:
        print(f"  {len(failures)} CRITICAL issues found today:")
        for f_line in failures[:5]:
            print(f"    {f_line}")
    else:
        print("  No critical issues found.")

    # ── STEP 7: Summary ───────────────────────────────────────────────────────
    hot_all = sum(1 for l in load_all_leads() if l.get("lead_tier") == "HOT")
    warm_all = sum(1 for l in load_all_leads() if l.get("lead_tier") == "WARM")
    print_summary(scraped_count, hot_all, warm_all, sites_built, sent_count)

    elapsed = (datetime.datetime.now() - cycle_start).seconds
    log("pipeline_cycle", "SUCCESS", f"Cycle done in {elapsed}s | scraped={scraped_count} sites={sites_built} sent={sent_count}")

    # Send summary email to admin
    summary_body = (
        f"FORGE Cycle Complete\n\n"
        f"Time: {cycle_start.strftime('%Y-%m-%d %H:%M')}\n"
        f"New leads scraped: {scraped_count}\n"
        f"HOT leads (total): {hot_all}\n"
        f"WARM leads (total): {warm_all}\n"
        f"Demo sites built: {sites_built}\n"
        f"Emails sent: {sent_count}\n"
        f"Critical issues: {len(failures)}\n"
    )
    send_summary_email(
        subject=f"FORGE Cycle Complete — {scraped_count} leads, {sent_count} emails sent",
        body=summary_body,
    )


# ─── SCHEDULER ────────────────────────────────────────────────────────────────

def start_scheduler():
    """Start the 6-hour scheduler. Runs once immediately, then at 00:00, 06:00, 12:00, 18:00."""
    print("FORGE Scheduler starting — runs at 00:00, 06:00, 12:00, 18:00")
    log("scheduler", "INFO", "Scheduler started")

    # Run once immediately on start
    run_pipeline_cycle()

    # Then schedule every 6 hours
    schedule.every().day.at("00:00").do(run_pipeline_cycle)
    schedule.every().day.at("06:00").do(run_pipeline_cycle)
    schedule.every().day.at("12:00").do(run_pipeline_cycle)
    schedule.every().day.at("18:00").do(run_pipeline_cycle)

    while True:
        schedule.run_pending()
        time.sleep(60)


def main():
    import sys
    if "--once" in sys.argv:
        run_pipeline_cycle()
    elif "--schedule" in sys.argv:
        start_scheduler()
    else:
        # Default: run once (backwards-compatible behavior)
        run_pipeline_cycle()


if __name__ == "__main__":
    main()
