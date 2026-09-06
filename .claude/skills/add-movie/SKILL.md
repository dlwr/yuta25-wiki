---
name: add-movie
description: 見た映画のページを Cosense に作り、「YYYY seen, read, played」の枠を埋める。「〇〇っていう映画見た」「映画のページ作って」で使う
---

引数: 邦題。視聴日（無ければ今日）と感想が言われていればそれも使う。

## 手順

1. 既にページがあるか見る: `cosense browsePage 'https://scrapbox.io/yuta25/<邦題>'`。あれば作らず手順 5 へ
2. 記事を特定する: `python3 scripts/movie_page.py search '<邦題>'`。記事名は `〇〇 (映画)` や `〇〇 (2015年の映画)` のことが多い。監督・年で 1 つに絞れなければ候補を番号付きで出して聞く
3. ポスターを上げる: `python3 scripts/movie_page.py poster '<記事名>' --out tmp/poster.jpg` → `cosense uploadFile https://scrapbox.io/yuta25 tmp/poster.jpg` の embedUrl を控える。exit 1（原題が無い、en.wikipedia に無い）ならポスター無しで進む
4. ページを作る
   - `python3 scripts/movie_page.py body '<記事名>' --poster <embedUrl> [--impression '<感想>'] > tmp/body.txt`
   - 本文を読む。キャストの `>` 行が 10 行を超えるなら、`table:info` の出演者に載っている人物の行だけ残す。それ以外は手で直さない
   - `cosense previewEdit --new --input-file tmp/body.txt https://scrapbox.io/yuta25` の出力を見せて `cosense submitEdit`。previewId は 5 分で切れるので、preview と submit は 1 つのコマンドで続けて実行する（submitEdit の確認プロンプトが承認になる）
5. seen の枠を埋める（YYYY は視聴日の年）
   - `cosense readPage 'https://scrapbox.io/yuta25/YYYY seen, read, played' > tmp/seen.json`
   - `python3 scripts/seen_frame.py YYYY/M/D 映画 '<邦題>' < tmp/seen.json > tmp/seen_ops.json`。exit 1 は枠が残っていない。行を足さずにその旨を報告する。exit 2 は既に表にある
   - pageId は `jq -r .id tmp/seen.json`。`cosense previewEdit --input-file tmp/seen_ops.json https://scrapbox.io/yuta25 <pageId>` → 手順 4 と同じく submit まで続けて実行する
6. 報告する: ページ URL、感想を入れていなければポスターの下の空行に書く旨

## やらないこと

- 本文の書き換え、既存ページへの上書き
- 枠が無いときの insertBefore。枠はペースメーカーなので増やさない
