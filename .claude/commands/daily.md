---
description: LOUIS DAILY REPORT を作成する（毎日22:00の定期実行で使う）
---
LOUIS DAILY REPORT を作成してください。日付の指定があれば $ARGUMENTS を使い、なければ今日（JST）です。

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
9. git が使える場合は `reports/` の変更だけをコミットして push する（`data/` は変更しない）
10. 最後に日報の要点（最重要アクション3つ）を短く報告する
