# -*- coding: utf-8 -*-
"""批量用 Word COM 验证各书分页并导出 PDF。
用法：python check_pages_all.py [书名1 书名2 ...]
"""
import os
import sys
import win32com.client as win32

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
DEFAULT = [
    "经典课实录",
    "赋文课实录",
    "图文课实录",
    "【书名】",
    "实战课实录",
    "【书名】",
]

word = win32.Dispatch("Word.Application")
word.Visible = False
word.DisplayAlerts = 0
try:
    for name in (sys.argv[1:] or DEFAULT):
        docx = os.path.join(BASE, name + ".docx")
        pdf = os.path.join(BASE, name + ".pdf")
        doc = word.Documents.Open(docx, ReadOnly=True, AddToRecentFiles=False)
        try:
            doc.Repaginate()
            total = doc.ComputeStatistics(2)
            heads = []
            for i in range(1, doc.Paragraphs.Count + 1):
                rng = doc.Paragraphs(i).Range
                t = rng.Text.replace("\r", "").replace("\x07", "").strip()
                if not t:
                    continue
                if rng.ParagraphFormat.OutlineLevel <= 3:      # 各级标题
                    heads.append((rng.Information(3), rng.ParagraphFormat.OutlineLevel, t[:30]))
            print("=" * 66)
            print("%s  共 %d 页  （标题 %d 个）" % (name, total, len(heads)))
            for pg, lv, t in heads[:8]:
                print("   p%-5d L%d  %s" % (pg, lv, t))
            if len(heads) > 8:
                pg, lv, t = heads[-1]
                print("   ...  末节 p%-5d L%d  %s" % (pg, lv, t))
            try:
                doc.ExportAsFixedFormat(pdf, 17)
                print("   PDF -> %s  %d KB" % (os.path.basename(pdf),
                                               os.path.getsize(pdf) // 1024))
            except Exception as e:  # noqa: BLE001
                print("   PDF 导出失败:", e)
        finally:
            doc.Close(False)
finally:
    word.Quit()
