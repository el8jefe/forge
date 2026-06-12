#!/usr/bin/env python3
"""
One-time import of leads.csv + call_list.csv into Supabase Postgres.

Prerequisites:
  - Run supabase/migrations/003_phase2_pipeline.sql in the Supabase SQL editor
  - Set SUPABASE_URL, SUPABASE_SERVICE_KEY, STORAGE_BACKEND=postgres in engine/.env

Usage:
  cd forge/engine
  python scripts/import_csv.py          # import
  python scripts/import_csv.py --dry-run
"""

import argparse
import csv
import os
import sys

_ENGINE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ENGINE_DIR)

from scraper import CALL_LIST_CSV, LEADS_CSV
from repositories import leads_repo
from repositories.postgres_client import is_configured


def _load_csv(path: str) -> list:
    if not os.path.exists(path):
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    parser = argparse.ArgumentParser(description="Import FORGE CSV leads into Postgres")
    parser.add_argument("--dry-run", action="store_true", help="Count rows only, no writes")
    args = parser.parse_args()

    if not is_configured():
        print("ERROR: Set SUPABASE_URL and SUPABASE_SERVICE_KEY in engine/.env")
        return 1

    email_leads = _load_csv(LEADS_CSV)
    call_leads = _load_csv(CALL_LIST_CSV)
    print(f"leads.csv:      {len(email_leads)} rows")
    print(f"call_list.csv:  {len(call_leads)} rows")

    if args.dry_run:
        print("Dry run — no database writes.")
        return 0

    if not email_leads and not call_leads:
        print("Nothing to import.")
        return 0

    count = leads_repo.upsert_csv_rows(email_leads, call_leads)
    print(f"Imported {count} leads (upsert on dedup_key).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())