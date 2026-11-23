#!/usr/bin/env python3
"""手持ち素材4本を、粗編集（テロップあり）・テロップなし版・編集素材（カット別）・カット表で書き出す。
使い方: python3 tools/render_all.py <素材フォルダ> <出力フォルダ> [V001 V002 ...]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from louis_edit import Editor, text, catch  # noqa: E402

Z = Editor.zoom


def v001(e):  # ② 天使（ハンター）｜A
    e.still(19.3, 1.2, [Z(1.0, 1.1, 1.2, 0.5, 0.30), text("天使…？", 0.1, 1.2, 120)])
    e.color(0.15, "white")
    e.still(19.3, 0.45, [Z(1.1, 1.1, 0.45, 0.5, 0.30), "hue=s=0", text("〜 15秒前 〜", 0, 0.45, 100, "h*0.45")])
    e.seg(1.3, 2.4, 1.2, [text("獲物を発見")])
    e.seg(3.0, 3.7, 0.6, [text("やんのか？？", size=110)])
    e.seg(4.3, 7.0, 2.0, [text("確保ォ！！", size=120)])
    e.seg(7.0, 13.0, 3.0, [text("ネズミと死闘中")])
    e.seg(14.0, 17.0, 2.5, [text("…こっちに来た")])
    e.still(18.3, 0.6)
    e.seg(18.2, 19.6, 0.5, [Z(1.0, 1.3, 2.8, 0.5, 0.28), text("獲物、見せに来ました", 0.2, 99, 92),
                            text("（褒めて）", 1.8, 99, 70, "h*0.60+120")])
    e.still(19.45, 0.8, [Z(1.3, 1.3, 0.8, 0.5, 0.28), text("獲物、見せに来ました", size=92),
                         text("（褒めて）", 0, 99, 70, "h*0.60+120"), catch()])


def v002(e):  # ③ ルイス失踪事件｜B
    e.color(1.6, "black", [text("【事件】", 0, 9, 130, "h*0.36"), text("ルイスが家から消えた", 0.3, 9, 84, "h*0.50")])
    e.seg(0.0, 4.5, 1.0, [Z(1.0, 1.6, 4.5, 0.95, 0.34), text("…いた", 0.5, 2.0, 110),
                          text("ようやく見つけたか", 2.1, 9, 92), text("（容疑者談）", 2.6, 9, 64, "h*0.60+120")])
    e.seg(5.3, 10.5, 2.5, [text("容疑者、逃走", size=100)])
    e.seg(11.0, 12.8, 1.0, [Z(1.0, 1.15, 1.8, 0.5, 0.3), text("反省の色なし", size=100)])
    e.still(12.5, 1.2, [Z(1.15, 1.15, 1, 0.5, 0.3), text("かわいいので無罪", size=110), catch(0.2)])


def v003(e):  # ① 王子は寝たまま遊びます｜C
    e.seg(0.0, 2.0, 1.0, [text("下僕、全力で振ってます", size=88)])
    e.seg(2.6, 5.4, 1.5, [text("王子、寝たまま応戦", size=92)])
    e.seg(6.6, 9.4, 1.5, [text("…見てるだけ", size=100)])
    e.seg(10.0, 22.0, 4.0, [text("起き上がる気配なし", size=92)])
    e.seg(25.5, 28.5, 1.0, [Z(1.0, 1.2, 3.0, 0.45, 0.55), text("本日の運動量：", 0.2, 9, 92),
                            text("前足のみ", 1.2, 9, 120, "h*0.60+130")])
    e.still(28.4, 0.8, [Z(1.2, 1.2, 1, 0.45, 0.55), text("本日の運動量：", size=92),
                        text("前足のみ", 0, 9, 120, "h*0.60+130"), catch()])


def v004(e):  # ④ おかえり（起きるとは言ってない）｜A（横動画を9:16に切り抜き）
    e.seg(3.3, 4.7, 1.0, [text("帰宅したら", size=96), text("出迎えてくれた", 0.4, 9, 96, "h*0.60+120")], cx=0.78)
    e.still(4.0, 0.6, [text("…寝たまま", size=110)], cx=0.78)
    e.seg(13.0, 18.0, 1.6, [text("指だけは全力でつかむ", size=88)], cx=0.62)
    e.seg(21.0, 25.0, 1.6, [text("（起きるとは言ってない）", size=80)], cx=0.68)
    e.seg(32.5, 35.5, 1.0, [text("ガジガジ…", 0.3, 9, 100)], cx=0.55)
    e.still(3.6, 1.4, [text("おかえりの顔だけは", size=92), text("100点", 0.3, 9, 130, "h*0.60+120"), catch(0.3)], cx=0.78)


VIDEOS = {
    "V001": ("天使ハンター", "IMG_2314.mov", None, v001),
    "V002": ("ルイス失踪事件", "IMG_2258.mov", None, v002),
    "V003": ("王子は寝たまま遊びます", "IMG_2395.mov", None, v003),
    "V004": ("おかえり", "IMG_2116.mov", 0.65, v004),
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
