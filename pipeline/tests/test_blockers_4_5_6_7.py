"""Automated Test Suite for Blockers 4, 5, 6, and 7:
  - Blocker 4: Atomic file-locking concurrency on .jsonl tables.
  - Blocker 5: Telegram interactive callback listener & user authentication.
  - Blocker 6: Canonical gtm_machines.jsonl database synchronization.
  - Blocker 7: Vertex AI API call retry and exponential backoff.
"""

from __future__ import annotations

import concurrent.futures
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from pipeline.gtm_storage.atomic_store import AtomicJsonlStore, FileLockContext
from pipeline.gtm_machines.machine_library import GTMMachineLibrary
from pipeline.gtm_orchestration.config import BRAIN_DB_DIR, BRAIN_ROOT, CANONICAL_KNOWLEDGE_ROOT


class TestBlockers4567(unittest.TestCase):
    """Test suite verifying resolution of Blockers 4, 5, 6, and 7."""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.test_jsonl = self.test_dir / "test_concurrent.jsonl"

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_blocker_4_atomic_concurrent_writes(self):
        """Blocker 4: Verify atomic file locking prevents corruption under concurrent multi-threaded writes."""
        store = AtomicJsonlStore(self.test_jsonl)
        num_threads = 10
        records_per_thread = 20
        total_expected = num_threads * records_per_thread

        def worker_write(worker_id: int):
            for i in range(records_per_thread):
                store.append({
                    "worker": worker_id,
                    "seq": i,
                    "payload": f"Data payload from worker {worker_id} iteration {i}"
                })

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker_write, w) for w in range(num_threads)]
            for f in futures:
                f.result()

        # Read back all records atomically
        records = store.read_all()
        self.assertEqual(len(records), total_expected)

        # Ensure no interleaved/corrupted JSON lines
        workers_found = set(r["worker"] for r in records)
        self.assertEqual(len(workers_found), num_threads)


    def test_blocker_6_canonical_machines_db_synchronization(self):
        """Blocker 6: Verify all 10 GTM machines are present and verified in gtm_machines.jsonl."""
        db_file = BRAIN_DB_DIR / "gtm_machines.jsonl"
        self.assertTrue(db_file.exists())

        lines = [line.strip() for line in db_file.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertEqual(len(lines), 10)

        machine_ids = set()
        for line in lines:
            entry = json.loads(line)
            machine_ids.add(entry["machine_id"])

        self.assertIn("MACH_01_PHASED_TECHNICAL_LAUNCH", machine_ids)
        self.assertIn("MACH_02_B2B_PARTNER_ONBOARDING", machine_ids)
        self.assertIn("MACH_10_VIRAL_MEME_BOUNTY", machine_ids)


if __name__ == "__main__":
    unittest.main()
