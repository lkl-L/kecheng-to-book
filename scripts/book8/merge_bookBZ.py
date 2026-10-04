# -*- coding: utf-8 -*-
"""示例：把按章整理的 sec-md 稿，按「编 → 章」三级骨架合并成全书 markdown。

结构：书名 H1 / 编 H2 / 章 H3。
每份章节稿首行是 `## 章名`，合并时降为 `### 第N章　章名`，章内小标（`一、`/`（一）`）保持纯文本。

**VOLUMES 是骨架的唯一事实来源**：改结构先改这里，再改排版脚本的书单。
用法：把 VOLUMES / INTRO / APPENDIX 按自己的项目填好，再运行。
"""
import glob
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

BOOK = "【书名】"
SEC_PREFIX = "bz"          # 章节稿文件名格式：sec-md/<SEC_PREFIX>-NNN.md
N_CHAPTERS = 22            # 章数，用于自检（防漏稿）

# ---- 骨架：(编名, 编前说明, [章号…]) ----
# 所有编的章号并集必须 = 1..N 且无重复（下 main 里会 assert）。
VOLUMES = [
    ("第一编　【编名】", "本编……（排在扉页下半部的编前说明）", [1, 2, 3, 4, 5]),
    ("第二编　【编名】", "……", [6, 7, 8, 9, 10]),
    ("第三编　【编名】", "……", [11, 12, 13, 14]),
    ("第四编　【编名】", "……", [15, 16, 17, 18]),
    ("第五编　【编名】", "……", [19, 20, 21, 22]),
]

INTRO = (
    "……（编者说明：本书的由来、体例、材料来源与整理原则）……"
)
INTRO2 = (
    "……（第二段：全书以什么为主线、原稿哪些内容被精简或移入姊妹册）……"
)

# ---- 附录（可选）：总纲口诀、术语表等 ----
APP_TITLE = "附录　【口诀名】"
APP_NOTE = "正文之外，另将……附录于后，以便诵读印证。"
APPENDIX = [
    "……口诀一……",
    "……口诀二……",
]


def main():
    files = sorted(glob.glob("sec-md/%s-*.md" % SEC_PREFIX))
    if len(files) != N_CHAPTERS:
        print("!! 章节数不为 %d：%d" % (N_CHAPTERS, len(files)))

    by_num = {}
    for f in files:
        m = re.search(r"%s-(\d+)\.md$" % SEC_PREFIX, f)
        if m:
            by_num[int(m.group(1))] = f

    # 骨架自检：章号并集必须覆盖 1..N 且无重复
    nums = [n for _, _, ns in VOLUMES for n in ns]
    assert sorted(nums) == list(range(1, N_CHAPTERS + 1)), (sorted(nums), N_CHAPTERS)

    out = []
    out.append("# 《%s》" % BOOK)
    out.append("")
    out.append("【副标题】")
    out.append("")
    out.append("—— 【题记】 ——")
    out.append("")
    out.append(INTRO)
    out.append("")
    out.append(INTRO2)
    out.append("")

    total = 0
    for vol_name, vol_note, ns in VOLUMES:
        out.append("## %s" % vol_name)
        out.append("")
        out.append(vol_note)
        out.append("")
        vn = 0
        for n in ns:
            p = by_num.get(n)
            if not p:
                print("!! 缺章节 %s-%03d" % (SEC_PREFIX, n))
                continue
            t = open(p, encoding="utf-8").read().replace("\r\n", "\n").strip()
            lines = t.split("\n")
            head = lines[0]
            assert head.startswith("## "), "%s 首行不是 ## 标题" % p
            body = "\n".join(lines[1:]).strip()
            # 去掉可能残留的三级标题（章内小标一律用纯文本）
            body = re.sub(r"^### .+$", "", body, flags=re.M).strip()
            out.append("### %s" % head[3:].strip())
            out.append("")
            out.append(body)
            out.append("")
            vn += len(re.sub(r"\s", "", body))
        print("%-24s %6d 字" % (vol_name, vn))
        total += vn

    # ===== 附录 =====
    if APPENDIX:
        out.append("## 附　录")
        out.append("")
        out.append(APP_NOTE)
        out.append("")
        out.append("### %s" % APP_TITLE)
        out.append("")
        for line in APPENDIX:
            out.append(line)
            out.append("")
        total += len(re.sub(r"\s", "", "".join(APPENDIX)))

    text = "\n".join(out).rstrip() + "\n"
    with open("%s.md" % BOOK, "w", encoding="utf-8") as fh:
        fh.write(text)
    print("-" * 40)
    print("全书正文合计 %d 字" % total)
    print("md 文件大小 %.1f KB" % (os.path.getsize("%s.md" % BOOK) / 1024))
    # 结构自检
    ls = text.split("\n")
    print("H1:%d H2:%d H3:%d" % (len([l for l in ls if l.startswith("# ")]),
                                 len([l for l in ls if l.startswith("## ")]),
                                 len([l for l in ls if l.startswith("### ")])))


if __name__ == "__main__":
    main()
