import unittest

from scripts.movie_page import (
    build_body,
    convert_inline,
    infobox_image,
    infobox_rows,
    lead_paragraphs,
    parse_infobox,
    pick_article,
    pick_poster,
    section_bullets,
    section_table_cast,
    wikipedia_url,
)


class ConvertInlineTest(unittest.TestCase):
    def test_plain_link(self):
        self.assertEqual(convert_inline("[[サンダンス映画祭]]で"), "[サンダンス映画祭]で")

    def test_piped_link_keeps_display(self):
        self.assertEqual(convert_inline("[[アメリカ合衆国の映画|アメリカ合衆国]]の"), "[アメリカ合衆国]の")

    def test_year_link_brackets_only_digits(self):
        self.assertEqual(convert_inline("[[2015年の映画|2015年]]の"), "[2015]年の")
        self.assertEqual(convert_inline("[[1974年]]の"), "[1974]年の")

    def test_keep_links_false_strips_brackets(self):
        self.assertEqual(convert_inline("[[英語]]・[[アルメニア語]]", keep_links=False), "英語・アルメニア語")
        self.assertEqual(convert_inline("[[2015年]][[7月10日]]", keep_links=False), "2015年7月10日")

    def test_file_and_category_links_removed(self):
        self.assertEqual(convert_inline("[[ファイル:a.jpg|thumb|説明]]本文[[Category:2015年の映画]]"), "本文")

    def test_refs_removed(self):
        self.assertEqual(convert_inline("使用された<ref>{{Cite web|url=x}}</ref>。"), "使用された。")
        self.assertEqual(convert_inline("受賞<ref name=\"a\" />した"), "受賞した")

    def test_comment_removed(self):
        self.assertEqual(convert_inline("a<!-- メモ -->b"), "ab")

    def test_bold_and_italic_stripped(self):
        self.assertEqual(convert_inline("『'''タンジェリン'''』は''良い''"), "『タンジェリン』は良い")

    def test_original_title_italic_becomes_link(self):
        self.assertEqual(convert_inline("（原題：''Tangerine''）"), "（原題：[Tangerine]）")
        self.assertEqual(convert_inline("（原題:''After Yang''）"), "（原題:[After Yang]）")

    def test_interlanguage_stub_link(self):
        self.assertEqual(
            convert_inline("{{仮リンク|マイヤ・テイラー|en|Mya Taylor}}が"),
            "[マイヤ・テイラー]（英語版）が",
        )

    def test_flagicon(self):
        self.assertEqual(convert_inline("{{flagicon|USA}} [[マグノリア・ピクチャーズ]]"), "アメリカ合衆国の旗 [マグノリア・ピクチャーズ]")
        self.assertEqual(convert_inline("{{flagicon|JPN}} ミッドシップ"), "日本の旗 ミッドシップ")

    def test_flagicon_with_english_country_name(self):
        self.assertEqual(convert_inline("{{Flagicon|China}} 中国電影集団公司"), "中華人民共和国の旗 中国電影集団公司")
        self.assertEqual(convert_inline("{{Flagicon|Japan}} 東宝東和"), "日本の旗 東宝東和")

    def test_country_template(self):
        self.assertEqual(convert_inline("{{USA}}"), "アメリカ合衆国の旗 アメリカ合衆国")
        self.assertEqual(convert_inline("{{FRA}}"), "フランスの旗 フランス")
        self.assertEqual(convert_inline("{{PRC}}"), "中華人民共和国の旗 中華人民共和国")

    def test_lang_template(self):
        self.assertEqual(convert_inline("{{lang|en|Tangerine}}"), "Tangerine")
        self.assertEqual(convert_inline("{{lang-en|Tangerine}}"), "Tangerine")

    def test_unknown_template_removed(self):
        self.assertEqual(convert_inline("受賞{{要出典|date=2020年}}した"), "受賞した")

    def test_html_tags_stripped_and_entities(self):
        self.assertEqual(convert_inline("<small>88分</small>&nbsp;x"), "88分 x")


INFOBOX = """{{Infobox Film
| 作品名 = タンジェリン
| 原題 = Tangerine
| 画像 = 
| 監督 = [[ショーン・ベイカー]]
| 製作総指揮 = [[マーク・デュプラス]]<br />[[ジェイ・デュプラス]]
| 製作 = 
| 脚本 = ショーン・ベイカー<br />[[クリス・バーゴッチ]]
| 配給 = {{flagicon|USA}} [[マグノリア・ピクチャーズ]]<br />{{flagicon|JPN}} ミッドシップ
| 公開 = {{flagicon|USA}} [[2015年]][[7月10日]]<br />{{flagicon|JPN}} [[2017年]][[1月28日]]
| 上映時間 = 88分
| 製作国 = {{USA}}
| 言語 = [[英語]]・[[アルメニア語]]
| 制作費 = $100,000
| 次作 = 
}}
"""

WIKITEXT = (
    "{{Otheruses|映画|果物|タンジェリン}}\n"
    + INFOBOX
    + "\n『'''タンジェリン'''』（原題：''Tangerine''）は、[[2015年の映画|2015年]]の[[コメディドラマ映画]]。\n"
    "\n2015年の[[サンダンス映画祭]]で公開された<ref>{{Cite web|url=x}}</ref>。\n"
    "\n== ストーリー ==\n長い話。\n"
    "\n== キャスト ==\n* シンディ・レラ：{{仮リンク|キタナ・キキ・ロドリゲス|en|Kitana Kiki Rodriguez}}\n"
    "* ラズミック：[[カレン・カラグリアン]]\n"
    "\n== 受賞 ==\n* 観客賞\n"
)


CAST_TABLE = (
    "== キャスト ==\n"
    "{| class=\"wikitable\" style=\"text-align: center;\"\n"
    "|-\n"
    "! rowspan=2|役名\n"
    "! rowspan=2|俳優\n"
    "! colspan=2|日本語吹替\n"
    "|-\n"
    "! ソフト版\n"
    "! [[フジテレビジョン|フジテレビ]]版\n"
    "|-\n"
    "| アーマンド・ゴールドマン || [[ロビン・ウィリアムズ]] || [[安原義人]] || [[羽佐間道夫]]\n"
    "|-\n"
    "| ケヴィン・キーリー上院議員 || [[ジーン・ハックマン]] || [[石森達幸]] || [[石田太郎]]\n"
    "|-\n"
    "| 本人役 || [[ジェイ・レノ]]<br />（クレジットなし） ||  || \n"
    "|-\n"
    "| その他 ||  || [[小室正幸]]<br>[[沢木郁也]] || [[秋元羊介]]\n"
    "|-\n"
    "|\n"
    "|-\n"
    "| 演出 ||  || 戸田清二郎 || 春日正伸\n"
    "|}\n"
    "\n== スタッフ ==\n* 監督：X\n"
)


class ParseInfoboxTest(unittest.TestCase):
    def test_returns_ordered_params_with_raw_values(self):
        params = parse_infobox(INFOBOX)
        self.assertEqual(params[0], ("作品名", "タンジェリン"))
        self.assertEqual(params[3], ("監督", "[[ショーン・ベイカー]]"))
        self.assertEqual(
            dict(params)["配給"],
            "{{flagicon|USA}} [[マグノリア・ピクチャーズ]]<br />{{flagicon|JPN}} ミッドシップ",
        )

    def test_empty_values_kept_as_empty(self):
        self.assertEqual(dict(parse_infobox(INFOBOX))["製作"], "")

    def test_returns_empty_list_without_infobox(self):
        self.assertEqual(parse_infobox("本文だけ"), [])


class InfoboxRowsTest(unittest.TestCase):
    def setUp(self):
        self.rows = infobox_rows(parse_infobox(INFOBOX))

    def test_skips_empty_and_image_and_sequel_params(self):
        labels = [r[0] for r in self.rows]
        self.assertNotIn("画像", labels)
        self.assertNotIn("製作", labels)
        self.assertNotIn("次作", labels)
        self.assertNotIn("作品名", labels)

    def test_br_splits_into_multiple_values(self):
        self.assertIn(("製作総指揮", ["[マーク・デュプラス]", "[ジェイ・デュプラス]"]), self.rows)

    def test_release_dates_are_plain(self):
        self.assertIn(("公開", ["アメリカ合衆国の旗 2015年7月10日", "日本の旗 2017年1月28日"]), self.rows)

    def test_language_and_country_are_plain(self):
        self.assertIn(("言語", ["英語・アルメニア語"]), self.rows)
        self.assertIn(("製作国", ["アメリカ合衆国の旗 アメリカ合衆国"]), self.rows)

    def test_distributor_keeps_link_with_flag(self):
        self.assertIn(("配給", ["アメリカ合衆国の旗 [マグノリア・ピクチャーズ]", "日本の旗 ミッドシップ"]), self.rows)

    def test_budget_label_is_normalized(self):
        self.assertIn(("製作費", ["$100,000"]), self.rows)

    def test_keeps_wikipedia_order(self):
        labels = [r[0] for r in self.rows]
        self.assertEqual(labels, ["監督", "製作総指揮", "脚本", "配給", "公開", "上映時間", "製作国", "言語", "製作費"])


class LeadAndSectionTest(unittest.TestCase):
    def test_lead_paragraphs_are_converted_and_exclude_templates(self):
        self.assertEqual(
            lead_paragraphs(WIKITEXT),
            [
                "『タンジェリン』（原題：[Tangerine]）は、[2015]年の[コメディドラマ映画]。",
                "2015年の[サンダンス映画祭]で公開された。",
            ],
        )

    def test_section_bullets(self):
        self.assertEqual(
            section_bullets(WIKITEXT, "キャスト"),
            ["シンディ・レラ：[キタナ・キキ・ロドリゲス]（英語版）", "ラズミック：[カレン・カラグリアン]"],
        )

    def test_section_bullets_missing_section(self):
        self.assertEqual(section_bullets(WIKITEXT, "スタッフ"), [])

    def test_section_table_cast_reads_role_and_actor(self):
        self.assertEqual(
            section_table_cast(CAST_TABLE, "キャスト"),
            [
                "アーマンド・ゴールドマン - [ロビン・ウィリアムズ]",
                "ケヴィン・キーリー上院議員 - [ジーン・ハックマン]",
                "本人役 - [ジェイ・レノ] （クレジットなし）",
            ],
        )

    def test_section_table_cast_empty_without_table(self):
        self.assertEqual(section_table_cast(WIKITEXT, "キャスト"), [])

    def test_section_table_cast_missing_section(self):
        self.assertEqual(section_table_cast(CAST_TABLE, "スタッフ"), [])


class BuildBodyTest(unittest.TestCase):
    def test_cast_from_table_when_no_bullets(self):
        body = build_body("バードケージ", INFOBOX + "\n\n本文。\n\n" + CAST_TABLE)
        self.assertIn("> アーマンド・ゴールドマン - [ロビン・ウィリアムズ]\n> ケヴィン・キーリー上院議員 - [ジーン・ハックマン]\n", body)

    def test_full_body(self):
        body = build_body("タンジェリン (映画)", WIKITEXT, poster="https://scrapbox.io/files/x.jpg")
        self.assertEqual(
            body,
            "タンジェリン\n"
            "[https://scrapbox.io/files/x.jpg]\n"
            "\n"
            "\n"
            "> 『タンジェリン』（原題：[Tangerine]）は、[2015]年の[コメディドラマ映画]。\n"
            "> 2015年の[サンダンス映画祭]で公開された。\n"
            "\n"
            "> シンディ・レラ：[キタナ・キキ・ロドリゲス]（英語版）\n"
            "> ラズミック：[カレン・カラグリアン]\n"
            "\n"
            "table:info\n"
            "\tタンジェリン\n"
            "\tTangerine\n"
            "\t監督\t[ショーン・ベイカー]\n"
            "\t製作総指揮\t[マーク・デュプラス]\n"
            "\t\t[ジェイ・デュプラス]\n"
            "\t脚本\tショーン・ベイカー\n"
            "\t\t[クリス・バーゴッチ]\n"
            "\t配給\tアメリカ合衆国の旗 [マグノリア・ピクチャーズ]\n"
            "\t\t日本の旗 ミッドシップ\n"
            "\t公開\tアメリカ合衆国の旗 2015年7月10日\n"
            "\t\t日本の旗 2017年1月28日\n"
            "\t上映時間\t88分\n"
            "\t製作国\tアメリカ合衆国の旗 アメリカ合衆国\n"
            "\t言語\t英語・アルメニア語\n"
            "\t製作費\t$100,000\n"
            "[https://ja.wikipedia.org/wiki/%E3%82%BF%E3%83%B3%E3%82%B8%E3%82%A7%E3%83%AA%E3%83%B3_(%E6%98%A0%E7%94%BB) タンジェリン (映画) - Wikipedia]\n",
        )

    def test_without_poster_and_with_impression(self):
        body = build_body("タンジェリン (映画)", WIKITEXT, impression="良かった")
        self.assertTrue(body.startswith("タンジェリン\n\n良かった\n\n> 『タンジェリン』"))

    def test_title_falls_back_to_article_title_without_disambiguation(self):
        body = build_body("二百三高地", "{{Infobox Film\n| 監督 = [[舛田利雄]]\n}}\n本文。\n")
        self.assertTrue(body.startswith("二百三高地\n\n\n> 本文。\n\ntable:info\n\t監督\t[舛田利雄]\n"))


class HelpersTest(unittest.TestCase):
    def test_wikipedia_url_keeps_parentheses_readable(self):
        self.assertEqual(
            wikipedia_url("タンジェリン (映画)"),
            "https://ja.wikipedia.org/wiki/%E3%82%BF%E3%83%B3%E3%82%B8%E3%82%A7%E3%83%AA%E3%83%B3_(%E6%98%A0%E7%94%BB)",
        )

    def test_pick_poster_prefers_file_named_poster(self):
        self.assertEqual(
            pick_poster(["File:OOjs UI icon edit-ltr-progressive.svg", "File:Tangerine (film) POSTER.jpg"]),
            "File:Tangerine (film) POSTER.jpg",
        )

    def test_pick_poster_falls_back_to_first_raster_image(self):
        self.assertEqual(pick_poster(["File:Icon.svg", "File:Still.png"]), "File:Still.png")

    def test_pick_article_prefers_film_title(self):
        hits = [{"title": "Xin Zhan: Red Cliff"}, {"title": "John Woo"}, {"title": "Red Cliff (film)"}]
        self.assertEqual(pick_article(hits), "Red Cliff (film)")

    def test_pick_article_accepts_year_film_suffix(self):
        self.assertEqual(pick_article([{"title": "Mya Taylor"}, {"title": "Tangerine (2015 film)"}]), "Tangerine (2015 film)")

    def test_pick_article_falls_back_to_first_hit(self):
        self.assertEqual(pick_article([{"title": "Inception"}, {"title": "Christopher Nolan"}]), "Inception")

    def test_pick_article_none_without_hits(self):
        self.assertIsNone(pick_article([]))

    def test_pick_poster_none_when_only_svg(self):
        self.assertIsNone(pick_poster(["File:Icon.svg"]))

    def test_infobox_image_reads_image_param(self):
        text = "{{Infobox film\n| name = The Birdcage\n| image = Birdcage_imp.jpg\n| director = [[Mike Nichols]]\n}}"
        self.assertEqual(infobox_image(text), "File:Birdcage imp.jpg")

    def test_infobox_image_strips_file_link(self):
        text = "{{Infobox film\n| image = [[File:Tangerine poster.jpg|220px|alt=Poster]]\n}}"
        self.assertEqual(infobox_image(text), "File:Tangerine poster.jpg")

    def test_infobox_image_none_when_empty(self):
        self.assertIsNone(infobox_image("{{Infobox film\n| image = \n| director = X\n}}"))

    def test_infobox_image_none_without_infobox(self):
        self.assertIsNone(infobox_image("plain text"))


if __name__ == "__main__":
    unittest.main()


class OriginalAndYearTest(unittest.TestCase):
    def test_from_infobox(self):
        from scripts.movie_page import original_and_year

        self.assertEqual(original_and_year(INFOBOX), ("Tangerine", "2015"))

    def test_missing_original_title(self):
        from scripts.movie_page import original_and_year

        self.assertEqual(original_and_year("{{Infobox Film\n| 公開 = 1980年8月2日\n}}"), (None, "1980"))

    def test_falls_back_to_english_title_and_release_date_param(self):
        from scripts.movie_page import original_and_year

        wikitext = "{{Infobox Film\n| 英語題 = Red Cliff Part I\n| 公開日 = {{Flagicon|China}} [[2008年]][[7月10日]]\n}}"
        self.assertEqual(original_and_year(wikitext), ("Red Cliff Part I", "2008"))

    def test_missing_infobox(self):
        from scripts.movie_page import original_and_year

        self.assertEqual(original_and_year("本文"), (None, None))
