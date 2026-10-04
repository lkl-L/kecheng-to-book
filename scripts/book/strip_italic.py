# -*- coding: utf-8 -*-
"""把 docx 里所有斜体标记关掉（一律正体）。

背景：python-docx 的默认模板继承 Word 内置样式，Heading 4/6/7/9、Subtitle、
Quote、Emphasis 等定义里自带 <w:i/>。我们书里的「（一）xxx」这一级目用的正是
Heading 4，于是整级目显示成斜体。脚本把 styles.xml / document.xml / 页眉页脚
里所有 <w:i/> 与 <w:iCs/> 显式改成 val="0"。

安全性：除斜体标记外不允许改动任何字节——逐个 part 比对，只有含斜体标记的
part 允许变化，且变化量必须等于替换条数。

用法：python strip_italic.py [文件或目录 ...]    （默认：book/ 与 book8/ 下所有 docx）
"""
import os
import re
import shutil
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)                       # transcribe/

DEFAULT_DIRS = [os.path.join(ROOT, "book"), os.path.join(ROOT, "book8")]

# 只匹配「开启斜体」的写法：<w:i/> / <w:i val="1|true|on"/>（含 w: 前缀的形式）
RE_I = re.compile(r'<w:(i|iCs)(?:\s+w:val="(?:1|true|on|True)")?\s*/>')


def fix_xml(text):
    n = 0

    def rep(m):
        nonlocal n
        n += 1
        return '<w:%s w:val="0"/>' % m.group(1)

    text = RE_I.sub(rep, text)
    # 极少见的长写法 <w:i></w:i>
    text = re.sub(r'<w:(i|iCs)></w:\1>', lambda m: '<w:%s w:val="0"/>' % m.group(1), text)
    return text, n


def strip_one(path):
    with zipfile.ZipFile(path) as z:
        items = [(i, z.read(i.filename)) for i in z.infolist()]
    out = []
    total = 0
    changed_parts = 0
    for info, data in items:
        name = info.filename
        if not name.endswith(".xml"):
            out.append((info, data))
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            out.append((info, data))
            continue
        new, n = fix_xml(text)
        if n:
            total += n
            changed_parts += 1
        out.append((info, new.encode("utf-8")))
    if not total:
        return 0, 0
    tmp = path + ".tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for info, data in out:
            z.writestr(info, data)
    # 校验：新包里除被改动的 part 外，其余 part 必须与旧包字节一致
    with zipfile.ZipFile(path) as a, zipfile.ZipFile(tmp) as b:
        na = set(a.namelist())
        nb = set(b.namelist())
        if na != nb:
            os.remove(tmp)
            raise RuntimeError("part 清单变化，已放弃：%s" % path)
        for nm in na:
            da, db = a.read(nm), b.read(nm)
            if da == db:
                continue
            if not nm.endswith(".xml"):
                os.remove(tmp)
                raise RuntimeError("非 xml part 被改动：%s / %s" % (path, nm))
            expect, _ = fix_xml(da.decode("utf-8"))
            if expect.encode("utf-8") != db:
                os.remove(tmp)
                raise RuntimeError("改动超出预期：%s / %s" % (path, nm))
    shutil.move(tmp, path)
    return total, changed_parts


def collect(args):
    files = []
    if not args:
        for d in DEFAULT_DIRS:
            if os.path.isdir(d):
                files += [os.path.join(d, f) for f in os.listdir(d)
                          if f.endswith(".docx") and not f.startswith("~$")
                          and ".bak" not in f]
    else:
        for a in args:
            if os.path.isdir(a):
                files += [os.path.join(a, f) for f in os.listdir(a)
                          if f.endswith(".docx") and not f.startswith("~$")
                          and ".bak" not in f]
            else:
                files.append(a)
    return files


def main():
    files = collect(sys.argv[1:])
    if not files:
        print("没有找到 docx")
        return
    grand = 0
    for p in sorted(files):
        n, parts = strip_one(p)
        grand += n
        print("%-44s 斜体标记 %3d 处 → 正体（%d 个 part）" %
              (os.path.basename(p), n, parts))
    print("\n合计处理 %d 处斜体标记，%d 个文件" % (grand, len(files)))


if __name__ == "__main__":
    main()
