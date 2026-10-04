# -*- coding: utf-8 -*-
"""对去重后的案例做主题粗分类，并导出人可读摘要 digest.txt 供人工核对。"""
import json, re, os
from collections import Counter

BASE = r"<项目根>/book9"

THEMES = [
    ("【主题一】", "关键词1|关键词2|关键词3"),
    ("【主题二】", "关键词1|关键词2|关键词3"),
    ("【主题三】", "关键词1|关键词2|关键词3"),
    ("【主题四】", "关键词1|关键词2|关键词3"),
    ("【主题五】", "关键词1|关键词2|关键词3"),
]
# 说明：主题名与关键词表都按你的领域改；一份案例可能命中多个主题，
# score() 取命中次数最多的那一个作为粗分类结果，人工可在 digest.txt 上复核。]


def score(body):
    c = Counter()
    for name, pat in THEMES:
        c[name] = len(re.findall(pat, body))
    return c


def main():
    d = json.load(open(os.path.join(BASE, "cases.json"), encoding="utf-8"))
    units = [u for u in d["units"] if u["len"] >= 400]
    for u in units:
        u["body"] = re.sub(r"\[\[PAGE:\d+\]\]", "", u["body"])
        c = score(u["body"])
        top = c.most_common(2)
        u["theme"] = top[0][0] if top and top[0][1] > 0 else "综合案例"
        u["scores"] = dict(c)
    dist = Counter(u["theme"] for u in units)
    print(">=400 字案例 %d 例，主题粗分：" % len(units))
    for k, v in dist.most_common():
        print("   %-12s %3d" % (k, v))

    with open(os.path.join(BASE, "digest.txt"), "w", encoding="utf-8") as fp:
        for i, u in enumerate(units, 1):
            fp.write("#%03d [%s] %s %s  演变%s  时间%s  (%s p%s, %d字)\n" % (
                i, u["theme"], u["mark"], u["key"], u["seq"][:40], u["time"][:30],
                u["src"], u["page"], u["len"]))
            fp.write(re.sub(r"\n+", " ", u["body"][:760]) + "\n\n")
    json.dump(units, open(os.path.join(BASE, "cases_tagged.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("已写 digest.txt / cases_tagged.json")


if __name__ == "__main__":
    main()
