#!/usr/bin/env python3
"""tmp/ のスナップショットから診断レポート(Markdown)を出力する。

入力:
  tmp/titles.json   GET /api/pages/yuta25/search/titles の配列
  tmp/pages.json    listPages を結合した {count, pages}
  tmp/seen/*.json   readPage の出力（YYYY seen, read, played）
"""
import glob
import json
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict

DIARY_TITLE = re.compile(r"^bolg\.in \d{4}-\d{2}-\d{2}$")
SEEN_ROW = re.compile(r"^ \[([^\]]+)\](?:\t([^\t]*)(?:\t\[?([^\]]*)\]?)?)?$")
TYPE_SYNONYMS = [("漫画", "マンガ"), ("本", "小説"), ("Youtube", "YouTube"), ("ライブ", "ライブ配信")]
STRUCTURAL = re.compile(
    r"^(\d{4}(/\d{1,2}(/\d{1,2})?)?|\d{1,2}月|\d{1,2}日"
    r"|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday"
    r"|[月火水木金土日]曜日?|yuta25のボルグ)$"
)
STRIP_CHARS = re.compile(r"[\s　・_\-–—:：!?！？.,、。'\"「」『』()（）]")


def normalize_link(s):
    return s.lower().replace(" ", "_")


def is_structural(title):
    return bool(STRUCTURAL.match(title))


def red_links(titles):
    existing = {normalize_link(t["title"]) for t in titles}
    counter = Counter()
    for t in titles:
        for link in set(t.get("links", [])):
            if normalize_link(link) not in existing and not is_structural(link):
                counter[link] += 1
    return sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))


def inbound_counts(titles):
    counts = defaultdict(int)
    for t in titles:
        me = normalize_link(t["title"])
        for link in {normalize_link(l) for l in t.get("links", [])}:
            if link != me:
                counts[link] += 1
    return counts


def orphans(titles):
    inbound = inbound_counts(titles)
    result = []
    for t in titles:
        me = normalize_link(t["title"])
        outbound = {normalize_link(l) for l in t.get("links", [])} - {me}
        if inbound[me] == 0 and not outbound and not DIARY_TITLE.match(t["title"]):
            result.append(t)
    return sorted(result, key=lambda t: -t.get("updated", 0))


def normalize_title(s):
    return STRIP_CHARS.sub("", unicodedata.normalize("NFKC", s)).lower()


def similar_titles(titles):
    groups = defaultdict(list)
    for t in titles:
        groups[normalize_title(t["title"])].append(t["title"])
    return [g for g in groups.values() if len(g) > 1]


def parse_seen_row(text):
    m = SEEN_ROW.match(text)
    if not m:
        return None
    date, kind, title = m.groups()
    return (date, kind or "", title or "")


def type_counts(lines):
    counts = Counter()
    for line in lines:
        row = parse_seen_row(line)
        if row and row[1]:
            counts[row[1]] += 1
    return dict(counts)


def type_variants(counts):
    return [(a, b) for a, b in TYPE_SYNONYMS if a in counts and b in counts]


def load_snapshot(root):
    titles = json.load(open(os.path.join(root, "tmp/titles.json")))
    pages_path = os.path.join(root, "tmp/pages.json")
    pages = json.load(open(pages_path))["pages"] if os.path.exists(pages_path) else []
    seen = {}
    for path in sorted(glob.glob(os.path.join(root, "tmp/seen/*.json"))):
        page = json.load(open(path))
        seen[page["title"]] = [l["text"] for l in page["lines"]]
    return titles, pages, seen


def render(titles, pages, seen, limit=40):
    meta = {p["title"]: p for p in pages}
    out = []
    out.append(f"# 診断 ({len(titles)} ページ)\n")

    orphan_pages = orphans(titles)
    out.append(f"## 孤立ページ ({len(orphan_pages)} 件。被リンクも発リンクも無い。bolg.in 日記を除く)\n")
    for t in orphan_pages[:limit]:
        views = meta.get(t["title"], {}).get("views", "-")
        out.append(f"- {t['title']} (views {views})")
    out.append("")

    reds = red_links(titles)
    out.append(f"## 未作成なのにリンクされているページ ({len(reds)} 件。日付・曜日・月・日・プロジェクトタグを除く)\n")
    for title, n in reds[:limit]:
        out.append(f"- {title}: {n} ページから")
    out.append("")

    groups = similar_titles(titles)
    out.append(f"## タイトルが同一視できるページ ({len(groups)} 組)\n")
    for g in groups[:limit]:
        out.append("- " + " / ".join(g))
    out.append("")

    out.append("## seen 表の種別\n")
    for title, lines in seen.items():
        counts = type_counts(lines)
        placeholders = sum(1 for l in lines if (r := parse_seen_row(l)) and not r[1])
        summary = ", ".join(f"{k} {v}" for k, v in sorted(counts.items(), key=lambda kv: -kv[1]))
        out.append(f"- {title}: {summary}（枠だけの行 {placeholders}）")
        for a, b in type_variants(counts):
            out.append(f"  - 表記ゆれ: {a} / {b}")
    out.append("")
    return "\n".join(out)


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    titles, pages, seen = load_snapshot(root)
    sys.stdout.write(render(titles, pages, seen))


if __name__ == "__main__":
    main()
