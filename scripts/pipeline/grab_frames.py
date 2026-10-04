# -*- coding: utf-8 -*-
"""从课程视频抽取关键帧，并拼成缩略图一览表（contact sheet）。

用法:
  python grab_frames.py <视频> --out <目录> --count 24 [--start 0] [--end 0]

产出:
  <目录>/frames/f000_0000123456.jpg   单帧（约 960px 宽）
  <目录>/sheet.jpg                    缩略图一览（默认 5 列），带时间标注
  <目录>/frames.json                  每帧的时间戳/文件路径
"""
import argparse
import json
import os
import sys

import av
from PIL import Image, ImageDraw, ImageFont

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    r"C:\Windows\Fonts\arial.ttf",
]


def load_font(size=18):
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def video_info(path):
    with av.open(path) as c:
        s = c.streams.video[0]
        cc = s.codec_context
        dur = float(s.duration * s.time_base) if s.duration else float(c.duration / 1_000_000 if c.duration else 0)
        return {
            "codec": cc.name,
            "width": cc.width,
            "height": cc.height,
            "fps": float(s.average_rate) if s.average_rate else 0,
            "duration": dur,
            "n_frames": int(s.frames) if s.frames else 0,
        }


def grab(path, out_dir, count=24, start=0.0, end=None, width=960, cols=5, quality=80):
    info = video_info(path)
    dur = info["duration"]
    if end is None or end <= 0:
        end = dur
    if start >= end:
        start = 0.0

    frames_dir = os.path.join(out_dir, "frames")
    os.makedirs(frames_dir, exist_ok=True)

    span = end - start
    # 均匀取样时间点（避开首尾各 2%）
    pts = [start + span * (0.02 + 0.96 * i / max(count - 1, 1)) for i in range(count)]

    results = []
    with av.open(path) as c:
        vs = c.streams.video[0]
        vs.thread_type = "AUTO"
        for i, ts in enumerate(pts):
            try:
                c.seek(int(ts * av.time_base), backward=True)
            except Exception:
                pass
            got = None
            try:
                for frame in c.decode(vs):
                    if frame.time is None or frame.time + 0.5 >= ts:
                        got = frame
                        break
            except Exception:
                pass
            if got is None:
                continue
            img = got.to_image()
            real_ts = got.time if got.time is not None else ts
            w, h = img.size
            if width and w > width:
                img = img.resize((width, int(h * width / w)), Image.LANCZOS)
            name = f"f{i:03d}_{int(real_ts*1000):09d}.jpg"
            fp = os.path.join(frames_dir, name)
            img.save(fp, quality=quality)
            results.append({"idx": i, "ts": round(real_ts, 2), "file": fp})
            print(f"  [{i+1}/{count}] t={real_ts/60:6.1f}min -> {name}", flush=True)

    # 拼 contact sheet
    if results:
        tw = 320
        thumbs = []
        for r in results:
            im = Image.open(r["file"])
            w, h = im.size
            im = im.resize((tw, max(1, int(h * tw / w))), Image.LANCZOS)
            thumbs.append((r, im))
        th = max(im.size[1] for _, im in thumbs)
        rows = (len(thumbs) + cols - 1) // cols
        pad, label_h = 6, 22
        sheet_w = cols * (tw + pad) + pad
        sheet_h = rows * (th + label_h + pad) + pad
        sheet = Image.new("RGB", (sheet_w, sheet_h), (255, 255, 255))
        d = ImageDraw.Draw(sheet)
        font = load_font(16)
        for k, (r, im) in enumerate(thumbs):
            cx, cy = k % cols, k // cols
            x = pad + cx * (tw + pad)
            y = pad + cy * (th + label_h + pad)
            sheet.paste(im, (x, y))
            label = f"#{r['idx']:02d}  {int(r['ts'])//60:02d}:{int(r['ts'])%60:02d}"
            d.text((x + 3, y + th + 3), label, fill=(0, 0, 0), font=font)
        sp = os.path.join(out_dir, "sheet.jpg")
        sheet.save(sp, quality=82)
        print("sheet ->", sp, f"{sheet.size[0]}x{sheet.size[1]}", flush=True)

    meta = {"video": path, "info": info, "start": start, "end": end, "frames": results}
    with open(os.path.join(out_dir, "frames.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    return meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--out", required=True)
    ap.add_argument("--count", type=int, default=24)
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float, default=0.0)
    ap.add_argument("--width", type=int, default=960)
    ap.add_argument("--cols", type=int, default=5)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    info = video_info(a.video)
    print(f"视频: {os.path.basename(a.video)}")
    print(f"  {info['width']}x{info['height']} {info['fps']:.1f}fps {info['codec']} 时长 {info['duration']/60:.1f} 分钟")
    grab(a.video, a.out, a.count, a.start, a.end, a.width, a.cols)


if __name__ == "__main__":
    main()
