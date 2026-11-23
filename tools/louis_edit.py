#!/usr/bin/env python3
"""LOUIS PROJECT 粗編集ライブラリ（ffmpeg）。音は入れない（BGM・効果音はアプリで付ける）。

使い方は tools/render_*.py を参照。秒数はすべて元動画の位置。
"""
import subprocess
from pathlib import Path

W, H, FPS = 1080, 1920, 30
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
CATCH = "可愛すぎて、今日も無罪。"


def _run(args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def _esc(s):
    return s.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’").replace("%", "\\%")


def text(s, start=0, end=99, size=96, y="h*0.60"):
    return (f"drawtext=fontfile='{FONT}':text='{_esc(s)}':fontsize={size}:fontcolor=white:"
            f"borderw=8:bordercolor=black:x=(w-text_w)/2:y={y}:enable='between(t,{start},{end})'")


def catch(start=0):
    return text(CATCH, start, 99, 56, "h*0.86")


class Editor:
    def __init__(self, src, out, landscape_cx=None):
        """landscape_cx: 横動画のとき、9:16に切り抜く横位置の既定値（0=左〜1=右）"""
        self.src, self.out = src, Path(out)
        self.tmp = self.out.parent / f"tmp_{self.out.stem}"
        self.tmp.mkdir(parents=True, exist_ok=True)
        self.landscape_cx = landscape_cx
        self.parts, self.n = [], 0

    def _base(self, cx):
        if self.landscape_cx is not None:
            cx = self.landscape_cx if cx is None else cx
            return f"crop=trunc(ih*9/16/2)*2:ih:x=(iw-ow)*{cx}:y=0,scale={W}:{H}"
        return f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}"

    @staticmethod
    def zoom(z0, z1, dur, cx=0.5, cy=0.5):
        z = f"({z0}+({z1}-{z0})*min(t/{dur},1))"
        return (f"scale=w='trunc({W}*{z}/2)*2':h=-2:eval=frame,"
                f"crop={W}:{H}:x=(iw-{W})*{cx}:y=(ih-{H})*{cy}")

    def _clip(self, filters, src_args):
        self.n += 1
        out = self.tmp / f"p{self.n:02d}.mp4"
        _run([*src_args, "-vf", ",".join(filters) + f",fps={FPS},format=yuv420p", "-an",
              "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-r", str(FPS), str(out)])
        self.parts.append(out)

    def seg(self, t0, t1, speed=1.0, extra=(), cx=None):
        self._clip([self._base(cx), f"setpts=(PTS-STARTPTS)/{speed}", *extra],
                   ["-ss", str(t0), "-t", str(t1 - t0), "-i", self.src])

    def still(self, at, dur, extra=(), cx=None):
        png = self.tmp / f"still_{at}.png"
        _run(["-ss", str(at), "-i", self.src, "-frames:v", "1", str(png)])
        self._clip([self._base(cx), *extra], ["-loop", "1", "-t", str(dur), "-i", str(png)])

    def color(self, dur, color="black", extra=()):
        self._clip(["null", *extra], ["-f", "lavfi", "-t", str(dur), "-i", f"color={color}:s={W}x{H}:r={FPS}"])

    def render(self):
        lst = self.tmp / "list.txt"
        lst.write_text("".join(f"file '{p.resolve()}'\n" for p in self.parts))
        _run(["-f", "concat", "-safe", "0", "-i", str(lst), "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
              "-shortest", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
              "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(self.out)])
        return self.out
