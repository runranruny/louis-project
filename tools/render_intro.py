#!/usr/bin/env python3
"""V000 自己紹介（TikTok 1投稿目）の粗編集
使い方: python3 tools/render_intro.py <素材フォルダ> <出力フォルダ>
素材: IMG_1946.mov（廊下・階段を探検）/ IMG_1996.mov（抱っこでとろける）/ IMG_2006.jpeg（キャリーの上の写真）
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from louis_edit import Editor, text, catch  # noqa: E402

Z = Editor.zoom
src_dir, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
find = lambda n: str(next(src_dir.glob(f"*{n}")))
V1946, V1996, PHOTO = find("IMG_1946.mov"), find("IMG_1996.mov"), find("image.jpg")

base = out_dir / "V000_自己紹介"
base.mkdir(parents=True, exist_ok=True)
for mode, out in (("full", base / "V000_自己紹介_テロップあり.mp4"), ("notext", base / "V000_自己紹介_テロップなし.mp4")):
    # 抱っこ動画は上部に人が写るため、1.25倍に拡大して上を切る
    e = Editor(V1996, out, mode=mode)
    e.seg(0.0, 2.4, 1.0, [Z(1.25, 1.3, 2.4, 0.5, 0.75), text("「この子が呼んでいる！」", 0, 9, 84, "h*0.62"),
                          text("新婚旅行中の妻のひと言から", 0.5, 9, 58, "h*0.62+110"),
                          text("すべては始まった", 0.9, 9, 58, "h*0.62+185")])
    e.src = V1946
    e.seg(0.0, 3.7, 2.0, [text("はじめまして、", 0, 9, 96), text("ルイスです", 0.4, 9, 110, "h*0.60+125")])
    e.seg(3.7, 12.0, 2.8, [text("好奇心は", 0, 9, 96), text("この頃から全開", 0.3, 9, 96, "h*0.60+120")])
    e.seg(22.0, 29.0, 2.0, [text("なでられるのは好き", 0, 9, 92)])
    e.src = V1996
    e.seg(9.7, 16.7, 2.0, [Z(1.25, 1.25, 1, 0.5, 0.75), text("抱っこされると…", 0, 9, 92, "h*0.62"),
                           text("とける", 1.6, 9, 130, "h*0.62+120")])
    e.image(PHOTO, 4.0, ["eq=contrast=1.12:brightness=0.02:saturation=1.15", Z(1.25, 1.45, 4.0, 0.5, 0.30),
                         "drawbox=x=0:y=ih*0.66:w=iw:h=ih*0.34:color=black@0.45:t=fill",
                         text("ルイス／ラグドール♂", 0.1, 9, 76, "h*0.69"),
                         text("2026.7.23生まれ　10.18 お迎え", 0.3, 9, 52, "h*0.69+100"),
                         text("顔は天使。中身は悪ガキ。", 1.2, 9, 70, "h*0.69+180")])
    e.image(PHOTO, 2.2, ["eq=contrast=1.12:brightness=0.02:saturation=1.15", Z(1.45, 1.45, 1, 0.5, 0.30),
                         "drawbox=x=0:y=ih*0.66:w=iw:h=ih*0.34:color=black@0.45:t=fill",
                         text("これから毎日、", 0, 9, 80, "h*0.70"),
                         text("ルイスの日常をお届けします", 0.2, 9, 66, "h*0.70+105"),
                         catch(0.6)])
    print(e.render())
