# -*- coding: utf-8 -*-
"""按场景切换抽取课程视频的每一张"图"（PPT 页 / 白板内容 / 演示画面）。

原理：每 0.5s 取一帧缩略图，与上一帧比较灰度差；差值超阈值视为画面切换，
把每个稳定片段的最后一帧存下来（白板字越写越多，取最后最完整）。

用法:
  python scene_frames.py <视频> --out <目录> [--thresh 20] [--minseg 3] [--cols 6]

产出:
  <目录>/slides/s000_000512_001023.jpg   片段代表帧（文件名=起止秒）
  <目录>/sheet.jpg                        全部代表帧一览表
  <目录>/scenes.json                      片段时间与文件清单
"""
import argparse
import json
import math
import os

import av
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    r"C:\Windows\Fonts\arial.ttf",
]
THUMB_W, THUMB_H = 160, 90


def load_font(size=16):
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def gray_small(img):
    im = img.convert("L").resize((THUMB_W, THUMB_H), Image.BILINEAR)
    return np.asarray(im, dtype=np.int16)


def fmt_t(sec):
    m, s = divmod(int(sec), 60)
    h, m = divmod(m, 60)
    return f"{h:d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def extract(path, out_dir, thresh=20.0, minseg=3.0, step=0.5, cols=6, width=960):
    os.makedirs(os.path.join(out_dir, "slides"), exist_ok=True)
    segs = []  # (start, last_ts, last_gray, last_pil)

    with av.open(path) as c:
        vs = c.streams.video[0]
        vs.thread_type = "AUTO"
        dur = float(vs.duration * vs.time_base) if vs.duration else 0
        fps = float(vs.average_rate) if vs.average_rate else 24
        skip = max(1, int(round(fps * step)))

        prev_gray = None
        seg_start = 0.0
        last_ts = 0.0
        last_gray = None
        last_img = None
        n_proc = 0

        for fi, frame in enumerate(c.decode(vs)):
            if fi % skip:
                continue
            ts = frame.time if frame.time is not None else fi / fps
            img = frame.to_image()
            g = gray_small(img)
            n_proc += 1

            if prev_gray is None:
                prev_gray, seg_start, last_ts, last_gray, last_img = g, ts, ts, g, img
                continue

            diff = float(np.abs(g - prev_gray).mean())
            if diff > thresh and ts - seg_start >= minseg:
                segs.append((seg_start, last_ts, last_gray, last_img))
                seg_start = ts
                last_gray, last_img = g, img
            else:
                # 同一片段：更新代表帧（保留最新、最全的内容）
                if ts - last_ts >= 1.0:
                    last_gray, last_img, last_ts = g, img, ts
                elif np.abs(g - last_gray).mean() > 3:
                    last_gray, last_img, last_ts = g, img, ts
            prev_gray = g
        if last_img is not None:
            segs.append((seg_start, last_ts, last_gray, last_img))

    # 保存代表帧
    results = []
    for i, (a, b, g, img) in enumerate(segs):
        w, h = img.size
        if width and w > width:
            img = img.resize((width, int(h * width / w)), Image.LANCZOS)
        name = f"s{i:03d}_{int(a*1000):07d}_{int(b*1000):07d}.jpg"
        fp = os.path.join(out_dir, "slides", name)
        img.save(fp, quality=85)
        results.append({"idx": i, "start": round(a, 1), "end": round(b, 1),
                        "file": fp})

    # 过滤太短的杂讯片段（<1s 且与相邻片段几乎相同）由调用方人工判断，这里全保留
    print(f"  处理 {n_proc} 个采样点 -> {len(results)} 个画面片段", flush=True)

    # contact sheet
    if results:
        tw = 300
        thumbs = []
        for r in results:
            im = Image.open(r["file"])
            w, h = im.size
            im = im.resize((tw, max(1, int(h * tw / w))), Image.LANCZOS)
            thumbs.append((r, im))
        th = max(im.size[1] for _, im in thumbs)
        rows = math.ceil(len(thumbs) / cols)
        pad, label_h = 6, 22
        sheet = Image.new("RGB", (cols * (tw + pad) + pad,
                                  rows * (th + label_h + pad) + pad), (255, 255, 255))
        d = ImageDraw.Draw(sheet)
        font = load_font(15)
        for k, (r, im) in enumerate(thumbs):
            x = pad + (k % cols) * (tw + pad)
            y = pad + (k // cols) * (th + label_h + pad)
            sheet.paste(im, (x, y))
            d.text((x + 3, y + th + 3),
                   f"#{r['idx']:03d} {fmt_t(r['start'])}-{fmt_t(r['end'])}",
                   fill=(0, 0, 0), font=font)
        sheet.save(os.path.join(out_dir, "sheet.jpg"), quality=82)

    meta = {"video": path, "duration": dur, "thresh": thresh, "minseg": minseg,
            "scenes": results}
    with open(os.path.join(out_dir, "scenes.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print("sheet + scenes.json ->", out_dir, flush=True)
    return meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--out", required=True)
    ap.add_argument("--thresh", type=float, default=20.0)
    ap.add_argument("--minseg", type=float, default=3.0)
    ap.add_argument("--cols", type=int, default=6)
    ap.add_argument("--width", type=int, default=960)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    print("视频:", os.path.basename(a.video), flush=True)
    extract(a.video, a.out, a.thresh, a.minseg, cols=a.cols, width=a.width)


if __name__ == "__main__":
    main()
