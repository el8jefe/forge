"""Outreach event logging — CSV log.csv or Postgres outreach_log."""

import csv
import datetime
import os

from storage import use_postgres

LOG_CSV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "log.csv")


def load_already_contacted() -> set:
    """Return business names that were successfully emailed."""
    if use_postgres():
        from repositories import outreach_repo
        return outreach_repo.contacted_business_names()

    contacted = set()
    if not os.path.exists(LOG_CSV):
        return contacted
    with open(LOG_CSV, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sent_flag = (row.get("email_sent") or "").strip().lower()
            if sent_flag != "true":
                continue
            n = (row.get("business_name") or row.get("name", "")).strip().lower()
            if n:
                contacted.add(n)
    return contacted


def sync_demos_from_log() -> None:
    """Back-fill demo_site_path from failed send log entries."""
    if use_postgres():
        from repositories import outreach_repo
        from system_logger import log
        updated = outreach_repo.sync_demos_from_failed_sends()
        if updated:
            log("sync_demos", "INFO", f"Back-filled {updated} demo URLs from outreach_log")
        return

    from scraper import LEADS_CSV
    from system_logger import log

    if not os.path.exists(LOG_CSV):
        return
    demo_from_log = {}
    with open(LOG_CSV, "r") as f:
        for row in csv.DictReader(f):
            name = (row.get("business_name") or row.get("name", "")).strip()
            url = (row.get("demo_url") or "").strip()
            if name and url:
                demo_from_log[name.lower()] = url

    if not demo_from_log or not os.path.exists(LEADS_CSV):
        return
    rows, fieldnames, updated = [], None, 0
    with open(LEADS_CSV, "r") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            name = (row.get("business_name") or "").strip()
            if not (row.get("demo_site_path") or "").strip() and name.lower() in demo_from_log:
                row["demo_site_path"] = demo_from_log[name.lower()]
                updated += 1
            rows.append(row)
    if updated and fieldnames:
        with open(LEADS_CSV, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        log("sync_demos", "INFO", f"Back-filled {updated} demo URLs from log.csv into leads.csv")


def log_sent(lead: dict, demo_url: str) -> None:
    business_name = (lead.get("business_name") or lead.get("name", "")).strip()
    email = lead.get("email", "")

    if use_postgres():
        from repositories import outreach_repo
        lead_id = lead.get("id") or outreach_repo.find_lead_id_by_name(business_name)
        outreach_repo.log_send(
            lead_id=lead_id,
            to_email=email,
            to_name=business_name,
            demo_url=demo_url,
            outreach_type="initial",
            success=True,
        )
        return

    file_exists = os.path.exists(LOG_CSV)
    with open(LOG_CSV, "a", newline="") as f:
        fieldnames = ["date", "business_name", "email", "demo_url", "email_sent"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "business_name": business_name,
            "email": email,
            "demo_url": demo_url,
            "email_sent": "True",
        })