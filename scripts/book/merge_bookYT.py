# -*- coding: utf-8 -*-
"""示例：把按讲整理的 sec-md 稿，按「卷 → 讲」三级骨架合并成全书 markdown。

结构：书名 H1 / 卷 H2 / 讲 H3，保留【原文】【讲解】标记行。
适用场景：课程主题跨度极大、需要按内容分卷（见 SKILL.md 第五节）。

用法：
  1) 填好 VOLUMES（**分卷的唯一事实来源**）；
  2) 改 OUT / PREFIX / N_LESSONS；
  3) 运行。卷内一律按讲号升序，不按"由浅入深"重排。
"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "sec-md")
PREFIX = "yt"                       # 章节稿文件名：sec-md/<PREFIX>-NNN.md
OUT = os.path.join(BASE, "【书名】.md")
N_LESSONS = 46                      # 讲数，用于自检

# 分卷划分：(卷名, [讲号...])  —— 卷内按讲号升序
# 所有卷的讲号并集必须 = 1..N_LESSONS 且无重复（见 main 里 assert）。
VOLUMES = [
    ("卷一　总论与源流", [1, 2, 4, 5, 6, 7, 8, 9, 10]),
    ("卷二　主干文本精读", [15, 22, 23, 24, 30, 31, 32, 35, 36]),
    ("卷三　其他文本导读", [14, 16, 17, 21, 33, 38]),
    ("卷四　方法与技术专题", [11, 20, 26, 27, 28, 29, 34, 37, 39, 40]),
    ("卷五　应用场景一", [12, 13]),
    ("卷六　应用场景二", [42, 43]),
    ("卷七　相邻领域", [18, 19, 44, 45, 46]),
    ("卷八　杂论与实战", [3, 25, 41]),
]


def convert_section(text):
    """拆出节标题与正文（去掉原 ## 标题行）"""
    lines = text.split("\n")
    title = ""
    body = []
    for ln in lines:
        s = ln.rstrip()
        if s.startswith("## "):
            title = s[3:].strip()
            continue
        body.append(s)
    out = []
    for ln in body:
        if ln.strip() == "" and (not out or out[-1].strip() == ""):
            continue
        out.append(ln)
    while out and out[-1].strip() == "":
        out.pop()
    return title, "\n".join(out)


def main():
    # 骨架自检：讲号并集必须覆盖 1..N 且无重复
    nums = [n for _, ns in VOLUMES for n in ns]
    assert sorted(nums) == list(range(1, N_LESSONS + 1)), (sorted(nums), N_LESSONS)

    book = []
    book.append("# 【书名】\n")
    book.append("【副标题】\n")
    book.append("—— 【题记】 ——\n")
    book.append(
        "本书是【课程名】连载（第 1 讲至第 %d 讲）的整理本，"
        "以讲授者亲撰的课程讲义为底本，融合现场讲授内容整理而成，"
        "按题材编为若干卷。\n" % N_LESSONS
    )
    book.append(
        "讲解文本的诸讲沿用全书体例，先出【原文】，再附【讲解】；"
        "其余各讲只列【讲解】。课程中的版头广告、口播、招生推广、"
        "以及指向配图的提示语均已删去，图中所讲的内容以文字保留；"
        "私人信息与学员姓名按惯例泛化处理。\n\n"
    )

    total = 0
    vol_chars = {}
    for vname, ns in VOLUMES:
        book.append("## %s\n" % vname)
        vc = 0
        for n in ns:
            p = os.path.join(SRC, "%s-%03d.md" % (PREFIX, n))
            if not os.path.exists(p):
                print("!! 缺失 %s" % p)
                continue
            t = open(p, encoding="utf-8").read()
            title, body = convert_section(t)
            vc += len(body)
            book.append("### 第%d讲　%s\n" % (n, title))
            book.append(body + "\n")
        vol_chars[vname] = vc
        total += vc
        book.append("")

    md = "\n".join(book)
    open(OUT, "w", encoding="utf-8").write(md)
    print("各卷字数：")
    for k, v in vol_chars.items():
        print("  %s  %d 字" % (k, v))
    print("全书字数（不含标记）: %d" % total)
    print("输出: %s  (%.0f KB)" % (OUT, os.path.getsize(OUT) / 1024))


if __name__ == "__main__":
    main()
