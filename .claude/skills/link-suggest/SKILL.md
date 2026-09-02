---
name: link-suggest
description: 指定ページに関連する既存ページを探し、選ばれたリンクを末尾行または本文中の完全一致箇所に付ける。「このページにリンク足して」「関連ページ探して」で使う
---

引数: ページタイトル。省略時は `cosense listPages https://scrapbox.io/yuta25/ --sort updated` の先頭（bolg.in 日記を除く）。

## 手順

1. `cosense readPage` で本文と `links`（既にリンク済みのタイトル）を取る
2. 候補を集める。理由を 1 行ずつ添える
   - `cosense searchVector https://scrapbox.io/yuta25/ "<タイトルと本文の要点>"`
   - `cosense list2hopLinks` で 2 hop 先
   - 本文中の固有名詞（人名・作品名・場所・製品名）を `cosense searchFullText` で引き、同じ語をタイトルに持つページ
   - 既に `links` にあるもの、日付ページ、bolg.in 日記は除く
3. 台帳 `python3 scripts/ledger.py list links` を見て、同じ (ページ, 候補) で skipped 済みのものは出さない。id は `<ページタイトル>|<候補タイトル>`
4. 候補を番号付きで一覧にする。ユーザーに残す番号を聞く
5. ops を組む
   - 本文の行にリンク先タイトルと完全一致する文字列がある: `printf '%s' "<行>" | python3 scripts/wrap_link.py "<タイトル>"` の出力で replace。exit 1 なら括れない行なので次へ
   - それ以外: ページ末尾の行を anchor に `insertBefore: _end` で `[A] [B] [C]` の 1 行。末尾が既にリンクだけの行なら、その行に足した内容で replace
6. previewEdit → 出力を見せる → OK なら submitEdit
7. 採用は `ledger.py add links "<id>" added`、却下は skipped

## 提案だけにするもの

- 切り出し: 本文の一部が独立した概念で、他ページからもリンクされそうなら「`[候補タイトル]` として切り出せる」と書く。ページは作らない
- 既存ページと同じ題材なのに別の語で書かれている箇所は、その語を指摘するだけにする
