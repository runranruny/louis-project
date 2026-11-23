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
    """mode:
      full   … テロップ・速度・ズームすべて入りの粗編集
      notext … テロップだけ抜いた版（CapCutで自分の文字を入れる用）
      parts  … 編集素材：各カットを等倍・テロップなし・ズームなしで個別に書き出し（静止画はPNG）
    """

    def __init__(self, src, out, landscape_cx=None, mode="full"):
        """landscape_cx: 横動画のとき、9:16に切り抜く横位置の既定値（0=左〜1=右）"""
        self.src, self.out, self.mode = src, Path(out), mode
        self.tmp = self.out.parent / f"tmp_{self.out.stem}"
        self.tmp.mkdir(parents=True, exist_ok=True)
        self.landscape_cx = landscape_cx
        self.parts, self.n = [], 0
        self.log = []  # (番号, 種類, 元の秒, 速度, 完成での長さ, テロップ一覧)
        self.t = 0.0

    def _filters(self, extra):
        if self.mode == "full":
            return list(extra)
        return [f for f in extra if not f.startswith("drawtext")]

    @staticmethod
    def _texts(extra):
        import re
        out = []
        for f in extra:
            m = re.search(r"text='(.*?)':fontsize", f)
            if f.startswith("drawtext") and m:
                out.append(m.group(1).replace("\\:", ":").replace("\\\\", "\\"))
        return out

    def _record(self, kind, src_range, speed, dur, extra):
        self.log.append((len(self.log) + 1, kind, src_range, speed, round(self.t, 2), round(self.t + dur, 2), self._texts(extra)))
        self.t += dur

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
        self._record("動画", f"{t0}〜{t1}秒", speed, (t1 - t0) / speed, extra)
        if self.mode == "parts":
            out = self.out / f"{len(self.log):02d}_動画_{t0}-{t1}秒_推奨{speed}倍速.mp4"
            _run(["-ss", str(t0), "-t", str(t1 - t0), "-i", self.src, "-vf", f"{self._base(cx)},fps={FPS},format=yuv420p",
                  "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", str(out)])
            return
        self._clip([self._base(cx), f"setpts=(PTS-STARTPTS)/{speed}", *self._filters(extra)],
                   ["-ss", str(t0), "-t", str(t1 - t0), "-i", self.src])

    def still(self, at, dur, extra=(), cx=None):
        self._record("静止画", f"{at}秒のコマ", 1.0, dur, extra)
        png = self.tmp / f"still_{at}.png"
        _run(["-ss", str(at), "-i", self.src, "-frames:v", "1", str(png)])
        if self.mode == "parts":
            _run(["-i", str(png), "-vf", self._base(cx), str(self.out / f"{len(self.log):02d}_静止画_{at}秒_{dur}秒間.jpg")])
            return
        self._clip([self._base(cx), *self._filters(extra)], ["-loop", "1", "-t", str(dur), "-i", str(png)])

    def image(self, path, dur, extra=(), cx=0.5):
        """写真（縦長）を9:16に切り抜いて dur 秒表示"""
        self._record("写真", Path(path).name, 1.0, dur, extra)
        base = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}:x=(iw-{W})*{cx}:y=(ih-{H})/2"
        if self.mode == "parts":
            _run(["-i", str(path), "-vf", base, str(self.out / f"{len(self.log):02d}_写真.jpg")])
            return
        self._clip([base, *self._filters(extra)], ["-loop", "1", "-t", str(dur), "-i", str(path)])

    def color(self, dur, color="black", extra=()):
        self._record({"white": "白い画面", "black": "黒い画面"}.get(color, color), "-", 1.0, dur, extra)
        if self.mode == "parts":
            return
        self._clip(["null", *self._filters(extra)], ["-f", "lavfi", "-t", str(dur), "-i", f"color={color}:s={W}x{H}:r={FPS}"])

    def telop_sheet(self, title):
        L = [f"# {title}｜カット表・テロップ一覧", "",
             "| # | 種類 | 元の動画 | 速度 | 完成での位置（秒） | テロップ |", "|---|---|---|---|---|---|"]
        for n, kind, rng, sp, a, b, texts in self.log:
            L.append(f"| {n:02d} | {kind} | {rng} | {sp}倍 | {a}〜{b} | {' ／ '.join(texts) or '（なし）'} |")
        L += ["", "※ 静止画はJPGで入っています。CapCutに読み込んで、表の秒数ぶん表示してください。",
              "※ 素材の動画は等倍（速度をかけていない状態）です。表の「速度」はおすすめの値です。"]
        return "\n".join(L) + "\n"

    def render(self):
        if self.mode == "parts":
            return self.out
        lst = self.tmp / "list.txt"
        lst.write_text("".join(f"file '{p.resolve()}'\n" for p in self.parts))
        _run(["-f", "concat", "-safe", "0", "-i", str(lst), "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
              "-shortest", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
              "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(self.out)])
        return self.out
