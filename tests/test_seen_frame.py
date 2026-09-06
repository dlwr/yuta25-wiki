import unittest

from scripts.seen_frame import already_recorded, first_frame, ops_for, row

LINES = [
    {"id": "t", "text": "2026 seen, read, played"},
    {"id": "h", "text": "table:seen_read_played"},
    {"id": "a", "text": " [2026/8/30]\tゲーム\t[真・三國無双オリジンズ]"},
    {"id": "f1", "text": " [2026/11/6]"},
    {"id": "f2", "text": " [2026/11/8]"},
]


class FirstFrameTest(unittest.TestCase):
    def test_returns_earliest_date_only_line(self):
        self.assertEqual(first_frame(LINES)["id"], "f1")

    def test_ignores_filled_rows(self):
        self.assertIsNone(first_frame(LINES[:3]))

    def test_ignores_lines_that_are_not_table_rows(self):
        self.assertIsNone(first_frame([{"id": "x", "text": "[2026/11/6]"}]))


class RowTest(unittest.TestCase):
    def test_row_format(self):
        self.assertEqual(row("2026/9/5", "映画", "タンジェリン"), " [2026/9/5]\t映画\t[タンジェリン]")


class AlreadyRecordedTest(unittest.TestCase):
    def test_true_when_title_is_in_table(self):
        self.assertTrue(already_recorded(LINES, "真・三國無双オリジンズ"))

    def test_false_when_absent(self):
        self.assertFalse(already_recorded(LINES, "タンジェリン"))

    def test_false_on_partial_match(self):
        self.assertFalse(already_recorded(LINES, "三國無双"))


class OpsForTest(unittest.TestCase):
    def test_replaces_first_frame(self):
        self.assertEqual(
            ops_for(LINES, "2026/9/5", "映画", "タンジェリン"),
            {"ops": [{"replace": "f1", "text": " [2026/9/5]\t映画\t[タンジェリン]"}]},
        )

    def test_none_without_frame(self):
        self.assertIsNone(ops_for(LINES[:3], "2026/9/5", "映画", "タンジェリン"))


if __name__ == "__main__":
    unittest.main()
