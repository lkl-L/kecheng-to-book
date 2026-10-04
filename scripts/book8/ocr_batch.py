# -*- coding: utf-8 -*-
"""批量 OCR 讲义扫描件（印刷体 PDF，无文字层），输出到 materials-ocr/。

· 自动用文件名里的数字密码解锁（791780048）
· 每页 200dpi 渲染 → RapidOCR → 按行拼接 → 按文件存 txt
· 断点续做：已存在且字数 > 0 的文件跳过；单文件内按页缓存（.part）
"""
import os
import re
import sys
import time
import numpy as np
import pymupdf
from PIL import Image
from rapidocr_onnxruntime import RapidOCR

sys.stdout.reconfigure(encoding="utf-8")
SRC = r"<资料目录>"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "materials-ocr")
os.makedirs(OUT, exist_ok=True)
PWD = "791780048"

# 要 OCR 的扫描件（手写笔记排除）
TARGETS = [
    r"八字\书籍整理\基础-第五版.pdf",
    r"八字\书籍整理\2017年11月密码：791780048.pdf",
    r"八字\书籍整理\2018年3月密码：791780048.pdf",
    r"八字\书籍整理\2018年5月密码：791780048.pdf",
    r"八字\书籍整理\2018年6月密码：791780048.pdf",
    r"八字\书籍整理\2018年11月.pdf",
    r"八字\书籍整理\2018年12月密码：791780048.pdf",
    r"八字\书籍整理\2019年2月深圳班讲座.pdf",
    r"八字\书籍整理\2019年7月深圳班.pdf",
    r"基础\2017年惠州.pdf",
    r"基础\2018年5月.pdf",
]

engine = RapidOCR()


def ocr_pdf(path, out_path):
    d = pymupdf.open(path)
    if d.needs_pass:
        if not d.authenticate(PWD):
            print("!! 解锁失败", os.path.basename(path))
            d.close()
            return
    n = len(d)
    part = out_path + ".part"
    done = set()
    parts = []
    if os.path.exists(part):
        prev = open(part, encoding="utf-8").read()
        m = re.findall(r"<<<PAGE:(\d+)>>>", prev)
        done = set(int(x) for x in m)
        parts = [prev]
        print("  续做: 已完成 %d 页" % len(done))
    t0 = time.time()
    for i in range(n):
        if i in done:
            continue
        try:
            pix = d[i].get_pixmap(dpi=200)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            res, _ = engine(np.array(img))
            txt = "\n".join(x[1] for x in res) if res else ""
        except Exception as e:  # noqa: BLE001
            txt = ""
            print("   !! p%d 失败 %s" % (i + 1, str(e)[:40]))
        parts.append("<<<PAGE:%d>>>\n%s\n" % (i, txt))
        if (i + 1) % 20 == 0 or i == n - 1:
            open(part, "w", encoding="utf-8").write("".join(parts))
            el = time.time() - t0
            rate = (i + 1 - len(done)) / el if el > 0 else 0
            eta = (n - i - 1) / rate / 60 if rate > 0 else 0
            print("   %d/%d 页  %.1fs/页  剩余约 %.0f 分钟" %
                  (i + 1, n, el / max(i + 1 - len(done), 1), eta))
    d.close()
    final = "".join(parts)
    open(out_path, "w", encoding="utf-8").write(final)
    if os.path.exists(part):
        os.remove(part)
    clean = len(re.sub(r"\s|<<<PAGE:\d+>>>", "", final))
    print("   DONE %s  %d 页  %d 字  %.0f 分钟" %
          (os.path.basename(out_path), n, clean, (time.time() - t0) / 60))


def main():
    t_all = time.time()
    total_pages = 0
    for rel in TARGETS:
        src = os.path.join(SRC, rel)
        base = os.path.splitext(os.path.basename(src))[0]
        base = base.replace("密码：791780048", "").replace("密码:791780048", "")
        out = os.path.join(OUT, base + ".txt")
        if os.path.exists(out) and os.path.getsize(out) > 500:
            print("跳过（已完成）", base)
            continue
        if not os.path.exists(src):
            print("!! 缺文件", rel)
            continue
        print("=" * 68)
        print("OCR:", base)
        ocr_pdf(src, out)
    print("\n全部完成，用时 %.1f 小时" % ((time.time() - t_all) / 3600))


if __name__ == "__main__":
    main()
