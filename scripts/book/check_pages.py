# -*- coding: utf-8 -*-
"""用 Word COM 打开排好版的 docx，报告总页数与目录/卷首页的实际页码，并导出 PDF 预览。"""
import os
import sys
import win32com.client as win32

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
DOCX = os.path.join(BASE, "微课堂实录.docx")
PDF = os.path.join(BASE, "微课堂实录.pdf")

word = win32.Dispatch("Word.Application")
word.Visible = False
word.DisplayAlerts = 0
try:
    doc = word.Documents.Open(DOCX, ReadOnly=True, AddToRecentFiles=False)
    doc.Repaginate()
    print("总页数:", doc.ComputeStatistics(2))

    rows = []
    n = doc.Paragraphs.Count
    for i in range(1, n + 1):
        rng = doc.Paragraphs(i).Range
        t = rng.Text.replace("\r", "").replace("\x07", "").strip()
        if not t:
            continue
        if t == "目　　录" or t in ("编 者 说 明",) or (t.startswith("卷") and "　" in t and len(t) < 40):
            rows.append((rng.Information(3), t[:36]))
    for pg, t in rows:
        print("  p%-4d %s" % (pg, t))

    try:
        doc.ExportAsFixedFormat(PDF, 17)
        print("PDF ->", PDF)
    except Exception as e:  # noqa: BLE001
        print("PDF 导出失败:", e)
    doc.Close(False)
finally:
    word.Quit()
