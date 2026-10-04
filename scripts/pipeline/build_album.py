# -*- coding: utf-8 -*-
"""把筛选出的图片+图说汇编成《图册》docx。

输入: figures/<课程>/captions_all.md  格式见 build_album 里解析规则
输出: transcribe/book/<书名>图册.docx

captions_all.md 每个图块格式:
### 图 2-3
- 讲次: 2
- 标题: 卫星图：某某龙局
- 时间: 08:15-12:40
- 文件: figures/qjj/lesson02/slides/s012_xxx.jpg
- 图说: 这里写一段完整图说，可多行，直到空行结束

块与块之间用空行分隔。
"""
import os
import re
import sys

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

BASE = r"<项目根>"


def parse_captions(md_path):
    figs = []
    cur = None
    for raw in open(md_path, encoding="utf-8"):
        line = raw.rstrip("\n")
        m = re.match(r"^###\s*(.+)$", line)
        if m:
            if cur:
                figs.append(cur)
            cur = {"编号": m.group(1).strip()}
            continue
        if cur is None:
            continue
        m2 = re.match(r"^-\s*(讲次|标题|时间|文件):\s*(.*)$", line)
        if m2:
            cur[m2.group(1)] = m2.group(2).strip()
        elif line.startswith("- 图说:"):
            cur["图说"] = [line[len("- 图说:"):].strip()]
        elif "图说" in cur and isinstance(cur["图说"], list):
            if line.strip():
                cur["图说"].append(line.strip())
            else:
                cur["图说"] = "\n".join(cur["图说"])
    if cur:
        if isinstance(cur.get("图说"), list):
            cur["图说"] = "\n".join(cur["图说"])
        figs.append(cur)
    return [f for f in figs if f.get("文件")]


def build(md_path, out_docx, book_title, intro):
    figs = parse_captions(md_path)
    doc = Document()
    t = doc.add_heading(book_title, level=1)
    p = doc.add_paragraph()
    r = p.add_run(intro)
    r.font.size = Pt(10.5)
    r.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

    last_lesson = None
    ok, miss = 0, 0
    for f in figs:
        if f.get("讲次") != last_lesson:
            last_lesson = f.get("讲次")
            doc.add_heading(f"第{last_lesson}讲", level=2)
        img = os.path.join(BASE, f["文件"])
        if not os.path.exists(img):
            print("!! 图片缺失:", img)
            miss += 1
            continue
        doc.add_picture(img, width=Inches(6.2))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap = doc.add_paragraph()
        rc = cap.add_run(f"{f['编号']}　{f.get('标题','')}")
        rc.bold = True
        rc.font.size = Pt(11)
        meta = doc.add_paragraph()
        rm = meta.add_run(f"（视频 {f.get('时间','')}）")
        rm.font.size = Pt(9)
        rm.font.color.rgb = RGBColor(0x88, 0x88, 0x88)
        body = doc.add_paragraph()
        rb = body.add_run(f.get("图说", ""))
        rb.font.size = Pt(10.5)
        ok += 1

    doc.save(out_docx)
    print(f"图册完成: {out_docx}  图片 {ok} 张, 缺失 {miss}")


if __name__ == "__main__":
    md = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE, "figures/qjj/captions_all.md")
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(BASE, "book/图文课图册.docx")
    title = sys.argv[3] if len(sys.argv) > 3 else "《地理千金赋》精讲图册"
    intro = sys.argv[4] if len(sys.argv) > 4 else (
        "本图册收录《地理千金赋》九讲课程视频中出现的图例——卫星地形图、沙盘示意、"
        "书影与板书，按讲次编排。每图配时间点，可与《图文课实录》对照阅读；"
        "正文相应位置亦标注了\"参见图册\"。")
    build(md, out, title, intro)
