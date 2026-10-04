# -*- coding: utf-8 -*-
"""实测转写速度：挑一个文件的前 20 分钟切片，输出实时倍率"""
import glob
import json
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cuda_env  # noqa: F401  必须在 faster_whisper 之前

from audio_utils import iter_slices, write_wav, SLICE_SEC  # noqa
from faster_whisper import WhisperModel  # noqa

ROOT = r"<媒体盘>/<课程目录>"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bench.json")

PROMPT = ("这是风水堪舆课程讲座。术语：寻龙点穴、龙脉、过峡、开帐、束气、蜂腰鹤膝、"
          "砂、水口、明堂、案山、朝山、青龙白虎、朱雀玄武、疑龙经、撼龙经、雪心赋、"
          "倒杖、葬法、峦头、理气、三合、三元、九星、贪狼巨门、罗盘分金、消砂纳水、"
          "阴阳宅、卫星地图、【机构名】。")


def main():
    beam = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    print(f"beam_size={beam}", flush=True)
    # 挑 01 课程第一个 mp4
    d = os.path.join(ROOT, "01.某课程（60 集）")
    src = None
    for dp, _, fns in os.walk(d):
        for fn in sorted(fns):
            if fn.lower().endswith(".mp4"):
                src = os.path.join(dp, fn)
                break
        if src:
            break
    assert src, "no sample found"
    print("sample:", src, flush=True)

    model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "..", "models", "faster-whisper-medium")
    ct = sys.argv[2] if len(sys.argv) > 2 else "int8_float16"
    print(f"compute_type={ct}", flush=True)
    t0 = time.time()
    model = WhisperModel(model_dir, device="cuda",
                         compute_type=ct, cpu_threads=4)
    print(f"model loaded in {time.time()-t0:.0f}s", flush=True)

    # 解码切片
    t0 = time.time()
    wav = os.path.join(os.path.dirname(OUT), "bench_slice.wav")
    n = 0
    for s in iter_slices(src, slice_sec=SLICE_SEC):
        write_wav(wav, s)
        n += 1
        break
    decode_t = time.time() - t0
    print(f"decode 20min slice: {decode_t:.1f}s", flush=True)

    # 转写（关 VAD，按保守情况测）
    t0 = time.time()
    segs, info = model.transcribe(wav, language="zh", beam_size=beam,
                                  initial_prompt=PROMPT,
                                  condition_on_previous_text=False,
                                  vad_filter=False)
    chars = 0
    first_texts = []
    for x in segs:
        chars += len(x.text.replace(" ", ""))
        if len(first_texts) < 3:
            first_texts.append(x.text.strip())
    tr_t = time.time() - t0
    rate = SLICE_SEC / tr_t
    print(f"transcribe: {tr_t:.0f}s  chars={chars}  realtime_x={rate:.1f}", flush=True)
    print("sample text:", " | ".join(first_texts), flush=True)

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"decode_sec": round(decode_t, 1),
                   "transcribe_sec": round(tr_t, 1),
                   "chars": chars, "realtime_x": round(rate, 2)},
                  f, ensure_ascii=False, indent=1)
    print("OK ->", OUT)


if __name__ == "__main__":
    main()
