#!/usr/bin/env python3
"""② 天使（ハンター）の粗編集を台本どおりに書き出す（音はアプリで付ける前提で無音）"""
import subprocess, sys
from pathlib import Path

SRC = sys.argv[1]
OUT = Path(sys.argv[2])
W, H, FPS = 1080, 1920, 30
TMP = OUT.parent / "tmp02"
TMP.mkdir(parents=True, exist_ok=True)
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"


def run(args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def esc(s):
    return s.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’").replace("%", "\\%")


def text(s, start, end, size=96, y="h*0.60"):
    return (f"drawtext=fontfile='{FONT}':text='{esc(s)}':fontsize={size}:fontcolor=white:"
            f"borderw=8:bordercolor=black:x=(w-text_w)/2:y={y}:enable='between(t,{start},{end})'")


def zoom(z0, z1, dur, ycenter=0.5):
    """dur秒かけて z0→z1 倍にズーム（ycenter=切り抜きの縦位置 0上〜1下）"""
    zexpr = f"({z0}+({z1}-{z0})*min(t/{dur},1))"
    return (f"scale=w='trunc({W}*{zexpr}/2)*2':h=-2:eval=frame,"
            f"crop={W}:{H}:x=(iw-{W})/2:y=(ih-{H})*{ycenter}")


BASE = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS}"


def clip(name, filters, src_args):
    out = TMP / f"{name}.mp4"
    run([*src_args, "-vf", ",".join(filters) + ",format=yuv420p", "-an",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-r", str(FPS), str(out)])
    return out


def seg(name, t0, t1, speed, extra=()):
    dur = (t1 - t0) / speed
    return clip(name, [BASE, f"setpts=(PTS-STARTPTS)/{speed}", *extra],
                ["-ss", str(t0), "-t", str(t1 - t0), "-i", SRC]) , dur


def still(name, at, dur, extra=()):
    png = TMP / f"{name}.png"
    run(["-ss", str(at), "-i", SRC, "-frames:v", "1", str(png)])
    return clip(name, [BASE, *extra], ["-loop", "1", "-t", str(dur), "-i", str(png)])


parts = []
# 0.0–1.2 冒頭フリーズ＋ズーム「天使…？」
parts.append(still("s00", 19.3, 1.2, [zoom(1.0, 1.1, 1.2, 0.30), text("天使…？", 0.1, 1.2, 120)]))
# 1.2–1.35 白フラッシュ
parts.append(clip("s01", [f"color=white:s={W}x{H}:r={FPS}"][0:0] or ["null"],
                  ["-f", "lavfi", "-t", "0.15", "-i", f"color=white:s={W}x{H}:r={FPS}"]))
# 1.35–1.8 巻き戻し風（モノクロ）「〜15秒前〜」
parts.append(still("s02", 19.3, 0.45, [zoom(1.1, 1.1, 0.45, 0.30), "hue=s=0", text("〜 15秒前 〜", 0, 0.45, 100, "h*0.45")]))
# 本編
parts.append(seg("s03", 1.3, 2.4, 1.2, [text("獲物を発見", 0, 9)])[0])
parts.append(seg("s04", 3.0, 3.7, 0.6, [text("やんのか？？", 0, 9, 110)])[0])
parts.append(seg("s05", 4.3, 7.0, 2.0, [text("確保ォ！！", 0, 9, 120)])[0])
parts.append(seg("s06", 7.0, 13.0, 3.0, [text("ネズミと死闘中", 0, 9)])[0])
parts.append(seg("s07", 14.0, 17.0, 2.5, [text("…こっちに来た", 0, 9)])[0])
# 間（無音・テロップなし）
parts.append(still("s08", 18.3, 0.6))
# オチ：0.5倍スロー＋ズーム
parts.append(seg("s09", 18.2, 19.6, 0.5, [zoom(1.0, 1.3, 2.8, 0.28),
                                          text("獲物、見せに来ました", 0.2, 9, 92),
                                          text("（褒めて）", 1.8, 9, 70, "h*0.60+120")])[0])
# 締め
parts.append(still("s10", 19.45, 0.8, [zoom(1.3, 1.3, 0.8, 0.28),
                                       text("獲物、見せに来ました", 0, 9, 92),
                                       text("（褒めて）", 0, 9, 70, "h*0.60+120"),
                                       text("可愛すぎて、今日も無罪。", 0, 9, 56, "h*0.86")]))

lst = TMP / "list.txt"
lst.write_text("".join(f"file '{p.resolve()}'\n" for p in parts))
# 無音トラックを付ける（アプリ側でBGM・効果音を足す前提）
run(["-f", "concat", "-safe", "0", "-i", str(lst), "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
     "-shortest", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
     "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(OUT)])
print("done", OUT)
