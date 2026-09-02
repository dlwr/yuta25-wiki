import os
import tempfile
import unittest

from scripts import ledger


class LedgerTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.dir.name, "bought.jsonl")

    def tearDown(self):
        self.dir.cleanup()

    def test_load_missing_file_returns_empty(self):
        self.assertEqual(ledger.load(self.path), [])

    def test_append_then_load_roundtrip(self):
        ledger.append(self.path, {"id": "o1", "decision": "added", "title": "x"})
        ledger.append(self.path, {"id": "o2", "decision": "skipped", "title": "y"})
        entries = ledger.load(self.path)
        self.assertEqual([e["id"] for e in entries], ["o1", "o2"])
        self.assertEqual(entries[0]["title"], "x")

    def test_append_stamps_recorded_at(self):
        ledger.append(self.path, {"id": "o1", "decision": "added"})
        self.assertIn("recorded_at", ledger.load(self.path)[0])

    def test_known_ids(self):
        entries = [{"id": "a"}, {"id": "b"}]
        self.assertEqual(ledger.known_ids(entries), {"a", "b"})

    def test_filter_new_drops_known_candidates(self):
        entries = [{"id": "a"}]
        candidates = [{"id": "a", "t": 1}, {"id": "b", "t": 2}]
        self.assertEqual(ledger.filter_new(candidates, entries), [{"id": "b", "t": 2}])


if __name__ == "__main__":
    unittest.main()
