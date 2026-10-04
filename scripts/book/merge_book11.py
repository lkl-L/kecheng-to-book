# -*- coding: utf-8 -*-
"""把 33 个小节 md 合并成全书 markdown（保留【原文】【讲解】标记行）"""
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "sec-md")
OUT = os.path.join(BASE, "赋文课实录.md")


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
    book.append("【课程名】解读三十三讲 · 全文整理本\n")
    book.append("—— 【原文】与讲解对照 ——\n\n")
    total_chars = 0
    for n in range(1, 34):
        p = os.path.join(SRC, f"11-{n:03d}.md")
        if not os.path.exists(p):
            print(f"!! 缺失 {p}")
            continue
        t = open(p, encoding="utf-8").read()
        title, body = convert_section(t)
        total_chars += len(body)
        book.append(f"## {title}\n")
        book.append(body + "\n")
    md = "\n".join(book)
    open(OUT, "w", encoding="utf-8").write(md)
    print(f"全书字数（不含标记）: {total_chars}")
    print(f"输出: {OUT}  ({os.path.getsize(OUT)/1024:.0f} KB)")


if __name__ == "__main__":
    main()
