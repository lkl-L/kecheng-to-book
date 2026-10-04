# -*- coding: utf-8 -*-
"""从 <资料目录> 提取所有可读文档为纯文本，存 book8/materials/。

PDF 分两类：有文字层的直接抽取；纯扫描件（无文字层）用 pymupdf 渲染关键页做 OCR 备用清单。
"""
import os
import re
import sys
import glob
import pymupdf
from docx import Document

sys.stdout.reconfigure(encoding="utf-8")
SRC = r"<资料目录>"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "materials")
os.makedirs(OUT, exist_ok=True)


def clean(s):
    s = s.replace("\u3000", " ").replace("\xa0", " ")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def from_docx(path):
    d = Document(path)
    parts = [p.text for p in d.paragraphs]
    # 表格内容也提取（归纳表类）
    for t in d.tables:
        for row in t.rows:
            cells = [c.text.strip().replace("\n", " ") for c in row.cells]
            if any(cells):
                parts.append(" | ".join(cells))
    return clean("\n".join(parts))


def from_pdf(path):
    d = pymupdf.open(path)
    parts = []
    for i in range(len(d)):
        try:
            parts.append(d[i].get_text())
        except Exception:  # noqa: BLE001
            parts.append("")
    d.close()
    return clean("\n".join(parts))


def main():
    report = []
    # docx
    for f in sorted(glob.glob(os.path.join(SRC, "**", "*.docx"), recursive=True)):
        base = os.path.basename(f)
        if base.startswith("~$"):
            continue
        try:
            txt = from_docx(f)
        except Exception as e:  # noqa: BLE001
            report.append(("DOCX-ERR", base, str(e)[:60])); continue
        out = os.path.join(OUT, os.path.splitext(base)[0] + ".txt")
        open(out, "w", encoding="utf-8").write(txt)
        report.append(("docx", base, len(re.sub(r"\s", "", txt))))

    # pdf
    for f in sorted(glob.glob(os.path.join(SRC, "**", "*.pdf"), recursive=True)):
        base = os.path.basename(f)
        try:
            txt = from_pdf(f)
        except Exception as e:  # noqa: BLE001
            report.append(("PDF-ERR", base, str(e)[:60])); continue
        n = len(re.sub(r"\s", "", txt))
        d = pymupdf.open(f); pages = len(d); d.close()
        out = os.path.join(OUT, os.path.splitext(base)[0] + ".txt")
        open(out, "w", encoding="utf-8").write(txt)
        tag = "pdf" if n > pages * 60 else "pdf-扫描(需OCR)"
        report.append((tag, base, "%d页 %d字" % (pages, n)))

    print("%-16s %-52s %s" % ("类型", "文件", "规模"))
    for t, b, s in report:
        print("%-16s %-52s %s" % (t, b[:50], s))


if __name__ == "__main__":
    main()
