---
name: import-seen
description: U-NEXT の視聴履歴（動画・書籍）から未記録の作品を拾い、選んだものを「YYYY seen, read, played」の表に追記する。「U-NEXTで見たもの取り込んで」「seenを更新して」で使う
---

## 手順

1. 台帳を読む: `python3 scripts/ledger.py list seen`
2. 今年の表を読む: `cosense readPage https://scrapbox.io/yuta25/YYYY%20seen,%20read,%20played`。既にある作品名の集合と、日付だけの枠行（id と日付）を控える
3. U-NEXT を Chrome 拡張で読む。ログイン済みの Chrome が前提
   - tabs_context_mcp → tabs_create_mcp → navigate `https://video.unext.jp/library/history/video`
   - 一覧は SPA なので get_page_text には出ない。find「視聴履歴一覧の作品タイトルのリンク」で取る。href は `/play/SID0033416/ED...` の形で、SID が作品 id
   - 続けて `https://video.unext.jp/library/history/book`（雑誌・マンガ・書籍）。id は href 中の作品 id
   - 履歴に視聴日は無い
   - 終わったらタブを閉じる
4. 台帳にある id と、表に既にある作品名を除く。候補を番号付きで一覧にする（作品名 / 動画か書籍か / 推定種別）。ユーザーに「残す番号と、それぞれの視聴日と種別」を聞く。日付の指定が無いものは今日の日付
5. 選ばれなかったものは `ledger.py add seen <id> skipped --title ...`
6. 追記する
   - 行は ` [YYYY/M/D]\t種別\t[作品名]`。先頭は半角スペース 1 つ、区切りはタブ。作品名は U-NEXT の表記から《ニューマスター版》のような版表記を落とす。既に感想ページがあるならそのタイトルに合わせる（searchFullText で確認）
   - 枠行（日付だけの行）はペースメーカー。残っている枠のうち最も早い行から順に replace で埋める。複数追記するときは視聴日順に並べて先頭の枠から詰める。insertBefore で行を増やさない
   - 種別は同じ年の表で使われている語（映画 / ドラマ / アニメ / バラエティ / 本 / 漫画 / 雑誌 / ゲーム）
   - previewEdit → 出力を見せる → OK なら submitEdit
7. 追記したものを `ledger.py add seen <id> added --title ... --date ...`
