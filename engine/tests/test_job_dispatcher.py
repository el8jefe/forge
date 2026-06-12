"""Unit tests for job_dispatcher celery detection."""

import unittest
from unittest.mock import patch

from job_dispatcher import celery_available


class TestJobDispatcher(unittest.TestCase):
    def test_celery_disabled(self):
        with patch("job_dispatcher.settings") as mock_settings:
            mock_settings.use_celery = False
            mock_settings.celery_broker = "redis://localhost:6379/0"
            self.assertFalse(celery_available())

    def test_celery_enabled(self):
        with patch("job_dispatcher.settings") as mock_settings:
            mock_settings.use_celery = True
            mock_settings.celery_broker = "redis://localhost:6379/0"
            self.assertTrue(celery_available())

    def test_celery_enabled_empty_broker(self):
        with patch("job_dispatcher.settings") as mock_settings:
            mock_settings.use_celery = True
            mock_settings.celery_broker = ""
            self.assertFalse(celery_available())


if __name__ == "__main__":
    unittest.main()