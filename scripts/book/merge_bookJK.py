# -*- coding: utf-8 -*-
"""把 30 个《某日课课程》小节 md 合并成全书 markdown（保留【讲解】标记行）"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "sec-md")
OUT = os.path.join(BASE, "日课课实录.md")

CN = "一二三四五六七八九十"


def cn_num(n):
    if n <= 10:
        return CN[n - 1]
    if n < 20:
        return "十" + CN[n - 11]
    if n == 20:
        return "二十"
    if n < 30:
        return "二十" + CN[n - 21]
    return "三十"


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
    book.append("# 《某日课课程》精讲实录\n")
    book.append("讲师团队《某日课课程》三十讲 · 全文整理本\n")
    book.append("—— 依讲义与讲课录音整理 ——\n\n")
    total_chars = 0
    for n in range(1, 31):
        p = os.path.join(SRC, f"jk-{n:03d}.md")
        if not os.path.exists(p):
            print(f"!! 缺失 {p}")
            continue
        t = open(p, encoding="utf-8").read()
        title, body = convert_section(t)
        total_chars += len(body)
        book.append(f"## 日课精讲 {cn_num(n)}：{title}\n")
        book.append(body + "\n")
    md = "\n".join(book)
    open(OUT, "w", encoding="utf-8").write(md)
    print(f"全书字数（不含标记）: {total_chars}")
    print(f"输出: {OUT}  ({os.path.getsize(OUT)/1024:.0f} KB)")


if __name__ == "__main__":
    main()
