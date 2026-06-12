"""Unit tests for Stripe webhook handler."""

import unittest

from integrations.stripe_conversions import PLAN_DEFINITIONS, process_stripe_webhook


class TestStripeWebhook(unittest.TestCase):
    def test_invalid_signature_returns_400(self):
        code, body = process_stripe_webhook(b"{}", "invalid")
        self.assertEqual(code, 400)
        self.assertEqual(body, "Invalid signature")

    def test_plan_definitions_complete(self):
        self.assertIn("starter", PLAN_DEFINITIONS)
        self.assertIn("growth", PLAN_DEFINITIONS)
        self.assertIn("autopilot", PLAN_DEFINITIONS)


if __name__ == "__main__":
    unittest.main()