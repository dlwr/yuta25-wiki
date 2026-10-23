#!/usr/bin/env python3
"""「YYYY seen, read, played」の枠行（日付だけの行）のうち最も早いものを埋める ops を作る。
枠が残っていなければ表の最後の行の次に 1 行足す。

  seen_frame.py <YYYY/M/D> <種別> <作品名> < readPage.json
  (既に表にあれば exit 2 で ops は出さない)
"""
import json
import re
import sys

FRAME = re.compile(r"^ \[\d{4}/\d{1,2}/\d{1,2}\]$")
ROW = re.compile(r"^ \[\d{4}/\d{1,2}/\d{1,2}\]")


def first_frame(lines):
    for line in lines:
        if FRAME.match(line["text"]):
            return line
    return None


def row(date, kind, title):
    return f" [{date}]\t{kind}\t[{title}]"


def already_recorded(lines, title):
    return any(f"[{title}]" in line["text"] for line in lines)


def ops_for(lines, date, kind, title):
    text = row(date, kind, title)
    frame = first_frame(lines)
    if frame is not None:
        return {"ops": [{"replace": frame["id"], "text": text}]}
    last = max(i for i, line in enumerate(lines) if ROW.match(line["text"]))
    anchor = lines[last + 1]["id"] if last + 1 < len(lines) else "_end"
    return {"ops": [{"insertBefore": anchor, "text": text}]}


def main():
    date, kind, title = sys.argv[1:4]
    lines = json.load(sys.stdin)["lines"]
    if already_recorded(lines, title):
        print(f"既に表にある: [{title}]", file=sys.stderr)
        sys.exit(2)
    print(json.dumps(ops_for(lines, date, kind, title), ensure_ascii=False))


if __name__ == "__main__":
    main()
