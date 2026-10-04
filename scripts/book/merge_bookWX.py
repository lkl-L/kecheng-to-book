# -*- coding: utf-8 -*-
"""把 8 个《卫星地图阴阳宅综合运用》讲义 md 合并成全书 markdown（保留【讲解】标记行）"""
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
    book.append("# 《卫星地图阴阳宅综合运用》精讲实录\n")
    book.append("卫星地图阴阳宅综合运用课程 · 全文整理本\n")
    book.append("—— 十节课，八讲 ——\n")
    book.append("本课程原本是对着卫星地图讲授的实战课。整理时，凡讲课画面上演示的地形关系"
                "（来龙从哪一方入首、水从哪边来哪边去、水口何在、砂在哪一侧、明堂与穴场的位置）"
                "一律改写为文字表述，读者可依文字自行在图上复原。"
                "文中\"某地\"\"某小区\"\"某先生的宅子\"等，是私人案例的泛化处理；"
                "公开的名山大川、城市与历史名人故居、陵墓则保留原名。\n\n")
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
