# -*- coding: utf-8 -*-
"""测试 RapidOCR 在讲义扫描件上的效果与速度。"""
import os
import sys
import time
import numpy as np
import pymupdf
from PIL import Image
from rapidocr_onnxruntime import RapidOCR

sys.stdout.reconfigure(encoding="utf-8")
PWD = "00000000"
engine = RapidOCR()

CASES = [
    (r"<资料目录>\书籍整理\基础-第五版.pdf", [10, 60, 150]),
    (r"<资料目录>\书籍整理\2019年7月课堂记录.pdf", [15, 60]),
    (r"<资料目录>\书籍整理\2018年11月.pdf", [20, 80]),
]


def ocr_page(page, dpi=200):
    pix = page.get_pixmap(dpi=dpi)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    t0 = time.time()
    res, _ = engine(np.array(img))
    dt = time.time() - t0
    if not res:
        return "", dt
    return "\n".join(x[1] for x in res), dt


for path, pages in CASES:
    print("=" * 70)
    print(os.path.basename(path))
    d = pymupdf.open(path)
    if d.needs_pass:
        d.authenticate(PWD)
    for i in pages:
        if i >= len(d):
            continue
        txt, dt = ocr_page(d[i])
        print("--- p%d  %.1fs  %d 字 ---" % (i + 1, dt, len(txt.replace("\n", ""))))
        print(txt[:420].replace("\n", " | "))
        print()
    d.close()
