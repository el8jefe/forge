"""Unit tests for repositories.lead_mapper."""

import unittest

from repositories.lead_mapper import (
    csv_row_to_db,
    db_row_to_csv,
    make_dedup_key,
    updates_csv_to_db,
)


class TestLeadMapper(unittest.TestCase):
    def test_make_dedup_key_normalizes_case(self):
        row = {"business_name": "Acme HVAC", "city": "Hartford", "state": "CT"}
        self.assertEqual(make_dedup_key(row), "acme hvac|hartford|ct")

    def test_make_dedup_key_falls_back_to_name(self):
        row = {"name": "Bob's Plumbing", "city": "Boston", "state": "MA"}
        self.assertEqual(make_dedup_key(row), "bob's plumbing|boston|ma")

    def test_csv_row_to_db_maps_pipeline_fields(self):
        row = {
            "business_name": "Acme HVAC",
            "city": "Hartford",
            "state": "CT",
            "score": "9",
            "lead_tier": "HOT",
            "demo_site_path": "https://example.com/demo",
            "email_sent": "true",
        }
        db = csv_row_to_db(row)
        self.assertEqual(db["dedup_key"], "acme hvac|hartford|ct")
        self.assertEqual(db["forge_score"], 9)
        self.assertEqual(db["demo_url"], "https://example.com/demo")
        self.assertTrue(db["email_sent"])
        self.assertEqual(db["status"], "emailed")
        self.assertEqual(db["source"], "forge_scraper")

    def test_csv_row_to_db_call_only_flag(self):
        row = {"business_name": "Call Only Co", "city": "NY", "state": "NY"}
        db = csv_row_to_db(row, is_call_only=True)
        self.assertTrue(db["is_call_only"])

    def test_db_row_to_csv_round_trip_core_fields(self):
        db = {
            "id": "uuid-1",
            "business_name": "Acme HVAC",
            "forge_score": 9,
            "lead_tier": "HOT",
            "demo_url": "https://example.com/demo",
            "email_sent": True,
            "email_sent_date": "2026-06-01T12:00:00Z",
            "approved": True,
            "approved_flag": "true",
        }
        csv = db_row_to_csv(db)
        self.assertEqual(csv["id"], "uuid-1")
        self.assertEqual(csv["score"], "9")
        self.assertEqual(csv["demo_site_path"], "https://example.com/demo")
        self.assertEqual(csv["email_sent"], "true")
        self.assertEqual(csv["email_sent_date"], "2026-06-01")

    def test_updates_csv_to_db_maps_agent_fields(self):
        updates = {
            "demo_site_path": "https://demo.example",
            "email_sent": "true",
            "email_sent_date": "2026-06-11",
            "approved": "false",
        }
        db = updates_csv_to_db(updates)
        self.assertEqual(db["demo_url"], "https://demo.example")
        self.assertTrue(db["email_sent"])
        self.assertEqual(db["status"], "emailed")
        self.assertEqual(db["approved_flag"], "false")
        self.assertFalse(db["approved"])
        self.assertIn("updated_at", db)


if __name__ == "__main__":
    unittest.main()