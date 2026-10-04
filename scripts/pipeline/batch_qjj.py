# -*- coding: utf-8 -*-
"""千金赋 9 集批量场景抽帧驱动。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scene_frames import extract

BASE = r"<媒体盘>/02.某课程（9 集）"
OUT = r"<项目根>/figures/qjj"
NUMS = "一二三四五六七八九"
SPACED = {5, 6, 7}

for i in range(1, 10):
    n = NUMS[i - 1]
    name = f"《地理千金赋 》第{n}节课.ts" if i in SPACED else f"《地理千金赋》第{n}节课.ts"
    if i == 2:
        name = f"《地理千金赋》第{n}节课.mp4"
    f = os.path.join(BASE, name)
    if not os.path.exists(f):
        print(f"!! 缺失 第{i}讲: {f}")
        continue
    print(f"===== 第{i}讲 {name}", flush=True)
    try:
        m = extract(f, os.path.join(OUT, f"lesson0{i}"))
        print(f"  -> {len(m['scenes'])} 个片段", flush=True)
    except Exception as e:
        print(f"  !! 失败: {e}", flush=True)
print("ALL_DONE")
