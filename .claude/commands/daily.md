---
description: LOUIS DAILY REPORT を作成する（毎日22:00の定期実行で使う）
---
LOUIS DAILY REPORT を作成してください。日付の指定があれば $ARGUMENTS を使い、なければ今日（JST）です。

0. **Google Sheetsから最新データを取り込む**：`config/project.toml` の `[google].sheet_id` のシートについて、Google Sheetsコネクタの get_values で `動画!A:L`、`投稿!A:H`、`数値!A:N`、`フォロワー!A:E`、`企画変更履歴!A:E`、`素材!A:H` を読む（タブ名・見出し・選択肢は日本語。変換は import-sheet が行う）。結果をタブ名をキーにした `{"動画": values, "投稿": values, ...}` のJSONで `/tmp/sheet.json` に保存し（values が無いタブは見出し行だけでなく空配列にせず、取得できた values をそのまま入れる）、`python3 scripts/louis.py import-sheet /tmp/sheet.json` を実行する。コネクタが使えない・取り込みがエラーになった場合は、リポジトリ内の既存CSVで続行し、日報の「データ品質」にその旨を書く
1. `inputs/direction.md` と `CLAUDE.md` を読む
2. `python3 scripts/louis.py validate` を実行。エラーは日報の「データ品質」に載せる
3. `python3 scripts/louis.py daily $ARGUMENTS` を実行。`reports/daily/YYYY-MM-DD.md` が生成される（①②・未取得データ・コンセプト別集計は確定値）
4. 以下のAI社員にサブエージェントとして依頼する（並行で可）
   - analyst：③GOOD ④MORE ⑤今日の学び
   - planner：⑥明日の企画3案（各案に必須項目をすべて付ける）
5. edit-director に、planner の3案それぞれの「編集ポイント」（短い台本の要点）を書かせる
6. strategy-lead に③〜⑥を確認させ、方針（`inputs/direction.md`）や安全ルールと矛盾があれば修正指示を出させる
7. pm が⑦明日の最重要アクション（最大3つ）と「人間が対応すべき事項」をまとめ、日報ファイルの「（AI社員が記入）」の箇所を埋めて保存する
8. ①②の数値は変更しない。データが無い項目は「未取得」のまま残す
9. git が使える場合は `reports/` と、手順0で取り込んだ `data/`（シートのスナップショット）をコミットして push する。シート自体はAIが書き換えない
10. 最後に日報の要点（最重要アクション3つ）を短く報告する
