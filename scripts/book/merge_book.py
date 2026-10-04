# -*- coding: utf-8 -*-
"""把 60 个小节 md 合并成全书 markdown
体例：第一编 撼龙经（001-026）/ 第二编 疑龙经（027-060）
【经文】块转 markdown 引用（> 前缀），【讲解】标记去除
"""
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "sec-md")
OUT = os.path.join(BASE, "经典课实录.md")

PART1 = (1, 26, "第一编 撼龙经")
PART2 = (27, 60, "第二编 疑龙经")

INTRO = {
    "第一编 撼龙经": "本编为 2024 年私教课《撼龙经》部分整理稿，凡二十六节，自总纲起，历统局、垣局、九星、变穴、吉凶诸篇，至全书总结止。",
    "第二编 疑龙经": "本编为 2024 年私教课《疑龙经》部分整理稿，凡三十四节，依次论龙、论局、论穴，并附以古证今、僧道嗣续、阳宅、日课诸篇。",
}


def convert_section(text):
    """保留【经文】【讲解】标记行（docx 中作为独立段落）；返回 (标题, 正文md)"""
    lines = text.split("\n")
    title = ""
    body = []
    for ln in lines:
        s = ln.rstrip()
        if s.startswith("## "):
            title = s[3:].strip()
            continue
        body.append(s)
    # 压缩连续空行 + 去首尾空行
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
    book.append("# 《撼龙经》《疑龙经》精讲实录\n")
    book.append("讲师 2024 年私教课 · 六十讲全文整理本\n")
    book.append("—— 经文原文与白话讲解对照 ——\n\n")
    total_chars = 0
    for lo, hi, part_title in (PART1, PART2):
        book.append(f"# {part_title}\n")
        book.append(INTRO[part_title] + "\n")
        for n in range(lo, hi + 1):
            p = os.path.join(SRC, f"01-{n:03d}.md")
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
