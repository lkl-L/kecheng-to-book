# -*- coding: utf-8 -*-
"""示例：把 8 个讲义小节 md 合并成全书 markdown（纯讲解体、不配图的实战课）"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "sec-md")
OUT = os.path.join(BASE, "实战课实录.md")


def convert_section(text):
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
    book.append("# 《【书名】》精讲实录\n")
    book.append("【课程名】· 全文整理本\n")
    book.append("—— 八讲 ——\n")
    book.append("本课程原本是依赖图示／演示讲授的实战课。整理时，凡演示画面里讲到的关系"
                "（空间方位、路径、先后、结构与数值）一律改写为文字表述，读者可依文字自行复原。"
                "文中\"某地\"\"某小区\"\"某先生的宅子\"等，是私人案例的泛化处理；"
                "公开的地名、城市与历史人物故居则保留原名。\n\n")
    total_chars = 0
    cn = "一二三四五六七八"
    for n in range(1, 9):
        p = os.path.join(SRC, f"wx-{n:03d}.md")
        if not os.path.exists(p):
            print(f"!! 缺失 {p}")
            continue
        t = open(p, encoding="utf-8").read()
        title, body = convert_section(t)
        total_chars += len(body)
        book.append(f"## 第{cn[n-1]}讲　{title}\n")
        book.append(body + "\n")
    md = "\n".join(book)
    open(OUT, "w", encoding="utf-8").write(md)
    print(f"全书字数（不含标记）: {total_chars}")
    print(f"输出: {OUT}  ({os.path.getsize(OUT)/1024:.0f} KB)")


if __name__ == "__main__":
    main()
