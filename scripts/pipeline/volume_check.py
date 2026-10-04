# -*- coding: utf-8 -*-
"""音量体检：抽样算 RMS/峰值/静音占比 + VAD on/off 字数对比"""
import json
import os
import sys
import tempfile
import time

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audio_utils import iter_slices, write_wav, TARGET_SR  # noqa

import av

ROOT = r"<媒体盘>/<课程目录>"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio_check.json")

# 抽样：每个大类挑 1 个
SAMPLES = [
    (r"01.某课程（60 集）", ".mp4"),
    (r"4.讲师丰水词典（抖音直播全程精华回放）", None),
    (r"07.某微课堂（音频+讲义）", ".mp3"),
    (r"15、形势系统精讲课视频74集", None),
]


def find_sample(sub, ext):
    d = os.path.join(ROOT, sub)
    for dp, _, fns in os.walk(d):
        for fn in sorted(fns):
            if ext is None or fn.lower().endswith(ext):
                return os.path.join(dp, fn)
    return None


def volume_stats(path, minutes=5):
    """取前 N 分钟算 RMS / 峰值 / 静音占比"""
    need = minutes * 60 * TARGET_SR
    chunks = []
    got = 0
    for s in iter_slices(path, slice_sec=minutes * 60):
        chunks.append(s)
        got += len(s)
        if got >= need:
            break
    if not chunks:
        return None
    a = np.concatenate(chunks)[:need]
    rms = float(np.sqrt((a ** 2).mean()))
    peak = float(np.abs(a).max())
    silent = float((np.abs(a) < 0.003).mean())  # 约 -50dB 以下视为静音
    return {"rms": round(rms, 4), "peak": round(peak, 4),
            "silent_ratio": round(silent, 3)}


def vad_compare(path, model):
    """同一切片 vad on/off 各转一次，比字数"""
    with tempfile.TemporaryDirectory() as td:
        wav = os.path.join(td, "c.wav")
        for s in iter_slices(path, slice_sec=3 * 60):  # 取前 3 分钟
            write_wav(wav, s)
            break
        res = {}
        for vad in (True, False):
            t0 = time.time()
            segs, _ = model.transcribe(wav, language="zh", beam_size=5,
                                       vad_filter=vad,
                                       condition_on_previous_text=False)
            text = "".join(x.text for x in segs)
            res[str(vad)] = {"chars": len(text.replace(" ", "")),
                             "sec": round(time.time() - t0, 1)}
        return res


def main():
    report = {}
    found = []
    for sub, ext in SAMPLES:
        p = find_sample(sub, ext)
        if p:
            found.append(p)
    for p in found:
        print(f"--- {p}", flush=True)
        st = volume_stats(p)
        print(f"    {st}", flush=True)
        report[p] = {"volume": st}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print("OK ->", OUT)


if __name__ == "__main__":
    main()
