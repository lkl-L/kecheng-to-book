# -*- coding: utf-8 -*-
"""《基础教程》全书合规校验"""
import glob, re, os, sys

sys.stdout.reconfigure(encoding="utf-8")
os.chdir(os.path.dirname(os.path.abspath(__file__)))

fs = sorted(glob.glob("sec-md/bz-*.md"))
print("章节稿: %d 份" % len(fs))
tot = 0
bad = 0
for f in fs:
    t = open(f, encoding="utf-8").read()
    n = len(re.sub(r"\s", "", t))
    tot += n
    h1 = len(re.findall(r"^## ", t, re.M))
    h2 = len(re.findall(r"^### ", t, re.M))
    bold = t.count("**")
    lst = len(re.findall(r"^\s*[-*]\s", t, re.M)) + len(re.findall(r"^\s*\d+[.、]\s", t, re.M))
    typo = [w for w in TYPO_WORDS if w in t]
    rep = [w for w in ["记者", "据报道", "本文认为", "综上所述", "值得一提的是"] if w in t]
    hd = re.search(r"^## .+$", t, re.M)
    flag = ""
    if h1 != 1 or h2 or bold or lst or typo or rep or not hd:
        flag = "  <<< " + str({"H2": h1, "H3": h2, "bold": bold, "list": lst,
                              "typo": typo, "rep": rep, "head": hd.group(0) if hd else None})
        bad += 1
    print("%-12s %6d字  标题: %s%s" % (os.path.basename(f), n, (hd.group(0)[3:20] if hd else "缺"), flag))
print("合计 %d 字，异常 %d 份" % (tot, bad))

txt = "".join(open(f, encoding="utf-8").read() for f in fs)
print("半角双引号: %d  中文左引号: %d  中文右引号: %d  半角单引号: %d  中文单引号: %d/%d"
      % (txt.count('"'), txt.count("\u201c"), txt.count("\u201d"),
         txt.count("'"), txt.count("\u2018"), txt.count("\u2019")))

print()
print("=== OCR 素材 ===")
for f in sorted(glob.glob("materials-ocr/*")):
    t = open(f, encoding="utf-8", errors="ignore").read()
    print("%-40s %4d 页  %7d 字" % (os.path.basename(f), len(re.findall(r"<<<PAGE:", t)),
                                    len(re.sub(r"\s|<<<PAGE:\d+>>>", "", t))))
