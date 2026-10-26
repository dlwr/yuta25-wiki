---
name: add-game
description: クリアしたゲームのページを Cosense に作り、「YYYY seen, read, played」の枠を埋める。「〇〇をクリアした」「ゲームのページ作って」で使う
---

引数: ゲーム名。クリア日（無ければ今日）と感想が言われていればそれも使う。

## 手順

1. 記事名を決める: `cosense searchFullText https://scrapbox.io/yuta25 '<ゲーム名>'` で既存の表記を確かめ、ja.wikipedia の記事名に合わせる（`FILE23` のような副題も含める）。既にページがあれば作らず手順 4 へ
2. 冒頭文を取る: `curl -s "https://ja.wikipedia.org/w/api.php?action=query&prop=extracts&exintro=1&explaintext=1&redirects=1&format=json&titles=<URL エンコードした記事名>"`。記事が無ければ公式サイトか Steam の紹介文を使う
3. ページを作る
   - 本文は既存のゲームページ（[Öoo] [Clair Obscur: Expedition 33]）と同じ並び

     ```
     <記事名>

     <感想。無ければ空行のまま>

     > <冒頭文。会社名・発売年は [ ] で括る>
     [<ja.wikipedia の URL> <記事名> - Wikipedia]
     ```
   - `tmp/game.txt` に書き、`cosense previewEdit --new --input-file tmp/game.txt https://scrapbox.io/yuta25` の出力を見せて、OK なら preview を取り直して `cosense submitEdit`（previewId は 5 分で切れる）
4. seen の枠を埋める（YYYY はクリア日の年）
   - `cosense readPage 'https://scrapbox.io/yuta25/YYYY seen, read, played' > tmp/seen.json`
   - `python3 scripts/seen_frame.py YYYY/M/D ゲーム '<記事名>' < tmp/seen.json > tmp/seen_ops.json`。exit 2 は既に表にある
   - `cosense previewEdit --input-file tmp/seen_ops.json https://scrapbox.io/yuta25 $(jq -r .id tmp/seen.json)` → 手順 3 と同じく submit
5. 報告する: ページ URL。感想と画像が無ければ、タイトルの下に自分で足す旨

## やらないこと

- 画像の取得。ゲームのキービジュアルは決まった取得元が無い
- 本文の書き換え、既存ページへの上書き
