#!/usr/bin/env python3
"""ja.wikipedia に無い映画記事の下書きに使う調べ物。投稿はしない。

  wiki_draft.py ids <lang> <記事名>            Wikidata から各言語版の記事名と外部 DB の URL を出す
  wiki_draft.py source <lang> <記事名> --out F  その言語版の本文を保存し、記事名・oldid・時刻を出す
  wiki_draft.py check <ja 記事名>...           ja での有無。missing / disambig / redirect / exists と冒頭 1 文
  wiki_draft.py summary <lang>:<記事名>:<oldid>...   要約欄の文面と、ノートに貼る翻訳告知を出す
"""
import argparse
import json
import sys
import urllib.parse
import urllib.request

UA = "yuta25-wiki/1.0 (https://github.com/dlwr/yuta25-wiki)"
LLM = "Claude (claude-fable-5-1)"

DATABASES = {
    "P7222": ("映画.com", "https://eiga.com/movie/{}/"),
    "P2465": ("allcinema", "https://www.allcinema.net/cinema/{}"),
    "P2508": ("KINENOTE", "https://www.kinenote.com/main/public/cinema/detail.aspx?cinema_id={}"),
    "P2509": ("MOVIE WALKER", "https://moviewalker.jp/{}/"),
    "P3704": ("KMDb", "https://www.kmdb.or.kr/db/kor/detail/movie/{}"),
    "P8921": ("KOFIC", "https://www.koreanfilm.or.kr/eng/films/index/filmsView.jsp?movieCd={}"),
    "P345": ("IMDb", "https://www.imdb.com/title/{}/"),
    "P4947": ("TMDb", "https://www.themoviedb.org/movie/{}"),
    "P1562": ("AllMovie", "https://www.allmovie.com/movie/{}"),
}


def external_ids(entity):
    out = {}
    for prop, (name, url) in DATABASES.items():
        for claim in entity.get("claims", {}).get(prop, []):
            value = claim["mainsnak"].get("datavalue", {}).get("value")
            if isinstance(value, str):
                out[name] = url.format(value)
    return out


def sitelinks(entity):
    return {site[:-4]: link["title"] for site, link in entity.get("sitelinks", {}).items() if site.endswith("wiki")}


def classify(page, redirects):
    extract = page.get("extract", "").strip()
    if page.get("missing"):
        return "missing", page["title"], ""
    if "disambiguation" in page.get("pageprops", {}):
        return "disambig", page["title"], extract
    if any(r["to"] == page["title"] for r in redirects):
        return "redirect", page["title"], extract
    return "exists", page["title"], extract


def revision(api):
    page = api["query"]["pages"][0]
    if "revisions" not in page:
        return None
    rev = page["revisions"][0]
    return page["title"], rev["revid"], rev["timestamp"], rev["slots"]["main"]["content"]


def summary_line(sources, llm=LLM):
    declared = f"{llm} の補助で下書きを作成し、全文と出典を人手で確認"
    if not sources:
        return declared
    cited = "、".join(f"[[{lang}:{title}]] oldid={revid}" for lang, title, revid in sources)
    return f"{cited} を一部翻訳。{declared}"


def translation_notices(sources):
    return [f"{{{{翻訳告知|{lang}|{title}|version={revid}|insertversion=}}}}" for lang, title, revid in sources]


def api_get(host, params):
    url = f"https://{host}/w/api.php?" + urllib.parse.urlencode({**params, "format": "json", "formatversion": "2"})
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req) as res:
        return json.load(res)


def fetch_entity(lang, title):
    data = api_get("www.wikidata.org", {
        "action": "wbgetentities", "sites": f"{lang}wiki", "titles": title,
        "props": "sitelinks|claims|labels", "languages": "ja|en|ko",
    })
    entity = next(iter(data["entities"].values()))
    return None if "missing" in entity else entity


def fetch_revision(lang, title):
    return revision(api_get(f"{lang}.wikipedia.org", {
        "action": "query", "prop": "revisions", "rvprop": "ids|content|timestamp", "rvslots": "main",
        "redirects": "1", "titles": title,
    }))


def fetch_classification(title):
    data = api_get("ja.wikipedia.org", {
        "action": "query", "prop": "extracts|pageprops", "exintro": "1", "explaintext": "1", "exsentences": "1",
        "ppprop": "disambiguation", "redirects": "1", "titles": title,
    })
    return classify(data["query"]["pages"][0], data["query"].get("redirects", []))


def cmd_ids(args):
    entity = fetch_entity(args.lang, args.title)
    if entity is None:
        sys.exit(f"Wikidata に {args.lang}:{args.title} が無い")
    print(entity["id"], "ja label:", entity.get("labels", {}).get("ja", {}).get("value", "—"))
    for lang, title in sorted(sitelinks(entity).items()):
        print(f"{lang}\t{title}")
    for name, url in external_ids(entity).items():
        print(f"{name}\t{url}")


def cmd_source(args):
    rev = fetch_revision(args.lang, args.title)
    if rev is None:
        sys.exit(f"{args.lang}.wikipedia に {args.title} が無い")
    title, revid, timestamp, content = rev
    with open(args.out, "w") as f:
        f.write(content)
    print(f"{args.lang}:{title}:{revid}\t{timestamp}\t{args.out}")


def cmd_check(args):
    for title in args.titles:
        status, resolved, extract = fetch_classification(title)
        note = f" -> {resolved}" if resolved != title else ""
        print(f"{status}\t{title}{note}\t{extract[:80]}")


def parse_source(spec):
    lang, rest = spec.split(":", 1)
    title, revid = rest.rsplit(":", 1)
    return lang, title, int(revid)


def cmd_summary(args):
    sources = [parse_source(spec) for spec in args.sources]
    print(summary_line(sources))
    for notice in translation_notices(sources):
        print(notice)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("ids")
    p.add_argument("lang")
    p.add_argument("title")
    p.set_defaults(func=cmd_ids)
    p = sub.add_parser("source")
    p.add_argument("lang")
    p.add_argument("title")
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_source)
    p = sub.add_parser("check")
    p.add_argument("titles", nargs="+")
    p.set_defaults(func=cmd_check)
    p = sub.add_parser("summary")
    p.add_argument("sources", nargs="*")
    p.set_defaults(func=cmd_summary)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
