# -*- coding: utf-8 -*-
"""用 Word COM 打开各书：更新所有域（目录页码/页脚页码）→ 保存 docx → 导出 PDF。

用法：python update_toc.py [书名1 书名2 ...]   （不带参数=全部）
"""
import os
import sys
import time
import win32com.client as win32

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
BOOKS = [
    "经典课实录",
    "赋文课实录",
    "图文课实录",
    "日课课实录",
    "实战课实录",
    "微课堂实录",
]
WD_UPDATE_TOC = 2          # wdUpdateToc
WD_FIELD_PAGE = -1


def main():
    names = sys.argv[1:] or BOOKS
    word = win32.Dispatch("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    try:
        for name in names:
            docx = os.path.join(BASE, name + ".docx")
            pdf = os.path.join(BASE, name + ".pdf")
            t0 = time.time()
            doc = word.Documents.Open(docx, AddToRecentFiles=False)
            try:
                # 1) 更新目录（隐含重排页）
                try:
                    doc.TablesOfContents(1).Update()
                except Exception as e:                       # noqa: BLE001
                    print("   目录更新异常:", str(e)[:80])
                # 2) 更新所有页脚/正文域
                for hf in (1, 2, 3):                             # 页眉/页脚/首页脚
                    try:
                        rng = doc.StoryRanges(hf)
                        while rng is not None:
                            rng.Fields.Update()
                            rng = rng.NextStoryRange
                    except Exception:                            # noqa: BLE001
                        pass
                doc.Repaginate()
                total = doc.ComputeStatistics(2)
                # 3) 统计目录条目数与页码，抽前几条核对
                rows = []
                if doc.TablesOfContents.Count >= 1:
                    toc = doc.TablesOfContents(1).Range
                    for i in range(1, toc.Paragraphs.Count + 1):
                        t = toc.Paragraphs(i).Range.Text.replace("\r", "").strip()
                        if t and t != "目　　录":
                            rows.append("      " + t[:56])
                # 4) 保存 docx（页脚域已算好；目录域保持可更新）
                doc.Save()
                doc.ExportAsFixedFormat(pdf, 17)
                print("%-26s %3d 页  目录 %2d 条  %.0fs" %
                      (name, total, len(rows), time.time() - t0))
                for r in rows[:6]:
                    print(r)
                if len(rows) > 6:
                    print("      ...")
                    print(rows[-1])
            finally:
                doc.Close(0)
    finally:
        word.Quit()


if __name__ == "__main__":
    main()
