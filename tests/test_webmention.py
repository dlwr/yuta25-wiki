import unittest

from scripts.webmention import (
    ME,
    discover_endpoint,
    extract_links,
    new_links,
    outcome,
    page_url,
    run,
    updated_pages,
)


def line(text, updated=200, user=ME):
    return {"text": text, "updated": updated, "userId": user}


class ExtractLinksTest(unittest.TestCase):
    def test_bracket_url(self):
        self.assertEqual(extract_links("見た [https://example.com/a]"), ["https://example.com/a"])

    def test_bracket_url_then_title(self):
        self.assertEqual(extract_links("[https://example.com/a 記事]"), ["https://example.com/a"])

    def test_bracket_title_then_url(self):
        self.assertEqual(extract_links("[記事 https://example.com/a]"), ["https://example.com/a"])

    def test_bare_url(self):
        self.assertEqual(extract_links("> https://example.com/a 鹿島に"), ["https://example.com/a"])

    def test_strips_trailing_punctuation(self):
        self.assertEqual(extract_links("（https://example.com/a）。"), ["https://example.com/a"])

    def test_keeps_non_ascii_path_as_written(self):
        self.assertEqual(
            extract_links("[https://ja.wikipedia.org/wiki/007/ゴールドフィンガー_(映画) wp]"),
            ["https://ja.wikipedia.org/wiki/007/ゴールドフィンガー_(映画)"],
        )

    def test_strips_trailing_fullwidth_bracket(self):
        self.assertEqual(extract_links("「https://t.co/exNoqWqYfH」"), ["https://t.co/exNoqWqYfH"])

    def test_excludes_own_and_image_hosts(self):
        text = "https://scrapbox.io/yuta25/x https://gyazo.com/abc https://i.gyazo.com/abc.png https://yuta25.on.bolg.in/p/1"
        self.assertEqual(extract_links(text), [])

    def test_excludes_image_extensions(self):
        self.assertEqual(extract_links("[https://example.com/poster.JPG]"), [])

    def test_ignores_backquoted(self):
        self.assertEqual(extract_links("`https://example.com/a` と https://example.com/b"), ["https://example.com/b"])

    def test_dedupes(self):
        self.assertEqual(extract_links("https://example.com/a [https://example.com/a]"), ["https://example.com/a"])


class NewLinksTest(unittest.TestCase):
    def test_takes_lines_updated_after_since(self):
        lines = [line("https://example.com/old", updated=100), line("https://example.com/new", updated=200)]
        self.assertEqual(new_links(lines, since=150), ["https://example.com/new"])

    def test_skips_lines_by_other_users(self):
        lines = [line("https://example.com/spam", user="someone"), line("https://example.com/mine")]
        self.assertEqual(new_links(lines, since=100), ["https://example.com/mine"])

    def test_skips_code_blocks(self):
        lines = [line("code:a.sh"), line(" curl https://example.com/api"), line("https://example.com/after")]
        self.assertEqual(new_links(lines, since=100), ["https://example.com/after"])


class UpdatedPagesTest(unittest.TestCase):
    def fetcher(self, batches):
        calls = []

        def fetch(skip):
            calls.append(skip)
            return batches[len(calls) - 1]

        return fetch, calls

    def test_stops_at_since_and_ignores_pins_for_cutoff(self):
        fetch, calls = self.fetcher([
            [
                {"title": "pinned old", "updated": 10, "pin": 1},
                {"title": "pinned new", "updated": 300, "pin": 1},
                {"title": "a", "updated": 250, "pin": 0},
                {"title": "b", "updated": 150, "pin": 0},
                {"title": "c", "updated": 90, "pin": 0},
            ],
        ])
        self.assertEqual([p["title"] for p in updated_pages(fetch, since=100, limit=5)], ["pinned new", "a", "b"])
        self.assertEqual(calls, [0])

    def test_pages_through(self):
        fetch, calls = self.fetcher([
            [{"title": "a", "updated": 300, "pin": 0}, {"title": "b", "updated": 200, "pin": 0}],
            [{"title": "c", "updated": 150, "pin": 0}, {"title": "d", "updated": 50, "pin": 0}],
        ])
        self.assertEqual([p["title"] for p in updated_pages(fetch, since=100, limit=2)], ["a", "b", "c"])
        self.assertEqual(calls, [0, 2])

    def test_stops_on_empty_batch(self):
        fetch, _ = self.fetcher([[{"title": "a", "updated": 300, "pin": 0}], []])
        self.assertEqual([p["title"] for p in updated_pages(fetch, since=100, limit=1)], ["a"])


class PageUrlTest(unittest.TestCase):
    def test_spaces_become_underscores(self):
        self.assertEqual(page_url("bolg.in 2026-09-23"), "https://scrapbox.io/yuta25/bolg.in_2026-09-23")

    def test_keeps_commas(self):
        self.assertEqual(page_url("2026 seen, read, played"), "https://scrapbox.io/yuta25/2026_seen,_read,_played")

    def test_encodes_non_ascii(self):
        self.assertEqual(page_url("スーパーフライ"), "https://scrapbox.io/yuta25/%E3%82%B9%E3%83%BC%E3%83%91%E3%83%BC%E3%83%95%E3%83%A9%E3%82%A4")

    def test_encodes_slash_and_question(self):
        self.assertEqual(page_url("a/b?"), "https://scrapbox.io/yuta25/a%2Fb%3F")

    def test_encodes_trailing_colon(self):
        self.assertEqual(page_url("a:b:"), "https://scrapbox.io/yuta25/a:b%3A")


class DiscoverEndpointTest(unittest.TestCase):
    def test_link_header_wins(self):
        headers = {"Link": '<https://ex.com/wm-header>; rel="webmention"', "Content-Type": "text/html"}
        body = '<link rel="webmention" href="/wm-html">'
        self.assertEqual(discover_endpoint("https://ex.com/p", headers, body), "https://ex.com/wm-header")

    def test_link_header_with_multiple_rels_and_entries(self):
        headers = {"Link": '<https://ex.com/a>; rel="other", </wm>; rel="me webmention"'}
        self.assertEqual(discover_endpoint("https://ex.com/p", headers, ""), "https://ex.com/wm")

    def test_first_link_or_a_in_document_order(self):
        body = '<a rel="webmention" href="/from-a">x</a><link rel="webmention" href="/from-link">'
        self.assertEqual(discover_endpoint("https://ex.com/p", {"Content-Type": "text/html; charset=utf-8"}, body), "https://ex.com/from-a")

    def test_rel_with_multiple_values_in_html(self):
        body = '<link rel="nofollow webmention" href="https://wm.io/ex">'
        self.assertEqual(discover_endpoint("https://ex.com/p", {"Content-Type": "text/html"}, body), "https://wm.io/ex")

    def test_ignores_rel_without_href(self):
        body = '<link rel="webmention"><link rel="webmention" href="/wm">'
        self.assertEqual(discover_endpoint("https://ex.com/p", {"Content-Type": "text/html"}, body), "https://ex.com/wm")

    def test_empty_href_is_target_itself(self):
        body = '<link rel="webmention" href="">'
        self.assertEqual(discover_endpoint("https://ex.com/p?q=1", {"Content-Type": "text/html"}, body), "https://ex.com/p?q=1")

    def test_skips_html_scan_for_non_html(self):
        body = '<link rel="webmention" href="/wm">'
        self.assertIsNone(discover_endpoint("https://ex.com/p", {"Content-Type": "application/json"}, body))

    def test_none_when_absent(self):
        self.assertIsNone(discover_endpoint("https://ex.com/p", {"Content-Type": "text/html"}, "<p>hi</p>"))


class OutcomeTest(unittest.TestCase):
    def test_2xx_is_sent(self):
        self.assertEqual(outcome(202), "sent")

    def test_4xx_is_rejected(self):
        self.assertEqual(outcome(400), "rejected")

    def test_5xx_is_retry(self):
        self.assertEqual(outcome(503), "retry")

    def test_error_is_retry(self):
        self.assertEqual(outcome(None), "retry")


class FakeScrapbox:
    def __init__(self, pages):
        self.pages = pages

    def list(self, skip):
        return [{"title": t, "updated": p["updated"], "pin": 0} for t, p in self.pages.items()][skip:]

    def page(self, title):
        return self.pages[title]


class RunTest(unittest.TestCase):
    def setUp(self):
        self.scrapbox = FakeScrapbox({"p": {"updated": 200, "lines": [line("p", 200), line("https://example.com/a", 200)]}})
        self.results = []
        self.sent = []

    def deliver(self, source, target):
        self.sent.append((source, target))
        return self.results.pop(0)

    def run_once(self, state, **kw):
        return run(state, self.scrapbox.list, self.scrapbox.page, self.deliver, now=lambda: "T", log=lambda _: None, **kw)

    def test_records_sent_and_advances_since(self):
        self.results = [("sent", 202)]
        state = self.run_once({"since": 100, "sent": {}})
        self.assertEqual(state["sent"]["https://scrapbox.io/yuta25/p"]["https://example.com/a"]["status"], "sent")
        self.assertEqual(state["since"], 200)

    def test_does_not_resend_known_pair(self):
        state = {"since": 100, "sent": {"https://scrapbox.io/yuta25/p": {"https://example.com/a": {"status": "sent"}}}}
        self.run_once(state)
        self.assertEqual(self.sent, [])

    def test_retries_5xx_on_next_run_even_after_since_advanced(self):
        self.results = [("retry", 503)]
        state = self.run_once({"since": 100, "sent": {}})
        self.results = [("sent", 202)]
        state = self.run_once(state)
        self.assertEqual(len(self.sent), 2)
        self.assertEqual(state["sent"]["https://scrapbox.io/yuta25/p"]["https://example.com/a"]["status"], "sent")

    def test_gives_up_after_max_attempts(self):
        self.results = [("retry", 503)] * 3
        state = {"since": 100, "sent": {}}
        for _ in range(3):
            state = self.run_once(state)
        self.results = []
        state = self.run_once(state)
        self.assertEqual(len(self.sent), 3)
        self.assertEqual(state["sent"]["https://scrapbox.io/yuta25/p"]["https://example.com/a"]["status"], "gave_up")

    def test_records_retry_when_delivery_raises(self):
        def broken(source, target):
            self.sent.append((source, target))
            raise ValueError("bad endpoint")

        state = run({"since": 100, "sent": {}}, self.scrapbox.list, self.scrapbox.page, broken, now=lambda: "T", log=lambda _: None)
        self.assertEqual(state["sent"]["https://scrapbox.io/yuta25/p"]["https://example.com/a"]["status"], "retry")

    def test_dry_run_does_not_touch_state(self):
        state = {"since": 100, "sent": {}}
        self.run_once(state, dry_run=True)
        self.assertEqual(state, {"since": 100, "sent": {}})
        self.assertEqual(self.sent, [])


if __name__ == "__main__":
    unittest.main()
