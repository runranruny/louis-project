# LOUIS PROJECT 🐱

猫のルイス（@louis_rd_0723）のショート動画運用を、AI社員5名と一緒に回す仕組みです。
ルールの全体像は [`CLAUDE.md`](CLAUDE.md) にあります。

## 毎日の流れ（人間がやること）

入力はすべて Google Sheets「[LOUIS 投稿管理](https://docs.google.com/spreadsheets/d/1xrZ2SEG7w8ar_JFlySex5DzXU55ciO8HGAwwDsP_V1k/edit)」で行います（iPhoneのSheetsアプリでOK）。

| タイミング | やること | タブ |
|---|---|---|
| 投稿前 | 動画を1行登録し、媒体ごとの投稿予定を2行登録する | `videos`・`posts` |
| 投稿後 | `status` を `posted` にし、投稿日時とURLを入れる | `posts` |
| 投稿の24時間後・72時間後 | アプリのインサイトを見て数値を1行ずつ追加 | `metrics` |
| 毎日22時前 | 両媒体のフォロワー数を追加 | `followers` |
| 22:00 | **AIがシートを読んで日報を作成** → `reports/daily/` | 自動 |
| 週1回 | `exports/` のレビュー資料をChatGPTに貼り、結論を `inputs/direction.md` に追記 | 手動 |

> 入力の目安は1日5〜10分。見出しのセルをタップすると、その列の説明が出ます。

## 入力ルール
- 日時は `2026-11-23 19:00` の形式（日本時間）
- **分からない数値は空欄にする。0は本当に0だったときだけ入れる**
- `metrics.csv` の `source` には取得元を書く：`manual_app`（IGアプリ）／`tiktok_studio`／`api`／`csv`
- `completion_rate`（完視聴率）は % の数値（例：41.5）
- IDの付け方の例：動画 `V001`、投稿 `P001-IG`・`P001-TT`

### 各媒体で数値を見る場所
- Instagram：投稿 →「インサイトを見る」（プロアカウントが必要）
- TikTok：動画 →「…」→「アナリティクス」、またはTikTok Studio

## コマンド
```bash
python3 scripts/louis.py validate            # 入力ミスのチェック
python3 scripts/louis.py daily 2026-11-23    # 日報の骨格（数値部分）を作成
python3 scripts/louis.py review              # ChatGPT用の戦略レビュー資料を作成
python3 -m unittest discover -s tests        # テスト
```
Claude Codeでは `/daily` で日報をフル作成できます（AI社員が③〜⑦を記入）。

## フェーズ
- [x] Phase 2：MVP（CSV・AI社員・日報）
- [x] Phase 3：Google Sheets / Drive 連携（シート読み込み・Driveフォルダ）
- [x] Phase 4：毎日22時の定期実行（失敗時もCSVで続行し、日報に記録）
- [ ] Phase 5：週報・コンセプト比較の強化・ChatGPT API連携の検討（費用見積もりと承認のあとで）
