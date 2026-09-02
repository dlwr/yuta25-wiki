#!/bin/sh
# scrapbox.io/yuta25 のメタデータを tmp/ に落とす。本文は seen 表のページだけ取る。
set -eu
cd "$(dirname "$0")/.."
PROJECT=https://scrapbox.io/yuta25
mkdir -p tmp/seen

curl -sf "$PROJECT/api/pages/yuta25/search/titles" -o tmp/titles.json \
  || curl -sf "https://scrapbox.io/api/pages/yuta25/search/titles" -o tmp/titles.json

count=$(cosense listPages "$PROJECT/" --limit 1 | jq .count)
skip=0
: > tmp/pages_parts.jsonl
while [ "$skip" -lt "$count" ]; do
  cosense listPages "$PROJECT/" --limit 1000 --skip "$skip" --sort title | jq -c '.pages[]' >> tmp/pages_parts.jsonl
  skip=$((skip + 1000))
done
jq -s '{count: length, pages: .}' tmp/pages_parts.jsonl > tmp/pages.json
rm tmp/pages_parts.jsonl

jq -r '.[].title | select(test("^[0-9]{4} seen, read, played$"))' tmp/titles.json | while read -r title; do
  encoded=$(printf '%s' "$title" | jq -sRr @uri)
  cosense readPage "$PROJECT/$encoded" > "tmp/seen/$(printf '%s' "$title" | cut -c1-4).json"
done

echo "titles: $(jq length tmp/titles.json), pages: $(jq .count tmp/pages.json), seen: $(ls tmp/seen | wc -l | tr -d ' ')"
