---
name: import-bought
description: Amazon 注文履歴（補助で Gmail）から期間内の購入を拾い、選んだものを「YYYY年買ったもの、捨てたもの」に追記する。「先月の買ったもの取り込んで」「8月の購入を追記して」で使う
---

引数: 期間。省略時は前月。年をまたぐ指定はしない。

## 手順

1. 台帳を読む: `python3 scripts/ledger.py list bought`
2. Amazon 注文履歴を Chrome 拡張で読む
   - tabs_context_mcp → tabs_create_mcp → navigate `https://www.amazon.co.jp/your-orders/orders?timeFilter=year-YYYY`
   - get_page_text で 10 件ずつ。次ページは `&startIndex=10`, `20`, …。期間より前の注文日が出たら止める
   - 1 注文は「注文日 / 合計 / 注文番号 / 商品名…」の並び。id は注文番号、複数商品の注文は `注文番号#n` で商品ごとに分ける
   - 「Amazonギフトカード チャージタイプ」は候補にしない
   - サインイン画面が出たら止めて、ユーザーに Chrome でログインしてもらう。パスワードは扱わない
   - 終わったらタブを閉じる
3. Gmail を補助に使う: search_threads `category:purchases after:YYYY/MM/01 before:YYYY/MM+1/01`。Amazon 以外のショップの注文だけ拾う。除外する送信元は末尾の一覧。id はメールの注文番号、無ければ threadId
4. 台帳にある id を除く。候補を番号付きで一覧にする（日付 / 店 / 品名 / URL）。ユーザーに残す番号を聞く
5. 選ばれなかったものは `ledger.py add bought <id> skipped --title ... --date ...`
6. 追記する
   - `cosense readPage https://scrapbox.io/yuta25/YYYY年買ったもの、捨てたもの` で lines と id を取る
   - `[* 買った]` 節の中で該当月見出し（例 `8月`）を探し、その月の最後の行（次の月見出し、空行、`[* 捨てた]` のいずれかの直前）を anchor にする
   - 月見出しが無ければ、直前の月の末尾に `N月` 行を足してから続ける
   - 行は `\t[商品URL 商品ページのタイトル]`。商品 URL は注文履歴の「商品を表示」リンク（find で href を取る）。ページタイトルは商品名を短くしたものでよい。URL が取れなければ `\t品名`
   - ops を previewEdit に渡し、出力を見せる。ユーザーが OK したら submitEdit
7. 追記したものを `ledger.py add bought <id> added --title ... --date ...`

## Gmail で除外する送信元

- noreply@nsp.mdj.jp（マックデリバリー）
- matsuben-net@matsuyafoods.co.jp（松弁ネット）
- *@stripe.com, invoice+statements@mail.anthropic.com, noreply@tm.openai.com, feedback@slack.com, googleplay-noreply@google.com（サブスク・領収書）
- noreply@flowr.is（花の定期便）
- no-reply@business.amazon.co.jp（宣伝）

新しい種類のノイズを見つけたらここに足す。
