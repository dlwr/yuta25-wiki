#!/usr/bin/env python3
"""scrapbox.io/yuta25 に新しく書いた外部リンクへ Webmention を送る。

  webmention.py run [--dry-run] [--state F]   更新ページの新しいリンクへ送り、state を更新する
  webmention.py send <source> <target>        1 件だけ送る
"""
import argparse
import copy
import ipaddress
import json
import re
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser

UA = "yuta25-wiki/1.0 (https://github.com/dlwr/yuta25-wiki)"
PROJECT = "yuta25"
ME = "582d2da90010d70011386875"
EXCLUDED_HOSTS = ("scrapbox.io", "gyazo.com", "yuta25.on.bolg.in")
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg")
MAX_ATTEMPTS = 3
JST = timezone(timedelta(hours=9))

URL = re.compile(r"https?://[^\s\[\]`<>\"]+")
BACKQUOTED = re.compile(r"`[^`]*`")


def excluded(url):
    parts = urllib.parse.urlsplit(url)
    host = (parts.hostname or "").lower()
    if any(host == h or host.endswith("." + h) for h in EXCLUDED_HOSTS):
        return True
    return parts.path.lower().endswith(IMAGE_EXTENSIONS)


def trim(url):
    while url:
        if url[-1] in ".,;:!?'。、，．！？」』】》〉":
            url = url[:-1]
        elif url[-1] == ")" and url.count("(") < url.count(")"):
            url = url[:-1]
        elif url[-1] == "）" and url.count("（") < url.count("）"):
            url = url[:-1]
        else:
            break
    return url


def extract_links(text):
    out = []
    for match in URL.finditer(BACKQUOTED.sub("", text)):
        url = trim(match.group())
        if url not in out and not excluded(url):
            out.append(url)
    return out


def indent(text):
    return len(text) - len(text.lstrip(" \t"))


def new_links(lines, since, user_id=ME):
    out = []
    block = None
    for line in lines:
        text = line["text"]
        if block is not None and text.strip() and indent(text) > block:
            continue
        block = indent(text) if text.lstrip(" \t").startswith("code:") else None
        if block is not None or line["updated"] <= since or line["userId"] != user_id:
            continue
        for url in extract_links(text):
            if url not in out:
                out.append(url)
    return out


def updated_pages(fetch, since, limit=100):
    out = []
    skip = 0
    while True:
        batch = fetch(skip)
        for page in batch:
            if page["updated"] > since:
                out.append(page)
            elif not page["pin"]:
                return out
        if len(batch) < limit:
            return out
        skip += limit


def page_url(title):
    title = title.replace(" ", "_")
    encoded = ""
    for i, ch in enumerate(title):
        tail = i == len(title) - 1
        if ch in "@$&+=:;\"," and not (tail and ch in ":;\","):
            encoded += ch
        else:
            encoded += urllib.parse.quote(ch, safe="-_.!~*'()")
    return f"https://scrapbox.io/{PROJECT}/{encoded}"


def header(headers, name):
    if hasattr(headers, "get_all"):
        return ", ".join(headers.get_all(name) or [])
    return headers.get(name, "")


def has_webmention_rel(value):
    return "webmention" in value.lower().split()


class RelFinder(HTMLParser):
    def __init__(self):
        super().__init__()
        self.href = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if self.href is None and tag in ("link", "a") and "href" in attrs and has_webmention_rel(attrs.get("rel") or ""):
            self.href = attrs["href"] or ""


def discover_endpoint(url, headers, body):
    for target, params in re.findall(r"<([^>]*)>\s*((?:;[^,<]*)*)", header(headers, "Link")):
        rel = re.search(r'rel\s*=\s*(?:"([^"]*)"|([^\s;,]+))', params)
        if rel and has_webmention_rel(rel.group(1) or rel.group(2)):
            return urllib.parse.urljoin(url, target)
    if "html" not in header(headers, "Content-Type").lower():
        return None
    finder = RelFinder()
    finder.feed(body)
    if finder.href is None:
        return None
    return urllib.parse.urljoin(url, finder.href)


def outcome(code):
    if code is None or code >= 500:
        return "retry"
    if code >= 400:
        return "rejected"
    return "sent"


def run(state, list_pages, get_page, deliver, now, dry_run=False, log=print):
    state = copy.deepcopy(state)
    sent = state["sent"]

    def record(source, target):
        if dry_run:
            log(f"{source}\t{target}")
            return
        try:
            status, code = deliver(source, target)
        except Exception as e:
            log(f"error\t{e!r}\t{source}\t{target}")
            status, code = "retry", None
        entry = sent.setdefault(source, {}).get(target, {})
        attempts = entry.get("attempts", 0) + 1
        if status == "retry" and attempts >= MAX_ATTEMPTS:
            status = "gave_up"
        sent[source][target] = {"status": status, "code": code, "at": now(), "attempts": attempts}
        log(f"{status}\t{code}\t{source}\t{target}")

    for source, targets in list(sent.items()):
        for target, entry in list(targets.items()):
            if entry["status"] == "retry":
                record(source, target)

    pages = updated_pages(list_pages, state["since"])
    for page in pages:
        source = page_url(page["title"])
        for target in new_links(get_page(page["title"])["lines"], state["since"]):
            if target not in sent.get(source, {}):
                record(source, target)
    if pages:
        state["since"] = max(p["updated"] for p in pages)
    return state


def public_host(url):
    host = urllib.parse.urlsplit(url).hostname
    if not host:
        return False
    try:
        infos = socket.getaddrinfo(host, None)
    except OSError:
        return False
    return all(ipaddress.ip_address(info[4][0].split("%")[0]).is_global for info in infos)


def request(url, data=None):
    url = urllib.parse.quote(url, safe=":/?#[]@!$&'()*+,;=%~")
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=10)


def deliver(source, target):
    time.sleep(1)
    if not public_host(target):
        return "rejected", None
    try:
        with request(target) as res:
            endpoint = discover_endpoint(res.geturl(), res.headers, res.read(1_000_000).decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        return ("retry", e.code) if e.code >= 500 else ("no_endpoint", e.code)
    except (urllib.error.URLError, OSError):
        return "retry", None
    if endpoint is None:
        return "no_endpoint", None
    if not public_host(endpoint):
        return "rejected", None
    data = urllib.parse.urlencode({"source": source, "target": target}).encode()
    try:
        with request(endpoint, data) as res:
            code = res.status
    except urllib.error.HTTPError as e:
        code = e.code
    except (urllib.error.URLError, OSError):
        code = None
    return outcome(code), code


def scrapbox(path):
    with request(f"https://scrapbox.io/api/pages/{PROJECT}{path}") as res:
        return json.load(res)


def list_pages(skip):
    return scrapbox(f"?sort=updated&limit=100&skip={skip}")["pages"]


def get_page(title):
    return scrapbox("/" + urllib.parse.quote(title, safe=""))


def now():
    return datetime.now(JST).isoformat(timespec="seconds")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    run_parser = sub.add_parser("run")
    run_parser.add_argument("--dry-run", action="store_true")
    run_parser.add_argument("--state", default="state/webmention.json")
    send_parser = sub.add_parser("send")
    send_parser.add_argument("source")
    send_parser.add_argument("target")
    args = parser.parse_args()

    if args.command == "send":
        print(*deliver(args.source, args.target))
        return

    try:
        with open(args.state) as f:
            state = json.load(f)
    except FileNotFoundError:
        state = None
    if state is None:
        if not args.dry_run:
            with open(args.state, "w") as f:
                json.dump({"since": int(time.time()), "sent": {}}, f, ensure_ascii=False, indent=2)
        print("state が無いので since だけ置いた", file=sys.stderr)
        return

    state = run(state, list_pages, get_page, deliver, now, dry_run=args.dry_run)
    if not args.dry_run:
        with open(args.state, "w") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
            f.write("\n")


if __name__ == "__main__":
    main()
