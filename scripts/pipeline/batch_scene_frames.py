# -*- coding: utf-8 -*-
"""示例：批量场景抽帧驱动。

为什么用 python 驱动、而不是 bash 循环：中文文件名在 bash 里容易翻车。

用法：
  1) 填好 BASE（媒体目录）/ OUT（输出目录）/ N（集数）/ name_of()（每集的文件名规则）；
  2) 运行。逐集调用 scene_frames.extract，单集失败不影响后续。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scene_frames import extract

BASE = r"<媒体盘>/【课程目录】"
OUT = r"<项目根>/figures/【课程前缀】"
N = 9
NUMS = "一二三四五六七八九"


def name_of(i):
    """第 i 集的文件名（按你的实际文件命名规则改）。"""
    return "第%s节课.ts" % NUMS[i - 1]


for i in range(1, N + 1):
    f = os.path.join(BASE, name_of(i))
    if not os.path.exists(f):
        print("!! 缺失 第%d讲: %s" % (i, f))
        continue
    print("===== 第%d讲 %s" % (i, os.path.basename(f)), flush=True)
    try:
        m = extract(f, os.path.join(OUT, "lesson%02d" % i))
        print("  -> %d 个片段" % len(m["scenes"]), flush=True)
    except Exception as e:
        print("  !! 失败: %s" % e, flush=True)
print("ALL_DONE")
