# -*- coding: utf-8 -*-
"""示例：把一份权威原文（从 docx/PDF 提取出的 txt）按章节标题切分，
再按课程节号映射，输出"每节该配哪段原文"的片段文件。

为什么要先做这一步：逐句讲解类课程，子代理整理每一节时都要贴出该节的原文块。
先建好映射，子代理直接读 `scripture/sec-NN.txt` 即可，不必自己在一整本书里找。

输出：scripture/sec-NN.txt（NN = 节号，两位）
用法：填好 SRC / TITLES / MAP 再运行；MAP 必须覆盖全部节号且不重复。
"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "【原文文件】.txt")
OUT = os.path.join(BASE, "scripture")
os.makedirs(OUT, exist_ok=True)

lines = open(SRC, encoding="utf-8").read().split("\n")

# 原文里的章节标题行（与正文区分：短、独立成行、不以标点结尾）
TITLES = [
    "【标题一】", "【标题二】", "【标题三】",
    # ……按原文实际标题补全
]

# 切分：收集每个标题的正文段
sections = {}  # title -> [lines]
cur = None
for ln in lines:
    s = ln.strip()
    if s in TITLES and s != cur:
        cur = s
        sections.setdefault(s, [])
        continue
    if cur and s:
        sections[cur].append(s)

# 课程节号 -> 章节标题列表（一节可对应多个标题；同一标题可被多节共用）
MAP = {
    1: ["【标题一】"],
    2: ["【标题一】"],
    3: ["【标题二】", "【标题三】"],
    # ……补全到最后一节
}

for sec, chaps in MAP.items():
    parts = []
    for c in chaps:
        body = sections.get(c, [])
        if body:
            parts.append("【%s】\n%s" % (c, "\n".join(body)))
    if parts:
        txt = "\n\n".join(parts)
        fn = os.path.join(OUT, "sec-%02d.txt" % sec)
        open(fn, "w", encoding="utf-8").write(txt)
        print("sec-%02d.txt  %d 字  <- %s" % (sec, len(txt), ",".join(chaps)))
    else:
        print("sec-%02d  无对应章节，跳过" % sec)

# 自检：MAP 的节号应连续覆盖 1..N
nums = sorted(MAP)
if nums != list(range(1, len(nums) + 1)):
    print("!! 节号不连续：%s" % nums)
