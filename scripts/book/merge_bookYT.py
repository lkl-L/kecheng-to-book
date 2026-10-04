# -*- coding: utf-8 -*-
"""把 46 个《某微课堂》微课堂小节 md 按八卷合并成全书 markdown
结构：书名 H1 / 卷 H2 / 讲 H3，保留【经文】【讲解】标记行
"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "sec-md")
OUT = os.path.join(BASE, "微课堂实录.md")

# 八卷划分：(卷名, [课号...])  —— 卷内按课号升序
VOLUMES = [
    ("卷一　风水总论与源流", [1, 2, 4, 5, 6, 7, 8, 9, 10]),
    ("卷二　形峦经典《地理啖蔗录》精读", [15, 22, 23, 24, 30, 31, 32, 35, 36]),
    ("卷三　经典导读：《博山篇》《地理人子须知》《雪心赋》《风水讲义》", [14, 16, 17, 21, 33, 38]),
    ("卷四　理气与水法", [11, 20, 26, 27, 28, 29, 34, 37, 39, 40]),
    ("卷五　阳宅", [12, 13]),
    ("卷六　择日", [42, 43]),
    ("卷七　命理与相理", [18, 19, 44, 45, 46]),
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
    book = []
    book.append("# 微课堂实录\n")
    book.append("讲师《某微课堂》会员微课堂 46 讲 · 全文整理本\n")
    book.append("—— 形、理、课三纲，微课堂全编 ——\n")
    book.append(
        "本书是讲师先生面向【品牌名】会员群的微课堂连载（第 1 讲至第 46 讲）整理本，"
        "以作者亲撰的课程讲义为底本，融合现场音频讲授的内容整理而成，"
        "按题材编为八卷：先述风水总论与源流，次及形峦经典《地理啖蔗录》与其他经典导读，"
        "再讲理气水法、阳宅、择日、命理相理，末以杂论实战收束。\n"
    )
    book.append(
        "经典导读诸讲沿用全书体例，先出【经文】原文，再附【讲解】；"
        "其余各讲只列【讲解】。课程中的版头广告、口播、招生推广、"
        "以及指向课程配图的提示语均已删去，图中所讲的内容以文字保留；"
        "私人宅第与学员姓名按惯例泛化处理。\n\n"
    )

    total = 0
    vol_chars = {}
    for vname, nums in VOLUMES:
        book.append(f"## {vname}\n")
        vc = 0
        for n in nums:
            p = os.path.join(SRC, f"yt-{n:03d}.md")
            if not os.path.exists(p):
                print(f"!! 缺失 {p}")
                continue
            t = open(p, encoding="utf-8").read()
            title, body = convert_section(t)
            vc += len(body)
            book.append(f"### 第{n}讲　{title}\n")
            book.append(body + "\n")
        vol_chars[vname] = vc
        total += vc
        book.append("")

    md = "\n".join(book)
    open(OUT, "w", encoding="utf-8").write(md)
    print("各卷字数：")
    for k, v in vol_chars.items():
        print(f"  {k}  {v} 字")
    print(f"全书字数（不含标记）: {total}")
    print(f"输出: {OUT}  ({os.path.getsize(OUT)/1024:.0f} KB)")


if __name__ == "__main__":
    main()
