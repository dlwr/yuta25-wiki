# yuta25-wiki

scrapbox.io/yuta25 を Claude Code と一緒に育てるためのルール・スキル・台帳・診断レポート。使い方は CLAUDE.md。

```sh
python3 -m unittest discover -s tests -t .
scripts/snapshot.sh && python3 scripts/audit.py > reports/$(date +%F).md
```
