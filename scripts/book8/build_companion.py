# -*- coding: utf-8 -*-
"""示例：从原稿备份里把某一层论述回捞出来，汇编成姊妹册。

背景：主线书（主干）已把相关章节抽去、术语改成以主干方法为主；
本脚本从**最早的备份稿**里按"原文唯一前缀"把那一层论述回捞出来，
照原文留档，独立成一册，走同一套排版流程。

为什么从备份稿取、而不是从当前正文取：正文那一层已被改写/删除，
姊妹册要的是**原文**，所以取备份。

用法：把下面几张表按自己的项目填好，再运行。
  - 单段：按"行首唯一片段"定位到该行末
  - 整节/整小节：按标题定位，到下一个同级标题为止
  - 汇编完自动调 reparagraph.process_text 做一次再分段（只动换行）
"""
import glob
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

SRC = "sec-md.bak-<改动名>"     # 最早的那份备份（改动前的原稿）
SRC_PREFIX = "bz"               # 备份稿文件名格式：<SRC>/<SRC_PREFIX>-*.md
BOOK = "姊妹册"                  # 成品册名

SEC = re.compile(r"^[一二三四五六七八九十]{1,3}、[^。，；：]{0,30}$")
SUB = re.compile(r"^（[一二三四五六七八九十]{1,3}）[^。]{0,30}$")

# 与 strip_brand_extract.py 同一张去表（姊妹册也要清品牌）
BRAND = [
    ("【品牌名】", "本门"),
    ("【讲授者】", "老师"),
    # 按你的项目补
]

# ---- 以原文唯一前缀定位的单段：键 → 行内唯一片段 ----
P = {
    "c1_总纲": "这套体系的基本法则，就是【框架术语】",
    "c1_法则": "……（原文唯一前缀）……",
    "c2_应用": "……",
}

# ---- 整节 / 整小节抽取：(键, 文件, 标题, 是否在小节处即止) ----
SECT = [
    ("s1_某节", "bz-002.md", "四、【某节标题】", False),
    ("s2_某小节", "bz-004.md", "（一）【某小节标题】", True),
]

# ---- 单段抽取：(键, 文件, 行首) ----
PARA = [
    ("p1_某段", "bz-004.md", "……（该行开头）……"),
]

# ---- 口诀／韵文（原在全书附录中，随内容一并移入本册）----
VERSE = [
    "……口示例……",
    "……口示例……",
]

# ---- 姊妹册的章节编排：标题 → 用哪些键 ----
SECTIONS = [
    ("一、【框架术语】的提出", ["c1_总纲", "c2_应用"]),
    ("二、它与主干方法的关系", ["c1_法则"]),
    ("三、这一层的若干专论", ["s1_某节", "s2_某小节", "p1_某段"]),
]


def clean(s):
    for old, new in BRAND:
        s = s.replace(old, new)
    return s


def grab_section(raw, title, stop_at_sub):
    """按标题抓一整节；stop_at_sub=True 时遇小节标题也停（只抓一节内的一小节）。"""
    lines = raw.split("\n")
    start = None
    for i, l in enumerate(lines):
        if l.strip() == title:
            start = i
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start + 1, len(lines)):
        s = lines[j].strip()
        if SEC.match(s) or (stop_at_sub and SUB.match(s)):
            end = j
            break
    while end - 1 > start and lines[end - 1].strip() == "":
        end -= 1
    return "\n".join(lines[start + 1:end]).strip()


def grab_para(raw, prefix):
    for l in raw.split("\n"):
        if l.startswith(prefix):
            return l.strip()
    return None


def main():
    pool = {}

    # 单段
    for path in sorted(glob.glob(os.path.join(SRC, "%s-*.md" % SRC_PREFIX))):
        raw = open(path, encoding="utf-8").read().replace("\r\n", "\n")
        for key, prefix in P.items():
            if key in pool:
                continue
            idx = raw.find(prefix)
            if idx == -1:
                continue
            end = raw.find("\n", idx)
            if end == -1:
                end = len(raw)
            pool[key] = raw[idx:end].strip()

    # 整节 / 小节
    for key, fname, title, stop_sub in SECT:
        raw = open(os.path.join(SRC, fname), encoding="utf-8").read().replace("\r\n", "\n")
        t = grab_section(raw, title, stop_sub)
        if t:
            pool[key] = t
        else:
            print("!! 未取到整节 %s @ %s" % (key, fname))

    # 单段（整行）
    for key, fname, prefix in PARA:
        raw = open(os.path.join(SRC, fname), encoding="utf-8").read().replace("\r\n", "\n")
        t = grab_para(raw, prefix)
        if t:
            pool[key] = t
        else:
            print("!! 未取到单段 %s @ %s" % (key, fname))

    missing = [k for _, keys in SECTIONS for k in keys if k not in pool]
    if missing:
        print("!! 未取到：%s" % missing)

    out = []
    out.append("# 《%s》" % BOOK)
    out.append("")
    out.append("整理者　整理")
    out.append("")
    out.append("—— 【副标题】 ——")
    out.append("")
    out.append(
        "本册是从主线书原稿中单独抽出的论述，另成一册。原稿有一层以【框架术语】为总纲的方法论，"
        "这一层自成一套体系，与以主干方法为主的正文不宜混编，故抽出别为一册，与主线书并行。"
        "正文回到主干本身；凡涉及这一层的论述，正文一律精简，详论尽在本册。"
        "所辑各节均照原稿收录，只对人名、地名作了泛化，术语与称谓作了统一。"
    )
    out.append("")

    for title, keys in SECTIONS:
        out.append("## %s" % title)
        out.append("")
        for k in keys:
            if k in pool:
                t = clean(pool[k])
                t = re.sub(r"^[⑥⑦⑧⑨]", "", t)      # 去掉从正文带来的序号
                out.append(t)
                out.append("")

    if VERSE:
        out.append("## 附　口诀")
        out.append("")
        out.append("原稿附录的口诀里有若干条属于这一层，随内容一并移入本册。")
        out.append("")
        for line in VERSE:
            out.append(line)
            out.append("")

    out.append("## 结语")
    out.append("")
    out.append(
        "这一层义理，说到底只有一句话：【一句话总纲】。"
        "它与主干方法一致时，主干方法才是准确的；二者相左时，以实际实况为准，不可偏执。"
        "本册所辑，即以此义为纲，读者与正文参看，自明其法。"
    )
    text = "\n".join(out).rstrip() + "\n"

    # 与正文同一套再分段规则（提行引文/韵文、裂开并列项、切长段），只动换行不改字
    if BASE not in sys.path:
        sys.path.insert(0, BASE)
    import reparagraph as _rp
    n_before = len([l for l in text.split("\n") if l.strip()])
    text, _st = _rp.process_text(text)
    n_after = len([l for l in text.split("\n") if l.strip()])

    with open("%s.md" % BOOK, "w", encoding="utf-8") as fh:
        fh.write(text)
    print("《%s》%d 字（分段 %d → %d 行，提行 %d 条）"
          % (BOOK, len(re.sub(r"\s", "", text)), n_before, n_after, _st.get("cite", 0)))


if __name__ == "__main__":
    main()
