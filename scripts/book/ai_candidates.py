# -*- coding: utf-8 -*-
"""为 AI 复核层生成候选清单。

只挑两类最可能有问题的段落，控制规模：
  · LONG  —— 正文段落 >180 字（规则层按 165 目标装箱后仍偏长的，值得人工再切一刀）；
  · SHORT —— 12~55 字的碎段（可能是被切坏的断头段，需要判断要不要并回上一段）。

输出 book/ai_tasks/<书名>.txt，供子代理逐条判断后写回 book/ai_out/<书名>.txt。
格式约定（子代理必须照此输出，脚本据此落地并逐字校验）：
    L<行号>\tKEEP
    L<行号>\tSPLIT\t片段1||片段2||片段3        ← 拼接后必须与原段逐字相同
    L<行号>\tMERGE_NEXT                        ← 并回下一段
"""
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.join(BASE, "ai_tasks")
BOOKS = [
    "经典课实录",
    "赋文课实录",
    "图文课实录",
    "日课课实录",
    "实战课实录",
    "微课堂实录",
]
LONG_MIN = 181
SHORT_MIN, SHORT_MAX = 12, 55
RE_MARK = re.compile(r"^【[^】]{1,10}】$")


def collect(path):
    lines = open(path, encoding="utf-8").read().split("\n")
    in_j = False
    long_items, short_items = [], []
    for i, l in enumerate(lines, 1):
        s = l.strip()
        if s == "【经文】":
            in_j = True
            continue
        if s in ("【讲解】", "【原文】", "【白话】", "【注解】"):
            in_j = False
            continue
        if not s or s.startswith("#") or in_j or RE_MARK.match(s):
            continue
        core = s[2:].strip() if s.startswith("> ") else s
        if len(core) >= LONG_MIN:
            long_items.append((i, core))
        elif SHORT_MIN <= len(core) <= SHORT_MAX:
            short_items.append((i, core))
    return long_items, short_items


def neighbours(lines, idx):
    def prev_body(k):
        j = k - 1
        while j >= 0 and not lines[j].strip():
            j -= 1
        return lines[j].strip()[-26:] if j >= 0 else ""
    def next_body(k):
        j = k + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        return lines[j].strip()[:26] if j < len(lines) else ""
    return prev_body(idx), next_body(idx)


def main():
    os.makedirs(TASK, exist_ok=True)
    long_only = os.environ.get("AI_LONG_ONLY") == "1"
    for b in BOOKS:
        path = os.path.join(BASE, b + ".md")
        lines = open(path, encoding="utf-8").read().split("\n")
        long_items, short_items = collect(path)
        if long_only:
            short_items = []
        out = ["# 待复核清单：%s" % b,
               "# 共 %d 条：LONG %d 条 / SHORT %d 条"
               % (len(long_items) + len(short_items), len(long_items), len(short_items)),
               "# 输出写在 ai_out/%s.txt，格式见表头说明。" % b, ""]
        for i, core in long_items:
            p, n = neighbours(lines, i - 1)
            out.append("=== L%d LONG len=%d" % (i, len(core)))
            out.append("上一段尾：…%s" % p)
            out.append(core)
            out.append("下一段头：%s…" % n)
            out.append("")
        for i, core in short_items:
            p, n = neighbours(lines, i - 1)
            out.append("=== L%d SHORT len=%d" % (i, len(core)))
            out.append("上一段尾：…%s" % p)
            out.append(core)
            out.append("下一段头：%s…" % n)
            out.append("")
        dst = os.path.join(TASK, b + ".txt")
        open(dst, "w", encoding="utf-8").write("\n".join(out))
        print("%-34s LONG %4d  SHORT %4d  → %s" %
              (b, len(long_items), len(short_items), os.path.basename(dst)))


if __name__ == "__main__":
    main()
