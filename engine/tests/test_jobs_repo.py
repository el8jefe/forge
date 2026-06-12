"""Unit tests for repositories.jobs_repo (in-memory fallback)."""

import unittest

from repositories import jobs_repo


class TestJobsRepoMemory(unittest.TestCase):
    def setUp(self):
        jobs_repo.use_memory_backend(True)

    def tearDown(self):
        jobs_repo.use_memory_backend(False)

    def test_create_and_complete_job(self):
        job_id = jobs_repo.create("scrape", {"max_leads": 10})
        self.assertTrue(job_id)

        jobs_repo.mark_running(job_id)
        jobs_repo.mark_complete(job_id, {"leads_found": 5})

        job = jobs_repo.get(job_id)
        self.assertIsNotNone(job)
        self.assertEqual(job["type"], "scrape")
        self.assertEqual(job["status"], "complete")
        self.assertEqual(job["leads_found"], 5)
        self.assertEqual(job["params"]["max_leads"], 10)

    def test_mark_failed(self):
        job_id = jobs_repo.create("agent", {})
        jobs_repo.mark_running(job_id)
        jobs_repo.mark_failed(job_id, "boom")

        job = jobs_repo.get(job_id)
        self.assertEqual(job["status"], "failed")
        self.assertEqual(job["error"], "boom")

    def test_list_jobs(self):
        jobs_repo.create("scrape", {})
        jobs_repo.create("followup", {})
        jobs = jobs_repo.list_jobs()
        self.assertEqual(len(jobs), 2)


if __name__ == "__main__":
    unittest.main()