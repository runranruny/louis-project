#!/usr/bin/env python3
"""11/27に受け取った素材5本（V005〜V009）を、粗編集・テロップなし版・編集素材・カット表で書き出す。
使い方: python3 tools/render_new5.py <素材フォルダ> <出力フォルダ> [V005 ...]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from louis_edit import Editor, text, catch  # noqa: E402


def Z(z0, z1, dur, px=0.5, py=0.5):
    """(px, py)＝画面内の注目点（0〜1）を中心にズームする"""
    def c(p, z):
        return 0.5 if z <= 1 else min(max((p * z - 0.5) / (z - 1), 0), 1)
    return Editor.zoom(z0, z1, dur, c(px, max(z0, z1)), c(py, max(z0, z1)))


TOP = "h*0.14"
DARK = "eq=brightness=0.07:gamma=1.5"


def v005(e):  # 天使のボクシング｜A（IMG_2704）
    e.still(12.0, 1.3, [Z(1.0, 1.15, 1.3, 0.5, 0.45), text("天使です", 0.1, 9, 120)])
    e.seg(1.8, 3.4, 1.0, [text("…と思ったら", size=100)])
    e.seg(3.6, 4.8, 0.6, [text("シュッ", size=140)])
    e.seg(7.6, 9.0, 0.6, [text("シュシュッ", size=140)])
    e.seg(13.0, 15.6, 1.0, [text("本気です", size=120)])
    e.seg(19.0, 20.6, 0.7, [text("ワン・ツー！", size=120)])
    e.seg(20.6, 21.6, 1.0)
    e.still(21.6, 1.6, [Z(1.0, 1.2, 1.6, 0.5, 0.42), text("…何か？", 0.2, 9, 120), catch(0.4)])


def v006(e):  # ぬいぐるみ襲撃事件｜B（IMG_2510）
    e.color(1.6, "black", [text("【事件】", 0, 9, 130, "h*0.36"), text("ぬいぐるみが襲われた", 0.3, 9, 84, "h*0.50")])
    e.seg(3.0, 9.0, 2.0, [text("証拠映像", size=64, y=TOP), text("キック連打", size=110)])
    e.seg(21.5, 25.0, 1.0, [text("証拠映像", size=64, y=TOP), text("噛みつき", size=120)])
    e.still(24.0, 1.0, [Z(1.0, 1.15, 1.0, 0.4, 0.4), text("容疑者", size=130)])
    e.seg(30.0, 36.0, 3.0, [text("取り調べ中…", size=100)])
    e.seg(38.4, 40.6, 1.0, [text("…仲直り？", size=110)])
    e.still(40.6, 1.5, [text("かわいいので無罪", size=110), catch(0.2)])


def v007(e):  # 深夜0時の運動会｜C（IMG_2777）
    e.seg(0.0, 3.0, 1.0, [Z(1.0, 2.0, 3.0, 0.42, 0.45), text("深夜0時。", 0, 9, 110, "h*0.60"),
                          text("寝ようとしたら", 0.8, 9, 84, "h*0.60+130")])
    e.seg(13.4, 15.4, 1.0, [Z(2.0, 2.0, 1, 0.42, 0.45), text("…視線を感じる", size=96)])
    e.seg(15.4, 17.4, 0.6, [text("来たーー！！", size=130)])
    e.still(20.0, 0.7, [text("近い", size=150)])
    e.seg(20.4, 22.0, 1.5, [text("そして逃走", size=110)])
    e.seg(30.3, 31.6, 0.7, [text("2回目", size=130)])
    e.seg(33.0, 40.0, 3.0, [Z(2.0, 2.0, 1, 0.42, 0.52), text("箱に潜伏", size=120)])
    e.seg(41.4, 43.0, 1.0, [text("また来た", size=120)])
    e.still(15.6, 1.8, [Z(1.0, 1.15, 1.8, 0.5, 0.5), text("下僕、今夜も", size=100),
                        text("寝られません", 0.3, 9, 100, "h*0.60+130"), catch(0.5)])


def v008(e):  # 布団の奥の視線｜B（IMG_2749）
    e.color(1.6, "black", [text("【事件】", 0, 9, 130, "h*0.36"), text("布団の奥から、視線", 0.3, 9, 84, "h*0.50")])
    e.seg(47.0, 52.0, 2.0, [DARK, text("…何かいる", size=110)])
    e.seg(84.0, 85.6, 1.0, [DARK, Z(1.4, 1.4, 1, 0.6, 0.6), text("…いた", 0.6, 9, 130)])
    e.seg(85.6, 88.0, 1.0, [DARK, Z(2.0, 2.0, 1, 0.6, 0.6), text("…いた", size=130)])
    e.seg(88.0, 92.0, 1.0, [DARK, Z(2.6, 2.6, 1, 0.6, 0.6), text("じーーーっ", size=120)])
    e.still(92.0, 1.8, [DARK, Z(2.6, 2.6, 1, 0.6, 0.6), text("容疑者、", size=100),
                        text("ずっと見てる", 0.3, 9, 100, "h*0.60+130"), catch(0.5)])


def v009(e):  # 肉球エステ｜C（IMG_2745）
    e.seg(0.0, 2.2, 1.0, [text("王子、お休み中", size=100)])
    e.seg(2.2, 6.0, 1.5, [text("下僕による", size=96), text("肉球マッサージ", 0.3, 9, 110, "h*0.60+130")])
    e.seg(7.0, 14.0, 2.5, [text("お腹まで全開", size=110)])
    e.seg(15.0, 17.0, 1.0, [text("…起きる気配ゼロ", size=96)])
    e.still(17.6, 1.6, [Z(1.0, 1.15, 1.6, 0.5, 0.4), text("ご満悦", size=140), catch(0.3)])


VIDEOS = {
    "V005": ("天使のボクシング", "IMG_2704.mov", None, v005),
    "V006": ("ぬいぐるみ襲撃事件", "IMG_2510.mov", None, v006),
    "V007": ("深夜0時の運動会", "IMG_2777.mov", None, v007),
    "V008": ("布団の奥の視線", "IMG_2749.mov", None, v008),
    "V009": ("肉球エステ", "IMG_2745.mov", None, v009),
}

if __name__ == "__main__":
    src_dir, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
    targets = sys.argv[3:] or list(VIDEOS)
    for vid in targets:
        title, fname, lcx, spec = VIDEOS[vid]
        src = str(next(src_dir.glob(f"*{fname}")))
        base = out_dir / f"{vid}_{title}"
        base.mkdir(parents=True, exist_ok=True)
        for mode, out in (("full", base / f"{vid}_{title}_テロップあり.mp4"),
                          ("notext", base / f"{vid}_{title}_テロップなし.mp4"),
                          ("parts", base / "編集素材")):
            if mode == "parts":
                out.mkdir(exist_ok=True)
            e = Editor(src, out, landscape_cx=lcx, mode=mode)
            spec(e)
            e.render()
        (base / f"{vid}_{title}_カット表.md").write_text(e.telop_sheet(f"{vid} {title}（元素材 {fname}）"), encoding="utf-8")
        print("done", base)
