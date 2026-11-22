"""python3 -m unittest discover -s tests で実行"""
import shutil
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import louis  # noqa: E402

SAMPLE = ROOT / "tests" / "fixtures" / "sample"


class SampleTest(unittest.TestCase):
    def setUp(self):
        self.data = louis.load_data(SAMPLE)
        self.cfg = louis.load_config(SAMPLE)
        self.facts = louis.compute_daily(self.data, self.cfg, date(2026, 11, 26))

    def test_validate_sample(self):
        errors, warns = louis.validate(self.data)
        self.assertEqual(errors, [])
        self.assertTrue(any("V003" in w and "コンセプト" in w for w in warns))
        self.assertTrue(any("P002-TT" in w and "URL" in w for w in warns))

    def test_progress_and_overdue(self):
        ig, tt = self.facts["progress"]["instagram"], self.facts["progress"]["tiktok"]
        self.assertEqual((ig["cumulative"], tt["cumulative"]), (2, 3))
        self.assertAlmostEqual(ig["expected"], 30 * 4 / 39)
        self.assertEqual(ig["overdue"], ["P003-IG"])
        self.assertEqual(tt["overdue"], [])

    def test_blank_is_not_zero(self):
        rows = {r["post_id"]: r for r in self.facts["kpi"]["instagram"]["rows"]}
        self.assertIsNone(rows["P002-IG"]["likes"])          # 空欄 → None
        tt = {r["post_id"]: r for r in self.facts["kpi"]["tiktok"]["rows"]}
        self.assertEqual(tt["P002-TT"]["v24"], 0)            # 本当の0 → 0
        self.assertEqual(louis.fmt(None), "未取得")

    def test_24h_and_72h_kept_separate(self):
        rows = {r["post_id"]: r for r in self.facts["kpi"]["instagram"]["rows"]}
        self.assertEqual(rows["P001-IG"]["v24"], 820)
        self.assertEqual(rows["P001-IG"]["v72"], 1300)
        self.assertIsNone(rows["P002-IG"]["v72"])

    def test_followers_comparison(self):
        f = self.facts["kpi"]["instagram"]["followers"]
        self.assertEqual((f["today"], f["d1"], f["d7"]), (99, 95, None))

    def test_missing_data_list(self):
        m = "\n".join(self.facts["missing"])
        self.assertIn("P003-TT", m)            # 投稿26h経過・24h未入力
        self.assertIn("P002-TT（TikTok「容疑者ルイス、現行犯逮捕」） の投稿URL", m)
        self.assertNotIn("P002-IG", m)         # 51h経過・72hはまだ不要、24hは入力済み
        self.assertIn("P001-TT（TikTok「この顔に騙されてはいけません」） の72h", m)  # 75h経過
        self.assertNotIn("P001-IG", m)         # 24h・72hとも入力済み
        self.assertIn("V003 のコンセプト分類", m)

    def test_concept_summary_marks_small_samples(self):
        a = self.facts["concepts"]["A"]
        self.assertEqual(a["posted_videos"], 1)
        self.assertEqual(a["per_pf"]["instagram"]["avg24"], 820)
        self.assertIn("参考値", louis.ref_tag(a["per_pf"]["instagram"]["n24"]))

    def test_render_contains_all_sections(self):
        text = louis.render_daily(self.facts, [], [])
        for h in ("① 本日の進捗", "② KPI", "③ GOOD", "④ MORE", "⑤ 今日の学び", "⑥ 明日の企画3案", "⑦ 明日の最重要アクション", "未取得データ"):
            self.assertIn(h, text)


class EmptyDataTest(unittest.TestCase):
    """データ未入力でも日報が作れること"""

    def test_empty_project(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            shutil.copytree(ROOT / "config", tmp / "config")
            shutil.copytree(ROOT / "data", tmp / "data")
            data = louis.load_data(tmp)
            self.assertEqual(louis.validate(data)[0], [])
            facts = louis.compute_daily(data, louis.load_config(tmp), date(2026, 11, 23))
            text = louis.render_daily(facts, [], [])
            self.assertIn("直近7日の投稿なし", text)
            self.assertIn("本日のフォロワー数", text)
            self.assertEqual(louis.main(["--root", str(tmp), "daily", "2026-11-23"]), 0)
            self.assertEqual(louis.main(["--root", str(tmp), "daily", "2026-11-23"]), 2)  # 上書き防止
        finally:
            shutil.rmtree(tmp)

    def test_invalid_data_is_rejected(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            shutil.copytree(SAMPLE, tmp, dirs_exist_ok=True)
            with (tmp / "data" / "metrics.csv").open("a", encoding="utf-8") as f:
                f.write("P001-TT,72h,,manual_app,abc,,,150,,,,,,\n")
            errors, _ = louis.validate(louis.load_data(tmp))
            joined = "\n".join(errors)
            self.assertIn("captured_at", joined)
            self.assertIn("views が数値でない", joined)
            self.assertIn("completion_rate", joined)
            self.assertEqual(louis.main(["--root", str(tmp), "daily", "2026-11-26"]), 1)
        finally:
            shutil.rmtree(tmp)


if __name__ == "__main__":
    unittest.main()
