"""Unit tests for mail.sender provider selection."""

import unittest
from unittest.mock import patch

from mail import sender


class TestMailSender(unittest.TestCase):
    def test_no_provider_configured(self):
        with patch("mail.sender.settings") as mock_settings:
            mock_settings.email_provider = "auto"
            mock_settings.resend_api_key = ""
            mock_settings.gmail_app_password = ""
            self.assertEqual(sender.active_provider(), "none")

    def test_resend_preferred(self):
        with patch("mail.sender.settings") as mock_settings:
            mock_settings.email_provider = "auto"
            mock_settings.resend_api_key = "re_test"
            mock_settings.gmail_app_password = "secret"
            self.assertEqual(sender.active_provider(), "resend")

    def test_gmail_fallback(self):
        with patch("mail.sender.settings") as mock_settings:
            mock_settings.email_provider = "auto"
            mock_settings.resend_api_key = ""
            mock_settings.gmail_app_password = "app-pass"
            self.assertEqual(sender.active_provider(), "gmail")


if __name__ == "__main__":
    unittest.main()