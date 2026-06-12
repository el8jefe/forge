"""Unified lead persistence — CSV or Postgres."""

import csv
import os
import shutil
from typing import List

from scraper import CALL_LIST_CSV, CSV_COLUMNS, LEADS_CSV, SCRIPT_DIR
from storage import use_postgres
from system_logger import log

_SCRIPT_DIR = SCRIPT_DIR


def _csv_save(email_leads: List[dict], call_leads: List[dict]) -> None:
    if email_leads:
        file_exists = os.path.exists(LEADS_CSV)
        if file_exists:
            with open(LEADS_CSV) as f:
                header = f.readline()
            if "business_name" not in header:
                shutil.move(LEADS_CSV, os.path.join(_SCRIPT_DIR, "leads_backup.csv"))
                file_exists = False

        with open(LEADS_CSV, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            if not file_exists:
                writer.writeheader()
            writer.writerows(email_leads)
        print(f"\n{len(email_leads)} email leads saved to leads.csv")

    if call_leads:
        file_exists = os.path.exists(CALL_LIST_CSV)
        if file_exists:
            with open(CALL_LIST_CSV) as f:
                header = f.readline()
            if "business_name" not in header:
                shutil.move(CALL_LIST_CSV, os.path.join(_SCRIPT_DIR, "call_list_backup.csv"))
                file_exists = False

        with open(CALL_LIST_CSV, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            if not file_exists:
                writer.writeheader()
            writer.writerows(call_leads)
        print(f"{len(call_leads)} call leads saved to call_list.csv")


def save_leads(email_leads: List[dict], call_leads: List[dict]) -> None:
    if use_postgres():
        from repositories import leads_repo
        count = leads_repo.upsert_csv_rows(email_leads, call_leads)
        log("save_leads", "SUCCESS", f"{count} leads written to postgres")
        return
    _csv_save(email_leads, call_leads)
    log("save_leads", "SUCCESS", f"{len(email_leads)} email + {len(call_leads)} call leads written to csv")


def load_all_leads() -> List[dict]:
    if use_postgres():
        from repositories import leads_repo
        return leads_repo.list_email_leads()
    if not os.path.exists(LEADS_CSV):
        return []
    with open(LEADS_CSV, "r") as f:
        return list(csv.DictReader(f))


def update_lead(business_name: str, updates: dict) -> None:
    if use_postgres():
        from repositories import leads_repo
        leads_repo.update_by_business_name(business_name, updates)
        return
    if not os.path.exists(LEADS_CSV):
        return
    rows = []
    fieldnames = None
    with open(LEADS_CSV, "r") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            n = (row.get("business_name") or row.get("name", "")).strip()
            if n.lower() == business_name.lower():
                row.update(updates)
            rows.append(row)
    if fieldnames:
        with open(LEADS_CSV, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)