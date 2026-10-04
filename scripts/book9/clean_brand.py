# -*- coding: utf-8 -*-
"""命例集：清掉品牌名残留。

对象：
  · sec-md/pz-*.md   已写出的章节稿（正文）
  · cases/*.txt      分节素材（子代理直接读，必须干净，免得照抄）
  · digest.txt       分类摘要
"""
import glob
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

# 素材里的页眉残留（「命理 93」之类）与正文称谓，一并中性化
MAP = [
    ("基础-第五版", "基础讲义第五版"),
    ("命理珍藏版", "命理讲义珍藏版"),
    ("命理", ""),          # 页眉「命理 93」→「 93」
    ("俞理", ""),
    ("一脉", "本门"),
    ("命", ""),
]


def clean(text):
    for old, new in MAP:
        text = text.replace(old, new)
    return text


def main():
    targets = (
        sorted(glob.glob("sec-md/pz-*.md"))
        + sorted(glob.glob("cases/*.txt"))
        + ["digest.txt"]
    )
    tot_before = tot_after = 0
    for path in targets:
        if not os.path.exists(path):
            continue
        t = open(path, encoding="utf-8").read()
        n = t.count("")
        if not n:
            continue
        tot_before += n
        t2 = clean(t)
        t2 = re.sub(r"[ \t]+\n", "\n", t2)
        open(path, "w", encoding="utf-8").write(t2)
        after = t2.count("")
        tot_after += after
        print("%-28s %3d → %d" % (os.path.basename(path), n, after))
    print("合计  %d → %d" % (tot_before, tot_after))


if __name__ == "__main__":
    main()
