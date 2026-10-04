# -*- coding: utf-8 -*-
"""把正文里的半角双引号 " 成对规范化为中文弯引号 “”。

转写稿里子代理混用半角/全角引号，排版前必须统一，否则：
  · docx 里引号字形不统一，观感差；
  · reparagraph.py 的引文提行规则（按 “…” 匹配）失效。

规则：逐行把未配对的行内 `"` 按出现顺序交替替换成 “ 和 ”；
      行内若原本已有 “”，则只对剩余的 `"` 计数（保证开闭正确）。
      若某行出现奇数个 `"`，打印告警，交人工核对（不强行替换最后一个）。

用法：python normalize_quotes.py [书名1 书名2 ...]
"""
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
BOOKS = [
    "经典课实录",
    "赋文课实录",
    "图文课实录",
    "【书名】",
    "实战课实录",
    "【书名】",
]
BAK = os.path.join(BASE, "md.bak-raw")


def norm_line(line):
    """把一行的 `"` 交替替换为 “ ”。返回 (新行, 替换数, 是否奇数)。"""
    n = line.count('"')
    if not n:
        return line, 0, False
    out = []
    open_q = True
    for ch in line:
        if ch == '"':
            out.append("\u201c" if open_q else "\u201d")
            open_q = not open_q
        else:
            out.append(ch)
    return "".join(out), n, (n % 2 == 1)


def process(path, dry=False):
    text = open(path, encoding="utf-8").read()
    lines = text.split("\n")
    total, odd = 0, 0
    new_lines = []
    for i, ln in enumerate(lines):
        nl, c, is_odd = norm_line(ln)
        total += c
        if is_odd:
            odd += 1
            print("   ! 第 %d 行引号奇数：%s" % (i + 1, ln[:60]))
        new_lines.append(nl)
    new = "\n".join(new_lines)
    # 校验：只允许引号字形变化，非引号字符与引号总数都必须一致
    qre = re.compile(r'["\u201c\u201d]')
    if qre.sub("", new) != qre.sub("", text) or len(qre.findall(new)) != len(qre.findall(text)):
        print("!! %s 校验失败（非引号字符被改动）" % os.path.basename(path))
        return False, total, odd
    if not dry:
        os.makedirs(BAK, exist_ok=True)
        dst = os.path.join(BAK, os.path.basename(path))
        if not os.path.exists(dst):
            open(dst, "w", encoding="utf-8").write(text)
        open(path, "w", encoding="utf-8").write(new)
    return True, total, odd


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry" in sys.argv
    targets = args or BOOKS
    bad = 0
    for name in targets:
        p = os.path.join(BASE, name + ".md")
        ok, c, odd = process(p, dry=dry)
        print("%s %-34s 归一 %4d 个引号%s" %
              ("OK " if ok else "FAIL", name, c,
               "  （%d 行奇数，需人工核）" % odd if odd else ""))
        bad += 0 if ok else 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
