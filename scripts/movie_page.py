#!/usr/bin/env python3
"""ja.wikipedia の映画記事から、既存の映画ページと同じ並びの Cosense 本文を作る。

  movie_page.py search <邦題>                                   記事候補を出す
  movie_page.py body <記事名> [--poster URL] [--impression TEXT] [--wikitext FILE]
  movie_page.py poster <記事名> --out <path>                     en.wikipedia のポスターを保存する
"""
import argparse
import html
import json
import re
import sys
import urllib.parse
import urllib.request

UA = "yuta25-wiki/1.0 (https://github.com/dlwr/yuta25-wiki)"

COUNTRIES = {
    "USA": "アメリカ合衆国", "JPN": "日本", "GBR": "イギリス", "UK": "イギリス", "FRA": "フランス",
    "DEU": "ドイツ", "GER": "ドイツ", "ITA": "イタリア", "ESP": "スペイン", "KOR": "韓国",
    "CHN": "中華人民共和国", "PRC": "中華人民共和国", "TWN": "中華民国", "HKG": "香港", "CAN": "カナダ", "AUS": "オーストラリア",
    "IND": "インド", "RUS": "ロシア", "SWE": "スウェーデン", "DNK": "デンマーク", "DEN": "デンマーク",
    "NOR": "ノルウェー", "FIN": "フィンランド", "NLD": "オランダ", "NED": "オランダ", "BEL": "ベルギー",
    "CHE": "スイス", "SUI": "スイス", "AUT": "オーストリア", "POL": "ポーランド", "IRN": "イラン",
    "MEX": "メキシコ", "BRA": "ブラジル", "ARG": "アルゼンチン", "IRL": "アイルランド", "NZL": "ニュージーランド",
    "PRT": "ポルトガル", "GRC": "ギリシャ", "TUR": "トルコ", "ISR": "イスラエル", "THA": "タイ",
    "PHL": "フィリピン", "IDN": "インドネシア", "VNM": "ベトナム", "HUN": "ハンガリー", "CZE": "チェコ",
    "ROU": "ルーマニア", "WORLD": "世界",
    "CHINA": "中華人民共和国", "JAPAN": "日本", "FRANCE": "フランス", "TAIWAN": "中華民国", "HONG KONG": "香港",
    "KOREA": "韓国", "SOUTH KOREA": "韓国", "GERMANY": "ドイツ", "ITALY": "イタリア", "SPAIN": "スペイン",
}
LANG_EDITIONS = {"en": "英語版", "fr": "フランス語版", "de": "ドイツ語版", "ko": "韓国語版", "zh": "中国語版",
                 "it": "イタリア語版", "es": "スペイン語版", "ru": "ロシア語版"}

SKIP_PARAMS = {"画像", "画像サイズ", "画像解説", "前作", "次作", "作品名", "原題"}
LABELS = {"制作費": "製作費"}
PLAIN_PARAMS = {"公開", "上映時間", "製作国", "言語", "製作費", "興行収入", "配給収入"}
DROP_LINK_PREFIXES = ("ファイル:", "file:", "画像:", "image:", "category:", "カテゴリ:")

TEMPLATE = re.compile(r"\{\{([^{}]*)\}\}", re.DOTALL)
LINK = re.compile(r"\[\[([^\[\]|]*)(?:\|([^\[\]]*))?\]\]")


def country_name(code):
    return COUNTRIES.get(code.strip().upper(), code.strip())


def render_template(body, keep_links):
    parts = [p.strip() for p in body.split("|")]
    name = parts[0].lower()
    positional = [p for p in parts[1:] if "=" not in p]
    if name in ("仮リンク", "ill2") and positional:
        edition = LANG_EDITIONS.get(positional[1].lower(), f"{positional[1]}版") if len(positional) > 1 else "英語版"
        display = f"[{positional[0]}]" if keep_links else positional[0]
        return f"{display}（{edition}）"
    if name == "flagicon" and positional:
        return f"{country_name(positional[0])}の旗 "
    if name in ("flag", "flagcountry") and positional:
        return f"{country_name(positional[0])}の旗 {country_name(positional[0])}"
    if name.upper() in COUNTRIES:
        return f"{country_name(name)}の旗 {country_name(name)}"
    if name == "lang" and len(positional) > 1:
        return positional[1]
    if name.startswith("lang-") and positional:
        return positional[0]
    if name in ("nowrap", "small", "big", "center") and positional:
        return positional[0]
    if name in ("plainlist", "unbulleted list", "ubl", "flatlist", "hlist"):
        items = []
        for p in positional:
            items.extend(re.sub(r"^\*\s*", "", line.strip()) for line in p.splitlines() if line.strip())
        return "<br />".join(items)
    return ""


def render_templates(text, keep_links=True):
    while True:
        new = TEMPLATE.sub(lambda m: render_template(m.group(1), keep_links), text)
        if new == text:
            return text
        text = new


def strip_prefixed_links(text):
    out = []
    i = 0
    while i < len(text):
        if text.startswith("[[", i) and text[i + 2:].lstrip().lower().startswith(DROP_LINK_PREFIXES):
            depth = 0
            j = i
            while j < len(text):
                if text.startswith("[[", j):
                    depth += 1
                    j += 2
                elif text.startswith("]]", j):
                    depth -= 1
                    j += 2
                    if depth == 0:
                        break
                else:
                    j += 1
            i = j
            continue
        out.append(text[i])
        i += 1
    return "".join(out)


def convert_link(m, keep_links):
    display = (m.group(2) if m.group(2) is not None else m.group(1)).strip()
    if not keep_links:
        return display
    year = re.fullmatch(r"(\d{4})年", display)
    if year:
        return f"[{year.group(1)}]年"
    return f"[{display}]"


def convert_inline(text, keep_links=True):
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    text = re.sub(r"<ref\b[^>]*/>", "", text)
    text = re.sub(r"<ref\b[^>]*>.*?</ref>", "", text, flags=re.DOTALL)
    text = render_templates(text, keep_links)
    text = strip_prefixed_links(text)
    text = LINK.sub(lambda m: convert_link(m, keep_links), text)
    if keep_links:
        text = re.sub(r"(原題|英題)([:：]\s*)''([^']+?)''", r"\1\2[\3]", text)
    text = text.replace("'''", "").replace("''", "")
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text.replace("&nbsp;", " "))
    return re.sub(r" {2,}", " ", text).strip()


def find_infobox(text):
    m = re.search(r"\{\{\s*Infobox", text, re.IGNORECASE)
    if not m:
        return None
    depth = 0
    i = m.start()
    while i < len(text):
        if text.startswith("{{", i):
            depth += 1
            i += 2
        elif text.startswith("}}", i):
            depth -= 1
            i += 2
            if depth == 0:
                return m.start(), i
        else:
            i += 1
    return None


def split_params(body):
    segments = []
    depth = 0
    current = []
    i = 0
    while i < len(body):
        two = body[i:i + 2]
        if two in ("{{", "[["):
            depth += 1
            current.append(two)
            i += 2
        elif two in ("}}", "]]"):
            depth -= 1
            current.append(two)
            i += 2
        elif body[i] == "|" and depth == 0:
            segments.append("".join(current))
            current = []
            i += 1
        else:
            current.append(body[i])
            i += 1
    segments.append("".join(current))
    return segments


def parse_infobox(text):
    span = find_infobox(text)
    if span is None:
        return []
    body = text[span[0] + 2:span[1] - 2]
    params = []
    for segment in split_params(body)[1:]:
        if "=" not in segment:
            continue
        key, value = segment.split("=", 1)
        params.append((key.strip(), value.strip()))
    return params


def infobox_rows(params):
    rows = []
    for key, raw in params:
        if key in SKIP_PARAMS or not raw:
            continue
        keep_links = key not in PLAIN_PARAMS
        rendered = render_templates(raw, keep_links)
        values = []
        for part in re.split(r"<br\s*/?>|\n", rendered):
            value = convert_inline(re.sub(r"^\*\s*", "", part.strip()), keep_links)
            if value:
                values.append(value)
        if values:
            rows.append((LABELS.get(key, key), values))
    return rows


def lead_paragraphs(text):
    span = find_infobox(text)
    if span:
        text = text[:span[0]] + text[span[1]:]
    text = text.split("\n==", 1)[0]
    paragraphs = []
    for block in re.split(r"\n\s*\n", text):
        converted = convert_inline("".join(block.splitlines()))
        if converted:
            paragraphs.append(converted)
    return paragraphs


def section_bullets(text, name):
    m = re.search(rf"^==+\s*{re.escape(name)}\s*==+\s*$", text, re.MULTILINE)
    if not m:
        return []
    body = text[m.end():].split("\n==", 1)[0]
    bullets = []
    for line in body.splitlines():
        if line.startswith("*") and not line.startswith("**"):
            converted = convert_inline(line[1:].strip())
            if converted:
                bullets.append(converted)
    return bullets


def wikipedia_url(article):
    return "https://ja.wikipedia.org/wiki/" + urllib.parse.quote(article.replace(" ", "_"), safe="()_,!:/'")


def build_body(article, wikitext, poster=None, impression=None):
    params = parse_infobox(wikitext)
    named = dict(params)
    title = convert_inline(named.get("作品名", ""), keep_links=False) or re.sub(r"\s*\([^()]*\)$", "", article)
    original = convert_inline(named.get("原題", ""), keep_links=False)
    lines = [title]
    if poster:
        lines.append(f"[{poster}]")
    lines.append("")
    lines.extend([impression, ""] if impression else [""])
    lines.extend(f"> {p}" for p in lead_paragraphs(wikitext))
    lines.append("")
    cast = section_bullets(wikitext, "キャスト")
    if cast:
        lines.extend(f"> {c}" for c in cast)
        lines.append("")
    lines.append("table:info")
    if original:
        lines.append(f"\t{title}")
        lines.append(f"\t{original}")
    for label, values in infobox_rows(params):
        lines.append(f"\t{label}\t{values[0]}")
        lines.extend(f"\t\t{v}" for v in values[1:])
    lines.append(f"[{wikipedia_url(article)} {article} - Wikipedia]")
    return "\n".join(lines) + "\n"


def original_and_year(wikitext):
    named = dict(parse_infobox(wikitext))
    original = convert_inline(named.get("原題") or named.get("英語題") or "", keep_links=False) or None
    year = re.search(r"\d{4}", convert_inline(named.get("公開") or named.get("公開日") or "", keep_links=False))
    return original, year.group(0) if year else None


def pick_article(hits):
    for h in hits:
        if re.search(r"\((?:\d{4} )?[^()]*film\)$", h["title"]):
            return h["title"]
    return hits[0]["title"] if hits else None


def pick_poster(titles):
    for t in titles:
        if "poster" in t.lower():
            return t
    for t in titles:
        if t.lower().endswith((".jpg", ".jpeg", ".png")):
            return t
    return None


def api(host, **params):
    params["format"] = "json"
    url = f"https://{host}/w/api.php?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req) as res:
        return json.load(res)


def first_page(data):
    return next(iter(data["query"]["pages"].values()))


def fetch_wikitext(article):
    page = first_page(api("ja.wikipedia.org", action="query", prop="revisions", rvprop="content",
                          rvslots="main", redirects=1, titles=article))
    if "missing" in page:
        sys.exit(f"記事が無い: {article}")
    return page["revisions"][0]["slots"]["main"]["*"]


def cmd_search(args):
    data = api("ja.wikipedia.org", action="query", list="search", srsearch=f"{args.title} 映画", srlimit=10)
    for r in data["query"]["search"]:
        print(f"{r['title']}\t{re.sub(r'<[^>]+>', '', r['snippet'])}")


def cmd_body(args):
    wikitext = open(args.wikitext, encoding="utf-8").read() if args.wikitext else fetch_wikitext(args.article)
    sys.stdout.write(build_body(args.article, wikitext, poster=args.poster, impression=args.impression))


def cmd_poster(args):
    original, year = original_and_year(fetch_wikitext(args.article))
    if not original:
        sys.exit("Infobox に原題が無い")
    hits = []
    for query in (f'"{original}" {year or ""} film', f"{original} {year or ''} film"):
        hits += api("en.wikipedia.org", action="query", list="search", srsearch=query, srlimit=5)["query"]["search"]
    article = pick_article(hits)
    if not article:
        sys.exit("en.wikipedia に記事が無い")
    page = first_page(api("en.wikipedia.org", action="query", prop="images", imlimit=50, titles=article))
    chosen = pick_poster([i["title"] for i in page.get("images", [])])
    if not chosen:
        sys.exit(f"ポスターが無い: {article}")
    info = first_page(api("en.wikipedia.org", action="query", prop="imageinfo", iiprop="url", titles=chosen))
    url = info["imageinfo"][0]["url"]
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req) as res, open(args.out, "wb") as f:
        f.write(res.read())
    print(f"{args.out}\t{article}\t{url}")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("search")
    p.add_argument("title")
    p.set_defaults(func=cmd_search)
    p = sub.add_parser("body")
    p.add_argument("article")
    p.add_argument("--poster")
    p.add_argument("--impression")
    p.add_argument("--wikitext")
    p.set_defaults(func=cmd_body)
    p = sub.add_parser("poster")
    p.add_argument("article")
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_poster)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
