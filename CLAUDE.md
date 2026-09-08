# yuta25-wiki

scrapbox.io/yuta25（Cosense。3000 ページ超、公開、誰でも編集可）を Claude Code と一緒に育てるための作業場。Wiki 本体は Cosense にあり、ここにはルール・スキル・台帳・診断レポートだけを置く。

## 手段

- Cosense の読み書きは cosense CLI（cosense skill）。書き込みは previewEdit → submitEdit の二段階
- Amazon 注文履歴・U-NEXT 視聴履歴はログインが要るので Chrome 拡張（mcp__claude-in-chrome__*）で動作中の Chrome を使う。agent-browser は `--profile` でもログインを引き継げない
- Gmail は claude.ai の Gmail 連携。検索と閲覧のみ

## このリポジトリの変更

- main に直接コミットして push する。ブランチも PR も作らない（グローバルの CLAUDE.md より優先）

## 原則

- 密度の高いリンク: 既存ページと結べる箇所を探して結ぶ。リンク付けと診断の基準
- 原子性: 1 ページ 1 概念。長いページの一部が独立した概念なら切り出しを提案する
- 概念指向: ハブは出来事ではなく概念や題材でまとめる。ハブ案の基準
- タイトルは既存ページと同じ語を使う。表記ゆれで新しいリンク先を増やさない。候補を出す前に searchFullText で既存の語を確かめる

## 書き込みの約束

- 候補を番号付きで提示 → ユーザーが残す番号を答える → previewEdit の出力を見せる → submitEdit
- 新規ページは作らない。切り出し案・ハブ案は提案止まり。例外は `/add-movie` の映画ページだけ
- 本文は書き換えない。リンクは末尾に 1 行追加する。本文にリンク先タイトルと完全一致する文字列があるときだけ、その行を `scripts/wrap_link.py` で括った行に replace する
- 削除・リネーム・replaceLinks はしない
- 候補ごとの採用 / 却下を `scripts/ledger.py` で台帳に残す。却下されたものは次回から候補に出さない

## Cosense 記法

- Markdown ではない。`#` 見出し、`-` 箇条書き、`**` は使わない
- インデントはタブ。`[title]` が内部リンク、`#tag` もリンク、`[* 太字]`、`[url タイトル]` が外部リンク
- 表は `table:名前` の次行からタブ区切り

## 決まっている形式

### YYYY seen, read, played

- 行は ` [YYYY/M/D]\t種別\t[作品名]`（先頭は半角スペース 1 つ、区切りはタブ）。日付順
- 日付だけの行はペースメーカーとして先置きした枠。追記は必ず残っている枠のうち最も早い行を replace で埋める（日付は視聴日に書き換える）。insertBefore で行を増やさない
- 種別は同じ年の表で使われている語に合わせる（2025 年以降は 映画 / ドラマ / アニメ / バラエティ / 本 / 漫画 / 雑誌 / ゲーム / ライブ / サッカー）

### YYYY年買ったもの、捨てたもの

- `[* 買った]` の下に月見出し（`1月`）、その下にタブ 1 つで `[商品URL ページタイトル]`。URL が無ければ品名だけ
- 追記位置は該当月の最後の行の次。月見出しが無ければ作る
- `[* 捨てた]` 節には触らない

## ファイル

- `ledger/<source>.jsonl`: 候補ごとの added / skipped。コミットする
- `reports/YYYY-MM-DD.md`: 診断レポート。コミットする
- `tmp/`: スナップショット。gitignore
- `scripts/snapshot.sh`: titles API と listPages で tmp/ を作る
- `scripts/audit.py`: tmp/ から診断レポートを出す
- `scripts/movie_page.py`: ja.wikipedia の記事から映画ページの本文とポスターを作る
- `scripts/seen_frame.py`: seen の枠行を埋める ops を出す
- テストは `python3 -m unittest discover -s tests -t .`

## スキル

- `/import-bought` `/import-seen` `/link-suggest` `/audit` `/add-movie`
