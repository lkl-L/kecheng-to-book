# -*- coding: utf-8 -*-
"""示例：把去重后的案例按主题分卷、再切成"节"，
为每一节生成自包含的素材文件（含完整正文），供子代理直接读写稿。

用法：
  1) 先跑 extract_cases.py + triage.py 得到 cases_tagged.json（含 theme 字段）；
  2) 填好 PLAN（卷名 / 主题标签 / 取例数 / 分几节）；
  3) 运行，输出 cases/volN_sM.txt。
"""
import json
import re
import os

BASE = r"<项目根>/book9"
OUT = os.path.join(BASE, "cases")
os.makedirs(OUT, exist_ok=True)

# (卷名, 主题标签, 取例数, 分几节)
PLAN = [
    ("卷一　【主题一】", "主题一", 24, 3),
    ("卷二　【主题二】", "主题二", 27, 3),
    ("卷三　【主题三】", "主题三", 21, 3),
    ("卷四　【主题四】", "主题四", 21, 3),
    ("卷五　【主题五】", "主题五", 18, 2),
    ("卷六　综合案例", None, 18, 2),
]

SKIP_SRC = {"【不参与选例的源文件】"}


def main():
    units = json.load(open(os.path.join(BASE, "cases_tagged.json"), encoding="utf-8"))
    units = [u for u in units if u["src"] not in SKIP_SRC and u["len"] >= 600]
    used, manifest = set(), []
    for vi, (title, theme, want, nsec) in enumerate(PLAN, 1):
        if theme:
            pool = [u for u in units if u["theme"] == theme]
        else:
            # 综合卷：取未被别卷选走、且讨论较厚的（各主题混合，作全书收官）
            pool = [u for u in units if id(u) not in used]
        pool = [u for u in pool if id(u) not in used]
        pool.sort(key=lambda u: -u["len"])
        picked = pool[:want]
        for u in picked:
            used.add(id(u))
        # 按篇幅均衡装箱：长例优先放进当前最轻的一节
        total = sum(u["len"] for u in picked)
        need = max(1, min(4, -(-total // 30000)))
        nsec = max(nsec, need)
        secs = [[] for _ in range(nsec)]
        load = [0] * nsec
        for u in picked:
            k = load.index(min(load))
            secs[k].append(u)
            load[k] += u["len"]
        for si, group in enumerate(secs, 1):
            fn = os.path.join(OUT, "vol%d_s%d.txt" % (vi, si))
            with open(fn, "w", encoding="utf-8") as fp:
                fp.write("%s　第%d节　素材（共 %d 例）\n" % (title, si, len(group)))
                fp.write("=" * 70 + "\n\n")
                for k, u in enumerate(group, 1):
                    fp.write("【原始案例 %d】出处：%s 第 %s 页\n" % (k, u["src"], u["page"]))
                    fp.write("标志词：%s　要素串（OCR 原样，可能有误识）：%s\n" % (u["mark"], u["key"]))
                    fp.write("演变：%s\n" % u["seq"])
                    fp.write("时间：%s\n" % u["time"])
                    if u.get("dups"):
                        fp.write("重出于：%s\n" % ", ".join(u["dups"][:5]))
                    fp.write("讨论篇幅：%d 字\n" % u["len"])
                    fp.write("表头原文（OCR 原样，要素串在此）：\n  %s\n" % u.get("raw_head", ""))
                    fp.write("-" * 66 + "\n")
                    fp.write(u["body"].strip() + "\n\n")
            manifest.append((os.path.basename(fn), title, si, len(group),
                             sum(x["len"] for x in group)))
    print("%-16s %-4s %-5s %s" % ("素材文件", "节", "例数", "源字数"))
    for fn, title, si, n, ln in manifest:
        print("%-16s %-4d %-5d %d" % (fn, si, n, ln))
    print("合计 %d 节 %d 例 %d 字源材料" % (len(manifest),
                                     sum(m[3] for m in manifest), sum(m[4] for m in manifest)))
    json.dump([{"file": m[0], "vol": m[1], "sec": m[2], "n": m[3]} for m in manifest],
              open(os.path.join(BASE, "volumes.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
