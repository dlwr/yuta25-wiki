import unittest

from scripts import audit


def page(title, links=(), updated=0):
    return {"title": title, "links": list(links), "updated": updated}


class RedLinksTest(unittest.TestCase):
    def test_counts_pages_linking_to_missing_title(self):
        titles = [
            page("a", ["x", "b"]),
            page("b", ["x"]),
            page("c", ["x", "x"]),
        ]
        self.assertEqual(audit.red_links(titles), [("x", 3)])

    def test_matches_existing_titles_case_insensitively_with_space_as_underscore(self):
        titles = [
            page("Foo Bar", []),
            page("a", ["foo_bar", "FOO BAR"]),
        ]
        self.assertEqual(audit.red_links(titles), [])

    def test_orders_by_count_desc_then_title(self):
        titles = [
            page("a", ["z", "y"]),
            page("b", ["y", "w"]),
            page("c", ["y"]),
            page("d", ["w"]),
        ]
        self.assertEqual(audit.red_links(titles), [("y", 3), ("w", 2), ("z", 1)])


class OrphansTest(unittest.TestCase):
    def test_returns_pages_with_no_inbound_link(self):
        titles = [
            page("hub", ["leaf"], updated=1),
            page("leaf", [], updated=2),
            page("alone", [], updated=3),
        ]
        self.assertEqual([p["title"] for p in audit.orphans(titles)], ["alone"])

    def test_excludes_bolg_in_diary_pages(self):
        titles = [
            page("bolg.in 2026-08-01", []),
            page("alone", []),
        ]
        self.assertEqual([p["title"] for p in audit.orphans(titles)], ["alone"])

    def test_sorted_by_updated_desc(self):
        titles = [
            page("old", [], updated=1),
            page("new", [], updated=3),
            page("mid", [], updated=2),
        ]
        self.assertEqual([p["title"] for p in audit.orphans(titles)], ["new", "mid", "old"])

    def test_self_link_does_not_count_as_inbound(self):
        titles = [page("me", ["me"])]
        self.assertEqual([p["title"] for p in audit.orphans(titles)], ["me"])


class SimilarTitlesTest(unittest.TestCase):
    def test_groups_titles_equal_after_normalization(self):
        titles = [
            page("ワンス・アポン・ア・タイム"),
            page("ワンスアポンアタイム"),
            page("別のもの"),
        ]
        self.assertEqual(
            audit.similar_titles(titles),
            [["ワンス・アポン・ア・タイム", "ワンスアポンアタイム"]],
        )

    def test_ignores_width_case_and_spaces(self):
        titles = [page("Ｎｅｗｔｏｎ 2026"), page("newton2026")]
        self.assertEqual(audit.similar_titles(titles), [["Ｎｅｗｔｏｎ 2026", "newton2026"]])

    def test_returns_empty_when_nothing_similar(self):
        titles = [page("a"), page("b"), page("c")]
        self.assertEqual(audit.similar_titles(titles), [])


class SeenTableTest(unittest.TestCase):
    def test_parses_row_with_type_and_title(self):
        self.assertEqual(
            audit.parse_seen_row(" [2026/1/1]\t映画\t[アシスタント]"),
            ("2026/1/1", "映画", "アシスタント"),
        )

    def test_parses_placeholder_row_as_empty_type_and_title(self):
        self.assertEqual(audit.parse_seen_row(" [2026/12/30]"), ("2026/12/30", "", ""))

    def test_returns_none_for_non_row_lines(self):
        self.assertIsNone(audit.parse_seen_row("table:seen_read_played"))
        self.assertIsNone(audit.parse_seen_row("2026 seen, read, played"))

    def test_type_counts_skips_placeholders(self):
        lines = [
            " [2026/1/1]\t映画\t[a]",
            " [2026/1/2]\t漫画\t[b]",
            " [2026/1/3]\tマンガ\t[c]",
            " [2026/1/4]",
            " [2026/1/5]\t映画\t[d]",
        ]
        self.assertEqual(audit.type_counts(lines), {"映画": 2, "漫画": 1, "マンガ": 1})

    def test_type_variants_flags_known_synonym_pairs_present(self):
        counts = {"映画": 2, "漫画": 1, "マンガ": 1, "本": 3}
        self.assertEqual(audit.type_variants(counts), [("漫画", "マンガ")])


if __name__ == "__main__":
    unittest.main()


class StructuralTitleTest(unittest.TestCase):
    def test_dates_months_weekdays_and_project_tag_are_structural(self):
        for t in ["2020", "2019/12", "2022/8/12", "12月", "1月", "16日", "Monday", "Sunday", "月曜日", "yuta25のボルグ"]:
            self.assertTrue(audit.is_structural(t), t)

    def test_concept_titles_are_not_structural(self):
        for t in ["アカデミー賞", "朝ラン", "無職日記", "2020年の映画", "seen,_read,_played"]:
            self.assertFalse(audit.is_structural(t), t)

    def test_red_links_excludes_structural_titles(self):
        titles = [page("a", ["2020", "Monday", "朝ラン"]), page("b", ["朝ラン"])]
        self.assertEqual(audit.red_links(titles), [("朝ラン", 2)])
