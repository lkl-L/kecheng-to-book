# -*- coding: utf-8 -*-
"""示例：去品牌关联 + 把某一层方法论整章抽出、另成一册。

对 sec-md/<前缀>-*.md 逐章改写：
  1) 品牌字样全部改为中性表述（零品牌词）
  2) 被抽出的那层框架的自有术语自正文去除；专论段落抽出，汇成姊妹册
  3) 正文的方法论层级相应改写（"以 X 为主" → "以 Y 为主"）

思路：正文（读者看的）只留主干；被抽走的整段不丢，另存进姊妹册。
本脚本可重入：跑坏了先 `rm -rf sec-md && cp -r sec-md.bak-<改动名> sec-md` 再重跑。

用法：把下面 6 张表按自己的项目填好，再运行。表里每一条都是
「原文 → 改写后」，原文必须能在稿子里唯一命中（拿不准就先 grep 一遍）。
"""
import glob
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

PREFIX = "bz"                # 章节稿前缀：sec-md/<PREFIX>-*.md
N_CHAPTERS = 22              # 章节数，用于自检（防误删/漏读）
FRAME = "【框架术语】"        # 要抽走的那层框架的名字，用于统计残留
COMPANION = "【姊妹册书名】"   # 抽出的内容汇编成的册名

# ============================================================
# 一、品牌词 → 中性表述（按顺序执行，长者优先）
# ============================================================
BRAND = [
    ("《书名》　讲授 · 某体系入门读本", "整理者　整理"),
    ("【品牌名】", "本门"),
    ("【机构名】", "本门"),
    ("【讲授者】", "老师"),
    # 按你的项目补：书名副标题、编者说明、附录标题与说明、
    # 以及本领域里其他与品牌绑定的固定表述，都要在这里覆盖。
]

# ============================================================
# 二、被抽走框架的自有术语：句内改写（在 BRAND 之后执行）
# ============================================================
FRAME_FIX = [
    ("（三）【框架术语】", "（三）中性小标题"),
    ("以【框架术语】为主要方法", "以主干方法为主"),
    # 每一条都要核对该句在稿子里唯一；宽泛的词（只出现几个字）别放进来，
    # 否则会误伤正常叙述。
]

# ============================================================
# 三、整段改写（旧段 → 新段）
#     句内替换搞不定的长段落（如"方法论层级"的整段论述）贴在这里
# ============================================================
REWRITE_BLOCKS = [
    # (
    #     "旧段全文……",
    #     "改写后的新段全文……",
    # ),
]

# ============================================================
# 四、整段抽出（正文删去，只进姊妹册）
#     前半是键名（随便起，只用于姊妹册编排），后半是**原文唯一前缀**
# ============================================================
EXTRACT = [
    ("D1", "这套体系的基本法则，就是【框架术语】"),
    ("D2", "……"),
]

# ============================================================
# 五、单独抽出的整行（小标题等，正文删去）
# ============================================================
DROP_LINES = [
    "（一）【框架术语】是这套体系的基本法则",
]

# ============================================================
# 六、辑要里另收、但正文只是改写不删的段落
# ============================================================
EXTRA_FOR_COMPANION = [
    ("J1", "……"),
]


def apply_pairs(text, pairs):
    """按顺序做字符串替换（长者优先，避免短词先截断长词）。"""
    for old, new in pairs:
        text = text.replace(old, new)
    return text


def main():
    files = sorted(glob.glob("sec-md/%s-*.md" % PREFIX))
    assert len(files) == N_CHAPTERS, (len(files), N_CHAPTERS)

    companion = {}          # 抽出的段落
    before = after = 0      # 框架词的残留统计

    for path in files:
        raw = open(path, encoding="utf-8").read().replace("\r\n", "\n")
        before += raw.count(FRAME)

        # 抽出段落先取原文（按唯一前缀定位到该行末）
        for key, prefix in EXTRACT + EXTRA_FOR_COMPANION:
            idx = raw.find(prefix)
            if idx == -1:
                continue
            end = raw.find("\n", idx)
            companion[key] = raw[idx:(end if end != -1 else len(raw))].strip()

        # 丢掉抽出的整段与整行（正文不要）
        lines = [
            ln for ln in raw.split("\n")
            if not any(p in ln for _, p in EXTRACT) and ln.strip() not in DROP_LINES
        ]
        text = "\n".join(lines)

        text = apply_pairs(text, BRAND)
        text = apply_pairs(text, FRAME_FIX)
        for old, new in REWRITE_BLOCKS:
            if old in text:
                text = text.replace(old, new)

        text = re.sub(r"\n{3,}", "\n\n", text)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text.rstrip() + "\n")
        after += text.count(FRAME)

    # ===== 生成姊妹册 =====
    def clean(s):
        return apply_pairs(s, BRAND)

    out = [
        "# %s" % COMPANION,
        "",
        "整理者　整理",
        "",
        "—— 说明 ——",
        "",
        "本册是从主干书正文中单独抽出的论述，正文只留主干。"
        "所辑各节照原稿收录，只对人名、地名作了泛化，术语作了统一。",
        "",
    ]
    sections = [
        ("一、【框架术语】的提出", ["D1", "D2"]),
        ("二、它与主干方法的关系", ["J1"]),
    ]
    for title, keys in sections:
        out.append("## %s" % title)
        out.append("")
        for k in keys:
            if k in companion:
                out.append(clean(companion[k]))
                out.append("")
    text = "\n".join(out).rstrip() + "\n"
    with open("%s.md" % COMPANION, "w", encoding="utf-8") as fh:
        fh.write(text)

    # ===== 自检 =====
    print("改写前：%s %d 处 → 改写后 %d 处" % (FRAME, before, after))
    print("姊妹册 %d 字" % len(re.sub(r"\s", "", text)))
    miss = [k for k, _ in EXTRACT + EXTRA_FOR_COMPANION if k not in companion]
    if miss:
        print("!! 未抽到的段落：%s" % miss)
    if after:
        for path in files:
            t = open(path, encoding="utf-8").read()
            for i, ln in enumerate(t.split("\n"), 1):
                if FRAME in ln:
                    print("  残留 %s:%d  %s" % (os.path.basename(path), i, ln[:120]))


if __name__ == "__main__":
    main()
