#!/usr/bin/env python3
"""③ ルイス失踪事件 / ① 王子は寝たまま遊びます / ④ おかえり の粗編集
使い方: python3 tools/render_rest.py <素材フォルダ> <出力フォルダ>
素材フォルダに IMG_2258.mov / IMG_2395.mov / IMG_2116.mov（前に任意の接頭辞があってもよい）を置く。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from louis_edit import Editor, text, catch  # noqa: E402

src_dir, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
out_dir.mkdir(parents=True, exist_ok=True)


def find(name):
    return str(next(src_dir.glob(f"*{name}")))


Z = Editor.zoom

# ③ ルイス失踪事件｜B：事件簿（約11秒）
e = Editor(find("IMG_2258.mov"), out_dir / "louis_03_missing_draft.mp4")
e.color(1.6, "black", [text("【事件】", 0, 9, 130, "h*0.36"), text("ルイスが家から消えた", 0.3, 9, 84, "h*0.50")])
e.seg(0.0, 4.5, 1.0, [Z(1.0, 1.6, 4.5, 0.95, 0.34), text("…いた", 0.5, 2.0, 110),
                      text("ようやく見つけたか", 2.1, 9, 92), text("（容疑者談）", 2.6, 9, 64, "h*0.60+120")])
e.seg(5.3, 10.5, 2.5, [text("容疑者、逃走", 0, 9, 100)])
e.seg(11.0, 12.8, 1.0, [Z(1.0, 1.15, 1.8, 0.5, 0.3), text("反省の色なし", 0, 9, 100)])
e.still(12.5, 1.2, [Z(1.15, 1.15, 1, 0.5, 0.3), text("かわいいので無罪", 0, 9, 110), catch(0.2)])
print(e.render())

# ① 王子は寝たまま遊びます｜C：王子と下僕（約12.5秒）
e = Editor(find("IMG_2395.mov"), out_dir / "louis_01_lazy_prince_draft.mp4")
e.seg(0.0, 2.0, 1.0, [text("下僕、全力で振ってます", 0, 9, 88)])
e.seg(2.6, 5.4, 1.5, [text("王子、寝たまま応戦", 0, 9, 92)])
e.seg(6.6, 9.4, 1.5, [text("…見てるだけ", 0, 9, 100)])
e.seg(10.0, 22.0, 4.0, [text("起き上がる気配なし", 0, 9, 92)])
e.seg(25.5, 28.5, 1.0, [Z(1.0, 1.2, 3.0, 0.45, 0.55), text("本日の運動量：", 0.2, 9, 92), text("前足のみ", 1.2, 9, 120, "h*0.60+130")])
e.still(28.4, 0.8, [Z(1.2, 1.2, 1, 0.45, 0.55), text("本日の運動量：", 0, 9, 92), text("前足のみ", 0, 9, 120, "h*0.60+130"), catch()])
print(e.render())

# ④ おかえり（起きるとは言ってない）｜A：ギャップ（約11秒）※横動画を9:16に切り抜き
e = Editor(find("IMG_2116.mov"), out_dir / "louis_04_okaeri_draft.mp4", landscape_cx=0.65)
e.seg(3.3, 4.7, 1.0, [text("帰宅したら", 0, 9, 96), text("出迎えてくれた", 0.4, 9, 96, "h*0.60+120")], cx=0.78)
e.still(4.0, 0.6, [text("…寝たまま", 0, 9, 110)], cx=0.78)
e.seg(13.0, 18.0, 1.6, [text("指だけは全力でつかむ", 0, 9, 88)], cx=0.62)
e.seg(21.0, 25.0, 1.6, [text("（起きるとは言ってない）", 0, 9, 80)], cx=0.68)
e.seg(32.5, 35.5, 1.0, [text("ガジガジ…", 0.3, 9, 100)], cx=0.55)
e.still(3.6, 1.4, [text("おかえりの顔だけは", 0, 9, 92), text("100点", 0.3, 9, 130, "h*0.60+120"), catch(0.3)], cx=0.78)
print(e.render())
