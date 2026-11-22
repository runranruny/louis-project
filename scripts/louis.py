#!/usr/bin/env python3
"""LOUIS PROJECT 集計ツール（標準ライブラリのみ）

使い方:
  python3 scripts/louis.py validate              データの入力ミスを確認
  python3 scripts/louis.py daily [YYYY-MM-DD]    日報の骨格を reports/daily/ に生成
  python3 scripts/louis.py review [YYYY-MM-DD]   ChatGPT用の戦略レビューを exports/ に生成

方針: 取得できていない値は None（表示は「未取得」）。0 と混同しない。
"""
from __future__ import annotations

import argparse
import csv
import sys
import tomllib
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from statistics import mean

PLATFORMS = ("instagram", "tiktok")
PLATFORM_LABEL = {"instagram": "Instagram", "tiktok": "TikTok"}
CONCEPTS = ("A", "B", "C")
STATUSES = ("planned", "ready", "posted", "skipped")
SNAPSHOTS = ("24h", "72h", "7d", "other")
METRIC_FIELDS = ("views", "reach", "avg_watch_sec", "completion_rate", "likes",
                 "comments", "saves", "shares", "follows_gained")
MIN_SAMPLE = 3           # これ未満は「参考値」
REPORT_HOUR = 22         # 日報の基準時刻（JST）
NA = "未取得"


# ---------- 読み込み ----------

@dataclass
class Data:
    videos: list[dict] = field(default_factory=list)
    posts: list[dict] = field(default_factory=list)
    metrics: list[dict] = field(default_factory=list)
    followers: list[dict] = field(default_factory=list)
    changes: list[dict] = field(default_factory=list)


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as f:
        return [{k: (v or "").strip() for k, v in row.items() if k} for row in csv.DictReader(f)]


def load_data(root: Path) -> Data:
    d = root / "data"
    return Data(
        videos=read_csv(d / "videos.csv"),
        posts=read_csv(d / "posts.csv"),
        metrics=read_csv(d / "metrics.csv"),
        followers=read_csv(d / "followers.csv"),
        changes=read_csv(d / "concept_changes.csv"),
    )


def load_config(root: Path) -> dict:
    with (root / "config" / "project.toml").open("rb") as f:
        return tomllib.load(f)


def parse_date(s: str) -> date | None:
    return datetime.strptime(s, "%Y-%m-%d").date() if s else None


def parse_dt(s: str) -> datetime | None:
    if not s:
        return None
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    raise ValueError(f"日時の形式が不正: {s!r}（YYYY-MM-DD HH:MM）")


def num(s: str) -> float | None:
    """空欄は None。数値でなければ ValueError。"""
    if s is None or s == "":
        return None
    return float(s.replace(",", "").replace("%", ""))


def fmt(v, digits: int = 0, suffix: str = "") -> str:
    if v is None:
        return NA
    if digits == 0:
        return f"{int(round(v)):,}{suffix}"
    return f"{v:,.{digits}f}{suffix}"


# ---------- 検証 ----------

def validate(data: Data) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warns: list[str] = []

    def check(cond: bool, msg: str, warn: bool = False):
        if not cond:
            (warns if warn else errors).append(msg)

    video_ids = set()
    for i, v in enumerate(data.videos, start=2):
        where = f"videos.csv {i}行目"
        vid = v.get("video_id", "")
        check(bool(vid), f"{where}: video_id が空")
        check(vid not in video_ids, f"{where}: video_id {vid} が重複")
        video_ids.add(vid)
        c = v.get("concept", "")
        check(c == "" or c in CONCEPTS, f"{where}: concept は A/B/C のいずれか（{c!r}）")
        check(c != "", f"{where}: {vid} のコンセプト分類が未記入", warn=True)
        for k in ("shot_date", "planned_date"):
            try:
                parse_date(v.get(k, ""))
            except ValueError:
                errors.append(f"{where}: {k} の形式が不正（YYYY-MM-DD）")
        try:
            num(v.get("duration_sec", ""))
        except ValueError:
            errors.append(f"{where}: duration_sec が数値でない")

    posts_by_id = {}
    for i, p in enumerate(data.posts, start=2):
        where = f"posts.csv {i}行目"
        pid = p.get("post_id", "")
        check(bool(pid), f"{where}: post_id が空")
        check(pid not in posts_by_id, f"{where}: post_id {pid} が重複")
        posts_by_id[pid] = p
        check(p.get("video_id") in video_ids, f"{where}: video_id {p.get('video_id')!r} が videos.csv にない")
        check(p.get("platform") in PLATFORMS, f"{where}: platform は instagram / tiktok（{p.get('platform')!r}）")
        check(p.get("status") in STATUSES, f"{where}: status は {'/'.join(STATUSES)}（{p.get('status')!r}）")
        try:
            parse_date(p.get("scheduled_date", ""))
            posted_at = parse_dt(p.get("posted_at", ""))
            if p.get("status") == "posted":
                check(posted_at is not None, f"{where}: 投稿済みなのに posted_at が空")
                check(bool(p.get("url")), f"{where}: {pid} の投稿URLが未記入", warn=True)
        except ValueError as e:
            errors.append(f"{where}: {e}")

    for i, m in enumerate(data.metrics, start=2):
        where = f"metrics.csv {i}行目"
        p = posts_by_id.get(m.get("post_id", ""))
        check(p is not None, f"{where}: post_id {m.get('post_id')!r} が posts.csv にない")
        check(m.get("snapshot") in SNAPSHOTS, f"{where}: snapshot は {'/'.join(SNAPSHOTS)}")
        check(bool(m.get("source")), f"{where}: source（取得元）が空")
        try:
            cap = parse_dt(m.get("captured_at", ""))
            check(cap is not None, f"{where}: captured_at（取得時刻）が空")
            if p and cap and p.get("posted_at"):
                elapsed = (cap - parse_dt(p["posted_at"])).total_seconds() / 3600
                need = {"24h": 20, "72h": 66, "7d": 160}.get(m.get("snapshot"))
                if need and elapsed < need:
                    warns.append(f"{where}: {m.get('snapshot')} なのに投稿から {elapsed:.0f} 時間で取得している")
        except ValueError as e:
            errors.append(f"{where}: {e}")
        for k in METRIC_FIELDS:
            try:
                val = num(m.get(k, ""))
                if val is not None:
                    check(val >= 0, f"{where}: {k} が負の値")
                    if k == "completion_rate":
                        check(val <= 100, f"{where}: completion_rate は 0〜100（%）")
            except ValueError:
                errors.append(f"{where}: {k} が数値でない（{m.get(k)!r}）")

    for i, f_ in enumerate(data.followers, start=2):
        where = f"followers.csv {i}行目"
        check(f_.get("platform") in PLATFORMS, f"{where}: platform が不正")
        try:
            parse_date(f_.get("date", ""))
            num(f_.get("followers", ""))
        except ValueError:
            errors.append(f"{where}: date または followers の形式が不正")

    return errors, warns


# ---------- 集計 ----------

def video_map(data: Data) -> dict[str, dict]:
    return {v["video_id"]: v for v in data.videos}


def snapshot(data: Data, post_id: str, kind: str) -> dict | None:
    """指定スナップショットの最新行（同種が複数あれば captured_at が最も新しいもの）"""
    rows = [m for m in data.metrics if m.get("post_id") == post_id and m.get("snapshot") == kind]
    return max(rows, key=lambda m: parse_dt(m["captured_at"])) if rows else None


def latest_metrics(data: Data, post_id: str) -> dict | None:
    rows = [m for m in data.metrics if m.get("post_id") == post_id and m.get("captured_at")]
    return max(rows, key=lambda m: parse_dt(m["captured_at"])) if rows else None


def mval(row: dict | None, key: str) -> float | None:
    return num(row.get(key, "")) if row else None


def followers_on(data: Data, platform: str, d: date) -> float | None:
    rows = [r for r in data.followers if r.get("platform") == platform and parse_date(r.get("date", "")) == d]
    if not rows:
        return None
    return num(max(rows, key=lambda r: r.get("captured_at", ""))["followers"])


def posted(data: Data, platform: str | None = None, until: datetime | None = None) -> list[dict]:
    out = []
    for p in data.posts:
        if p.get("status") != "posted" or not p.get("posted_at"):
            continue
        if platform and p.get("platform") != platform:
            continue
        if until and parse_dt(p["posted_at"]) > until:
            continue
        out.append(p)
    return out


def avg(values: list[float | None]) -> tuple[float | None, int]:
    vals = [v for v in values if v is not None]
    return (mean(vals) if vals else None, len(vals))


def compute_daily(data: Data, cfg: dict, d: date) -> dict:
    start, end = parse_date(cfg["period"]["start"]), parse_date(cfg["period"]["end"])
    total_days = (end - start).days + 1
    elapsed = max(0, min(total_days, (d - start).days + 1))
    target = cfg["targets"]["posts_per_platform"]
    cutoff = datetime.combine(d, datetime.min.time()).replace(hour=REPORT_HOUR)
    end_of_day = datetime.combine(d, datetime.max.time())
    vmap = video_map(data)

    progress = {}
    for pf in PLATFORMS:
        today = [p for p in posted(data, pf) if parse_dt(p["posted_at"]).date() == d]
        cumulative = [p for p in posted(data, pf) if parse_dt(p["posted_at"]).date() <= d]
        expected = target * elapsed / total_days
        scheduled_today = [p for p in data.posts if p.get("platform") == pf and parse_date(p.get("scheduled_date", "")) == d]
        overdue = [p for p in data.posts if p.get("platform") == pf
                   and p.get("status") in ("planned", "ready")
                   and p.get("scheduled_date") and parse_date(p["scheduled_date"]) <= d]
        progress[pf] = {
            "today": len(today), "cumulative": len(cumulative), "target": target,
            "expected": expected, "diff": len(cumulative) - expected,
            "scheduled_today": len(scheduled_today),
            "scheduled_done": sum(1 for p in scheduled_today if p.get("status") == "posted"),
            "overdue": [p["post_id"] for p in overdue],
        }

    kpi = {}
    for pf in PLATFORMS:
        fol = {k: followers_on(data, pf, d - timedelta(days=off)) for k, off in (("today", 0), ("d1", 1), ("d7", 7))}
        recent = [p for p in posted(data, pf) if d - timedelta(days=6) <= parse_dt(p["posted_at"]).date() <= d]
        rows = []
        for p in sorted(recent, key=lambda p: p["posted_at"]):
            s24, s72, last = snapshot(data, p["post_id"], "24h"), snapshot(data, p["post_id"], "72h"), latest_metrics(data, p["post_id"])
            v = vmap.get(p["video_id"], {})
            rows.append({
                "post_id": p["post_id"], "title": v.get("title", ""), "concept": v.get("concept", ""),
                "posted_at": p["posted_at"], "v24": mval(s24, "views"), "v72": mval(s72, "views"),
                "likes": mval(last, "likes"), "saves": mval(last, "saves"), "shares": mval(last, "shares"),
                "completion": mval(last, "completion_rate"),
                "last_source": last.get("source") if last else None,
                "last_captured": last.get("captured_at") if last else None,
            })
        yday = [p for p in posted(data, pf) if parse_dt(p["posted_at"]).date() == d - timedelta(days=1)]
        prior = [p for p in posted(data, pf) if d - timedelta(days=8) <= parse_dt(p["posted_at"]).date() <= d - timedelta(days=2)]
        y_avg = avg([mval(snapshot(data, p["post_id"], "24h"), "views") for p in yday])
        p_avg = avg([mval(snapshot(data, p["post_id"], "24h"), "views") for p in prior])
        all_views = [mval(m, "views") for m in data.metrics
                     if any(p["post_id"] == m["post_id"] and p["platform"] == pf for p in data.posts)]
        max_v = max([v for v in all_views if v is not None], default=None)
        kpi[pf] = {"followers": fol, "rows": rows, "yday_avg24": y_avg, "prior_avg24": p_avg, "max_views": max_v}

    concepts = {}
    for c in CONCEPTS:
        info = cfg["concepts"][c]
        vids = {v["video_id"] for v in data.videos if v.get("concept") == c}
        made = {p["video_id"] for p in posted(data, until=end_of_day) if p["video_id"] in vids}
        per_pf = {}
        for pf in PLATFORMS:
            ps = [p for p in posted(data, pf, until=end_of_day) if p["video_id"] in vids]
            a24, n24 = avg([mval(snapshot(data, p["post_id"], "24h"), "views") for p in ps])
            comp, ncomp = avg([mval(snapshot(data, p["post_id"], "24h"), "completion_rate") for p in ps])
            per_pf[pf] = {"posted": len(ps), "avg24": a24, "n24": n24, "comp24": comp, "ncomp": ncomp}
        concepts[c] = {"name": info["name"], "planned": info["planned"], "posted_videos": len(made), "per_pf": per_pf}

    missing = []
    for pf in PLATFORMS:
        if followers_on(data, pf, d) is None:
            missing.append(f"{PLATFORM_LABEL[pf]} の本日のフォロワー数（followers.csv）")
    for p in posted(data, until=cutoff):
        hours = (cutoff - parse_dt(p["posted_at"])).total_seconds() / 3600
        title = vmap.get(p["video_id"], {}).get("title", p["video_id"])
        label = f"{p['post_id']}（{PLATFORM_LABEL.get(p['platform'], p['platform'])}「{title}」）"
        if hours >= 24 and snapshot(data, p["post_id"], "24h") is None:
            missing.append(f"{label} の24h指標（metrics.csv, snapshot=24h）")
        if hours >= 72 and snapshot(data, p["post_id"], "72h") is None:
            missing.append(f"{label} の72h指標（metrics.csv, snapshot=72h）")
        if not p.get("url"):
            missing.append(f"{label} の投稿URL（posts.csv）")
    for v in data.videos:
        if not v.get("concept"):
            missing.append(f"{v['video_id']} のコンセプト分類（videos.csv）")

    return {"date": d, "elapsed": elapsed, "total_days": total_days, "progress": progress,
            "kpi": kpi, "concepts": concepts, "missing": missing, "cfg": cfg}


# ---------- 出力 ----------

def ref_tag(n: int) -> str:
    return "" if n >= MIN_SAMPLE else f"（n={n}・参考値）" if n else ""


def concept_table(facts: dict) -> list[str]:
    out = ["| コンセプト | 予定 | 投稿済み動画 | IG 24h再生平均 | TikTok 24h再生平均 | IG 24h完視聴率 | TikTok 24h完視聴率 |",
           "|---|---|---|---|---|---|---|"]
    for c, info in facts["concepts"].items():
        ig, tt = info["per_pf"]["instagram"], info["per_pf"]["tiktok"]
        out.append(f"| {c}：{info['name']} | {info['planned']} | {info['posted_videos']} "
                   f"| {fmt(ig['avg24'])}{ref_tag(ig['n24'])} | {fmt(tt['avg24'])}{ref_tag(tt['n24'])} "
                   f"| {fmt(ig['comp24'], 1, '%')}{ref_tag(ig['ncomp'])} | {fmt(tt['comp24'], 1, '%')}{ref_tag(tt['ncomp'])} |")
    return out


def render_daily(facts: dict, errors: list[str], warns: list[str]) -> str:
    d = facts["date"]
    L = [f"# LOUIS DAILY REPORT — {d.isoformat()}（{facts['elapsed']}/{facts['total_days']}日目）", "",
         "> ①②と「未取得データ」「コンセプト別集計」は `scripts/louis.py` による確定値。③〜⑦はAI社員が記入。", ""]

    L += ["## ① 本日の進捗", "", "| 媒体 | 本日投稿 | 累計 | 目標 | 本日時点の目安 | 差分 | 本日予定の達成 |", "|---|---|---|---|---|---|---|"]
    for pf, pr in facts["progress"].items():
        sched = f"{pr['scheduled_done']}/{pr['scheduled_today']}" if pr["scheduled_today"] else "予定なし"
        L.append(f"| {PLATFORM_LABEL[pf]} | {pr['today']} | {pr['cumulative']} | {pr['target']} "
                 f"| {pr['expected']:.1f} | {pr['diff']:+.1f} | {sched} |")
    overdue = [pid for pr in facts["progress"].values() for pid in pr["overdue"]]
    L += ["", f"- 投稿漏れ・遅れ：{'、'.join(overdue) if overdue else 'なし'}", ""]

    L += ["## ② KPI", ""]
    for pf, k in facts["kpi"].items():
        f_ = k["followers"]
        def delta(a, b):
            return f"{int(a - b):+,}" if a is not None and b is not None else NA
        L += [f"### {PLATFORM_LABEL[pf]}", "",
              f"- フォロワー：{fmt(f_['today'])}（前日比 {delta(f_['today'], f_['d1'])} ／ 7日前比 {delta(f_['today'], f_['d7'])}）",
              f"- 単一動画の最高再生数（全期間）：{fmt(k['max_views'])}",
              f"- 昨日投稿分の24h再生平均：{fmt(k['yday_avg24'][0])}{ref_tag(k['yday_avg24'][1])} "
              f"／ その前7日間の投稿の24h再生平均：{fmt(k['prior_avg24'][0])}{ref_tag(k['prior_avg24'][1])}", ""]
        if k["rows"]:
            L += ["| 投稿 | 動画 | 分類 | 投稿日時 | 24h再生 | 72h再生 | いいね | 保存 | シェア | 完視聴率 | 最新値の取得元・時刻 |",
                  "|---|---|---|---|---|---|---|---|---|---|---|"]
            for r in k["rows"]:
                src = f"{r['last_source']} {r['last_captured']}" if r["last_source"] else NA
                L.append(f"| {r['post_id']} | {r['title']} | {r['concept'] or NA} | {r['posted_at']} | {fmt(r['v24'])} | {fmt(r['v72'])} "
                         f"| {fmt(r['likes'])} | {fmt(r['saves'])} | {fmt(r['shares'])} | {fmt(r['completion'], 1, '%')} | {src} |")
        else:
            L.append("- 直近7日の投稿なし")
        L.append("")

    L += ["### コンセプト別集計（期間累計・24h値）", ""] + concept_table(facts) + [""]

    L += ["## ③ GOOD", "", "（AI社員が記入：analyst）", "",
          "## ④ MORE", "", "（AI社員が記入：analyst）", "",
          "## ⑤ 今日の学び", "", "（AI社員が記入：analyst ― 【観測】【仮説】【解釈】を区別）", "",
          "## ⑥ 明日の企画3案", "", "（AI社員が記入：planner ＋ edit-director）", "",
          "## ⑦ 明日の最重要アクション（最大3つ）", "", "（AI社員が記入：pm）", ""]

    L += ["## 未取得データと必要な入力作業", ""]
    L += [f"- [ ] {m}" for m in facts["missing"]] or ["- なし"]
    L += ["", "## データ品質", ""]
    if not errors and not warns:
        L.append("- 問題なし")
    L += [f"- ❌ {e}" for e in errors] + [f"- ⚠️ {w}" for w in warns]
    L.append("")
    return "\n".join(L)


def render_review(facts: dict, data: Data, root: Path) -> str:
    d = facts["date"]
    direction = (root / "inputs" / "direction.md").read_text(encoding="utf-8") if (root / "inputs" / "direction.md").exists() else "（なし）"
    L = [f"# LOUIS PROJECT 戦略レビュー用資料（{d.isoformat()}時点）", "",
         "ChatGPTへ：以下は猫のルイス（Instagram/TikTok @louis_rd_0723）のショート動画運用データです。"
         "数値は記録された実測値のみで、「未取得」は欠損です（0ではありません）。",
         "", "## プロジェクト概要",
         "- コンセプト：「顔は天使。中身は悪ガキ。」／キャッチコピー「可愛すぎて、今日も無罪。」",
         f"- 期間：{facts['cfg']['period']['start']}〜{facts['cfg']['period']['end']}（{facts['elapsed']}/{facts['total_days']}日目）",
         f"- 目標：各媒体{facts['cfg']['targets']['posts_per_platform']}投稿、フォロワー IG {facts['cfg']['targets']['followers']['instagram']} / TikTok {facts['cfg']['targets']['followers']['tiktok']}",
         "", "## 進捗"]
    for pf, pr in facts["progress"].items():
        fol = facts["kpi"][pf]["followers"]["today"]
        L.append(f"- {PLATFORM_LABEL[pf]}：累計{pr['cumulative']}本（目安{pr['expected']:.1f}本）、フォロワー {fmt(fol)}、最高再生 {fmt(facts['kpi'][pf]['max_views'])}")
    L += ["", "## コンセプト別"] + concept_table(facts)
    L += ["", "## 投稿一覧（24h/72h）", "| 投稿 | 媒体 | 動画 | 分類 | 投稿日時 | 24h再生 | 72h再生 | 24h完視聴率 |", "|---|---|---|---|---|---|---|---|"]
    vmap = video_map(data)
    for p in sorted(posted(data), key=lambda p: p["posted_at"]):
        v = vmap.get(p["video_id"], {})
        s24, s72 = snapshot(data, p["post_id"], "24h"), snapshot(data, p["post_id"], "72h")
        L.append(f"| {p['post_id']} | {PLATFORM_LABEL[p['platform']]} | {v.get('title','')} | {v.get('concept') or NA} | {p['posted_at']} "
                 f"| {fmt(mval(s24,'views'))} | {fmt(mval(s72,'views'))} | {fmt(mval(s24,'completion_rate'),1,'%')} |")
    if data.changes:
        L += ["", "## 企画の変更履歴"] + [f"- {c['changed_at']} [{c['concept']}] {c['before']} → {c['after']}（{c['reason']}）" for c in data.changes]
    L += ["", "## 現在の方針", "", direction.strip(), "",
          "## 相談したいこと",
          "1. 来週注力すべき改善テーマを3つ（根拠付き。サンプルが少ない点を考慮して）",
          "2. コンセプト配分（A12/B9/C9）を変えるべきか",
          "3. 冒頭2秒のフックで試すべきパターン",
          "", "回答の最後に「次週の方針」を箇条書きでまとめてください（そのまま inputs/direction.md に貼ります）。", ""]
    return "\n".join(L)


# ---------- Google Sheets 取り込み ----------

SHEET_TABS = {"videos": "videos.csv", "posts": "posts.csv", "metrics": "metrics.csv",
              "followers": "followers.csv", "concept_changes": "concept_changes.csv"}


def import_sheet(root: Path, json_path: Path) -> int:
    """get_values の values（2次元配列）をタブごとに受け取り、CSVに書き出す。
    ヘッダー行は既存CSVと一致している必要がある（列の入れ替え事故を防ぐ）。
    空行は捨て、行末の欠けたセルは空欄で補う。"""
    import json
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    problems = []
    staged = {}
    for tab, fname in SHEET_TABS.items():
        if tab not in payload:
            problems.append(f"タブ {tab} のデータがありません")
            continue
        rows = payload[tab] or []
        target = root / "data" / fname
        with target.open(encoding="utf-8-sig", newline="") as f:
            expected = next(csv.reader(f))
        header = [h.strip() for h in rows[0]] if rows else []
        if header[:len(expected)] != expected:
            problems.append(f"タブ {tab} の1行目（見出し）が想定と違います：{header}")
            continue
        body = []
        for r in rows[1:]:
            cells = [("" if c is None else str(c)).strip() for c in r][:len(expected)]
            if not any(cells):
                continue
            body.append(cells + [""] * (len(expected) - len(cells)))
        staged[target] = [expected] + body
    if problems:
        for p in problems:
            print(f"ERROR: {p}", file=sys.stderr)
        print("取り込みを中止しました（CSVは変更していません）", file=sys.stderr)
        return 1
    for target, rows in staged.items():
        with target.open("w", encoding="utf-8", newline="") as f:
            csv.writer(f).writerows(rows)
        print(f"{target.relative_to(root)}: {len(rows) - 1} 行")
    return 0


# ---------- CLI ----------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="LOUIS PROJECT 集計ツール")
    ap.add_argument("--root", default=str(Path(__file__).resolve().parent.parent))
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("validate")
    for name in ("daily", "review"):
        sp = sub.add_parser(name)
        sp.add_argument("date", nargs="?", help="YYYY-MM-DD（省略時は今日・JST）")
        sp.add_argument("--force", action="store_true", help="既存ファイルを上書き")
        sp.add_argument("--stdout", action="store_true", help="ファイルに保存せず表示")
    sp = sub.add_parser("import-sheet", help="Google Sheets の get_values 結果(JSON)を data/*.csv に書き出す")
    sp.add_argument("json_path", help='{"videos": [[...],...], "posts": ..., ...} 形式のJSON')
    a = ap.parse_args(argv)
    root = Path(a.root)

    if a.cmd == "import-sheet":
        return import_sheet(root, Path(a.json_path))

    data = load_data(root)
    errors, warns = validate(data)

    if a.cmd == "validate":
        for e in errors:
            print(f"ERROR: {e}")
        for w in warns:
            print(f"WARN:  {w}")
        print(f"検証完了：エラー {len(errors)} 件 / 警告 {len(warns)} 件")
        return 1 if errors else 0

    if errors:
        print("データにエラーがあるため集計できません。先に `validate` の結果を修正してください：", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    from zoneinfo import ZoneInfo
    d = parse_date(a.date) if a.date else datetime.now(ZoneInfo("Asia/Tokyo")).date()
    facts = compute_daily(data, load_config(root), d)
    if a.cmd == "daily":
        text, out = render_daily(facts, errors, warns), root / "reports" / "daily" / f"{d.isoformat()}.md"
    else:
        text, out = render_review(facts, data, root), root / "exports" / f"chatgpt_review_{d.isoformat()}.md"

    if a.stdout:
        print(text)
        return 0
    if out.exists() and not a.force:
        print(f"{out.relative_to(root)} は既に存在します（上書きは --force）", file=sys.stderr)
        return 2
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"作成しました：{out.relative_to(root)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
