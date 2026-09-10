import unittest

from scripts.wiki_draft import classify, external_ids, parse_source, revision, sitelinks, summary_line, translation_notices

ENTITY = {
    "id": "Q485069",
    "labels": {"ja": {"value": "アタック・ザ・ガス・ステーション!"}},
    "sitelinks": {"enwiki": {"title": "Attack the Gas Station"}, "kowiki": {"title": "주유소 습격 사건"}},
    "claims": {
        "P345": [{"mainsnak": {"datavalue": {"value": "tt0262246"}}}],
        "P2465": [{"mainsnak": {"datavalue": {"value": "162814"}}}],
        "P7222": [{"mainsnak": {"datavalue": {"value": "51235"}}}],
        "P3704": [{"mainsnak": {"datavalue": {"value": "K/05013"}}}],
        "P8921": [{"mainsnak": {"datavalue": {"value": "19990067"}}}],
        "P57": [{"mainsnak": {"datavalue": {"value": {"id": "Q914001"}}}}],
    },
}


class ExternalIdsTest(unittest.TestCase):
    def test_maps_known_properties_to_urls(self):
        ids = external_ids(ENTITY)
        self.assertEqual(ids["映画.com"], "https://eiga.com/movie/51235/")
        self.assertEqual(ids["allcinema"], "https://www.allcinema.net/cinema/162814")
        self.assertEqual(ids["KMDb"], "https://www.kmdb.or.kr/db/kor/detail/movie/K/05013")
        self.assertEqual(ids["IMDb"], "https://www.imdb.com/title/tt0262246/")
        self.assertEqual(ids["KOFIC"], "https://www.koreanfilm.or.kr/eng/films/index/filmsView.jsp?movieCd=19990067")

    def test_ignores_item_valued_claims(self):
        self.assertNotIn("P57", external_ids(ENTITY))

    def test_omits_missing_databases(self):
        self.assertNotIn("KINENOTE", external_ids(ENTITY))


class SitelinksTest(unittest.TestCase):
    def test_keys_by_language(self):
        self.assertEqual(sitelinks(ENTITY), {"en": "Attack the Gas Station", "ko": "주유소 습격 사건"})


class ClassifyTest(unittest.TestCase):
    def test_missing(self):
        self.assertEqual(classify({"title": "ユ・オソン", "missing": True}, []), ("missing", "ユ・オソン", ""))

    def test_disambiguation(self):
        page = {"title": "イ・ソンジェ", "pageprops": {"disambiguation": ""}, "extract": "イ・ソンジェは朝鮮語圏内における人名である。"}
        self.assertEqual(classify(page, []), ("disambig", "イ・ソンジェ", "イ・ソンジェは朝鮮語圏内における人名である。"))

    def test_redirect_reports_target(self):
        page = {"title": "金尚珍", "extract": "金 尚珍は元プロ野球選手。"}
        redirects = [{"from": "キム・サンジン", "to": "金尚珍"}]
        self.assertEqual(classify(page, redirects), ("redirect", "金尚珍", "金 尚珍は元プロ野球選手。"))

    def test_exists(self):
        page = {"title": "ユ・ジテ", "extract": "ユ・ジテは、韓国の俳優、映画監督。"}
        self.assertEqual(classify(page, []), ("exists", "ユ・ジテ", "ユ・ジテは、韓国の俳優、映画監督。"))


class RevisionTest(unittest.TestCase):
    def test_extracts_title_revid_timestamp_content(self):
        api = {"query": {"pages": [{"title": "Attack the Gas Station", "revisions": [
            {"revid": 1366614734, "timestamp": "2026-07-29T02:15:25Z", "slots": {"main": {"content": "{{Infobox film}}"}}}]}]}}
        self.assertEqual(revision(api), ("Attack the Gas Station", 1366614734, "2026-07-29T02:15:25Z", "{{Infobox film}}"))

    def test_missing_page_returns_none(self):
        self.assertIsNone(revision({"query": {"pages": [{"title": "X", "missing": True}]}}))


class SummaryLineTest(unittest.TestCase):
    def test_lists_every_source_with_oldid_and_declares_llm(self):
        line = summary_line([("en", "Attack the Gas Station", 1366614734), ("ko", "주유소 습격 사건", 41773823)], "Claude (claude-fable-5-1)")
        self.assertEqual(
            line,
            "[[en:Attack the Gas Station]] oldid=1366614734、[[ko:주유소 습격 사건]] oldid=41773823 を一部翻訳。"
            "Claude (claude-fable-5-1) の補助で下書きを作成し、全文と出典を人手で確認",
        )

    def test_without_sources_only_declares_llm(self):
        self.assertEqual(summary_line([], "Claude (claude-fable-5-1)"), "Claude (claude-fable-5-1) の補助で下書きを作成し、全文と出典を人手で確認")


class ParseSourceTest(unittest.TestCase):
    def test_title_may_contain_colons_and_spaces(self):
        self.assertEqual(parse_source("en:Star Trek: Nemesis:12345"), ("en", "Star Trek: Nemesis", 12345))


class TranslationNoticesTest(unittest.TestCase):
    def test_one_template_per_source(self):
        self.assertEqual(
            translation_notices([("en", "Attack the Gas Station", 1366614734), ("ko", "주유소 습격 사건", 41773823)]),
            ["{{翻訳告知|en|Attack the Gas Station|version=1366614734|insertversion=}}",
             "{{翻訳告知|ko|주유소 습격 사건|version=41773823|insertversion=}}"],
        )


if __name__ == "__main__":
    unittest.main()
