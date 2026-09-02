#!/usr/bin/env python3
"""ledger/<source>.jsonl に候補ごとの added / skipped を記録する。

  ledger.py list <source>
  ledger.py has <source> <id>            (exit 0 = 記録済み)
  ledger.py add <source> <id> <added|skipped> [--title T] [--date D] [--note N]
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def path_for(source):
    return os.path.join(ROOT, "ledger", f"{source}.jsonl")


def load(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def append(path, entry):
    entry = {**entry, "recorded_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")}
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def known_ids(entries):
    return {e["id"] for e in entries}


def filter_new(candidates, entries, key="id"):
    known = known_ids(entries)
    return [c for c in candidates if c[key] not in known]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("list"); p.add_argument("source")
    p = sub.add_parser("has"); p.add_argument("source"); p.add_argument("id")
    p = sub.add_parser("add")
    p.add_argument("source"); p.add_argument("id"); p.add_argument("decision", choices=["added", "skipped"])
    p.add_argument("--title", default=""); p.add_argument("--date", default=""); p.add_argument("--note", default="")
    args = parser.parse_args(argv)

    path = path_for(args.source)
    if args.cmd == "list":
        for e in load(path):
            print(json.dumps(e, ensure_ascii=False))
    elif args.cmd == "has":
        sys.exit(0 if args.id in known_ids(load(path)) else 1)
    elif args.cmd == "add":
        entry = {"id": args.id, "decision": args.decision, "title": args.title, "date": args.date}
        if args.note:
            entry["note"] = args.note
        print(json.dumps(append(path, entry), ensure_ascii=False))


if __name__ == "__main__":
    main()
