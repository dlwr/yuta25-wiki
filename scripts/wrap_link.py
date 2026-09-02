#!/usr/bin/env python3
"""行の中で [ ] や ` ` の外側にあるタイトル文字列を [タイトル] に括る。

  wrap_link.py <title> < line   (該当なしなら exit 1、出力なし)
"""
import sys


def wrap(line, title):
    out = []
    i = 0
    depth = 0
    in_code = False
    changed = False
    n = len(title)
    while i < len(line):
        ch = line[i]
        if ch == "`":
            in_code = not in_code
        elif not in_code and ch == "[":
            depth += 1
        elif not in_code and ch == "]" and depth > 0:
            depth -= 1
        elif not in_code and depth == 0 and line.startswith(title, i):
            out.append(f"[{title}]")
            i += n
            changed = True
            continue
        out.append(ch)
        i += 1
    return "".join(out) if changed else None


def main():
    title = sys.argv[1]
    line = sys.stdin.read().rstrip("\n")
    result = wrap(line, title)
    if result is None:
        sys.exit(1)
    print(result)


if __name__ == "__main__":
    main()
