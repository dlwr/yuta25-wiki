import unittest

from scripts.wrap_link import wrap


class WrapTest(unittest.TestCase):
    def test_wraps_plain_occurrence(self):
        self.assertEqual(wrap("昨日は甲府に行った", "甲府"), "昨日は[甲府]に行った")

    def test_wraps_every_plain_occurrence(self):
        self.assertEqual(wrap("甲府と甲府", "甲府"), "[甲府]と[甲府]")

    def test_returns_none_when_absent(self):
        self.assertIsNone(wrap("昨日は東京に行った", "甲府"))

    def test_returns_none_when_already_bracketed(self):
        self.assertIsNone(wrap("昨日は[甲府]に行った", "甲府"))

    def test_skips_occurrence_inside_external_link(self):
        self.assertIsNone(wrap("[https://example.com 甲府の情報]", "甲府"))

    def test_wraps_outside_but_not_inside_brackets(self):
        self.assertEqual(
            wrap("[甲府の試合] 甲府は勝った", "甲府"),
            "[甲府の試合] [甲府]は勝った",
        )

    def test_skips_occurrence_inside_inline_code(self):
        self.assertIsNone(wrap("`甲府` はコード", "甲府"))

    def test_preserves_leading_indent(self):
        self.assertEqual(wrap("\t甲府へ", "甲府"), "\t[甲府]へ")


if __name__ == "__main__":
    unittest.main()
