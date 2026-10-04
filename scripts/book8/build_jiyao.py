# -*- coding: utf-8 -*-
"""从原稿备份 sec-md.bak-predao 中，把「道法自然」与「四时（四季／节气）」两系论述
汇编成《姊妹册》。

正文（《基础教程》）已把相关章节抽去、术语改为以理法为主；
本辑要则把原文照录留档，独立成一册。字样同样一律去除。
"""
import glob
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

SRC = "sec-md.bak-predao"
BOOK = "姊妹册"

SEC = re.compile(r"^[一二三四五六七八九十]{1,3}、[^。，；：]{0,30}$")
SUB = re.compile(r"^（[一二三四五六七八九十]{1,3}）[^。]{0,30}$")

# 与 strip_brand_extract.py 同一张去表
BRAND = [
    ("命理核心的核心", "看命的核心"),
    ("这套命理体系核心口诀", "命理要诀口诀"),
    ("这套命理体系", "命理体系"),
    ("命理的核心", "八字命理的核心"),
    ("命理", "八字命理"),
    ("举过两组例子", "书中举过两组例子"),
    ("讲土与金", "论土与金"),
    ("道法分自自然然法则和生存法则", "道法分自然法则和生存法则"),
]

# ---- 以原文唯一前缀定位的单段 ----
P = {
    # 第一章
    "c1_总纲": "这套命理体系的基本法则，就是道法自然四个字。八字是模拟个人的小自然小宇宙的",
    "c1_法则": "自然法则主要讲的是四季的变化、十二个月的变化、二十四节气的变化，只有把这三个变化弄得非常明白",
    "c1_四季": "自然法则首先指四季气象。四季是春、夏、秋、冬，按照这个顺序轮回",
    "c1_向阳": "自然法则还有向阳法则、吸引力法则、万物一体法则，核心是同气相求。",
    "c1_死活": "道法自然的第二个法则是生存法则，讲的就是死活的配置。",
    # 第二章
    "c2_总纲": "八字是模拟个人的小自然、小宇宙的，它的源代码就来自自然，所以算八字要回归到自然。这套命理体系的基本法则就是道法自然四个字。",
    "c2_道德经": "《道德经》讲，人法地，地法天，天法道，道法自然。这是天地运行的法则",
    "c2_应用": "如何把道法自然应用到演算八字？道法分自然法则和生存法则两部分。",
    "c2_偏执": "这里要纠正一个理法的偏执：理法讲生我者为印、为妈",
    # 第三章
    "c3_依据": "判断的依据只有四个字：道法自然。",
    # 第四章
    "c4_人法地": "古人说“人法地，地法天，天法道，道法自然”，地支这一层，就是“人法地”的那一层。",
    # 第五章
    "c5_配置": "十二个月每个月都有自己的道法自然的配置，配置就是六合、六冲。",
    "c5_节气": "二十四节气每一个节气需要的配置是不一样的，就看命局处于哪一个节气。",
    "c5_时宜": "要因时而变，因用而变，就是时宜。如冬季休息，春季播种",
    # 第六章
    "c6_五合": "天干五合是自然的配置，道法自然讲的就是气象配置、物象配置。",
    # 第八章
    "c8_冲": "六冲是道法自然的需要，是每个月道法自然的配置。",
    # 第十二章
    "c12_理法": "理法与道法自然一致时，这样的理法才是正确的理法、准确的理法；",
    "c12_十神": "十神在不同场合的运用，用最简单的四个字概括，就是道法自然。十神要符合道法自然",
    "c12_万能": "阴阳一定是相互对立、相互统一，最后达到平衡。人的命运跟时代而变",
    # 第十四章
    "c14_关系": "再说一遍道法与理法的关系。理法是理，是最基础的一层",
    "c14_服从": "四法之中，理法与生存法则一致时，这个理法才是正确的理法、准确的理法。",
    "c14_大运": "大运与原局的关系，有两条现成的法则：一是道法自然",
    "c14_摆正": "要把这几层关系摆正：道法自然是底盘，象法是主方法，理法是补充，技法是工具。",
    # 第十六章
    "c16_宪法": "⑥道法自然是算命的大纲，相当于宪法。在它之下有一组原则：",
    # 第十七章
    "c17_取象": "取象的根，说到底落在道法自然上。道德经讲，人法地，地法天",
}

# ---- 整节 / 整小节抽取：(键, 文件, 标题, 是否在小节处即止) ----
SECT = [
    ("s7_五行四季", "bz-002.md", "四、五行的四季状态", False),
    ("s8_天干四季", "bz-003.md", "三、天干五行属性在不同时空的状态", False),
    ("s9_十二月形态", "bz-004.md", "（一）十二个月的形态、状态", True),
    ("s10_四季旺衰", "bz-010.md", "二、四季的旺衰之气", False),
    ("s11_五行配置", "bz-010.md", "一、五行的季节配置", False),
    ("s12a_因时而变", "bz-002.md", "（五）因时而变，因用而变", True),
    ("s12b_时宜", "bz-002.md", "（六）时宜", True),
    ("s12c_转换以季节定", "bz-012.md", "（三）转换以季节定", True),
]

# ---- 单段抽取：(键, 文件, 行首) ----
PARA = [
    ("p方位四季", "bz-004.md", "十二地支又代表四季："),
    ("p花甲定季节", "bz-005.md", "运用六十花甲子看命局，第一步是定季节。"),
    ("p看命定季节", "bz-014.md", "看命局要定季节。"),
]

# ---- 四时口诀（原在全书附录中，随季节内容一并移入本册） ----
VERSE = [
    "大道乃至简，立春阳已进。",
    "春阳木气旺，春未阴气藏。",
    "立夏阳攀升，夏末木气藏。",
    "立秋阳至上，秋未火气藏。",
    "立冬阴攀升，冬末金气藏。",
    "一年三六五，节气二十四。",
    "放眼大自然，寻找真易理。",
]

SECTIONS = [
    ("一、什么是道法自然", ["c2_总纲", "c2_道德经", "c1_总纲", "c3_依据", "c4_人法地"]),
    ("二、道法自然如何用于演算", ["c1_法则", "c2_应用", "c2_偏执", "c16_宪法"]),
    ("三、道法自然与理法、技法、象法的关系", ["c14_关系", "c14_服从", "c14_大运", "c14_摆正"]),
    ("四、道法自然与十神", ["c12_十神", "c12_理法", "c12_万能"]),
    ("五、取象的根在道法自然", ["c17_取象"]),
    ("六、四季气象与生存法则", ["c1_四季", "c1_向阳", "c1_死活", "c6_五合", "c8_冲"]),
    ("七、五行的四季状态", ["s7_五行四季"]),
    ("八、天干在四季的形态", ["s8_天干四季"]),
    ("九、十二个月的形态与气量", ["s9_十二月形态"]),
    ("十、四季的旺衰之气", ["s10_四季旺衰"]),
    ("十一、五行配置与季节", ["s11_五行配置"]),
    ("十二、四时配置与天人合一", ["s12c_转换以季节定", "s12a_因时而变", "s12b_时宜",
                                     "c5_配置", "c5_节气", "c5_时宜", "p花甲定季节", "p看命定季节"]),
    ("十三、方位、月建与四季", ["p方位四季", "c4_人法地"]),
]


def clean(s):
    for old, new in BRAND:
        s = s.replace(old, new)
    s = s.replace("", "")
    return s


def grab_section(raw, title, stop_at_sub):
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
    for path in sorted(glob.glob(os.path.join(SRC, "bz-*.md"))):
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

    # 单段
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
    out.append("—— 命理总纲与四时辑要 ——")
    out.append("")
    out.append(
        "本册是从《基础教程》原稿中单独抽出的论述，另成一册。原稿有一层以「道法自然」为总纲的方法论："
        "它讲八字是模拟个人的小自然、小宇宙，讲自然法则与生存法则，讲四时的气象、十二个月与二十四节气的配置，"
        "并以此定命局的层次、大运的吉凶。这一层内容自成一套体系，与以理法为主干的正文不宜混编，"
        "故抽出别为一册，与《基础教程》并行。正文回到理法本身，以理法、技法、象法三法看命，以理法为主；"
        "凡涉及道法自然与四时气象的论述，正文一律精简，详论尽在本册。"
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

    # 四时口诀
    out.append("## 十四、四时口诀")
    out.append("")
    out.append(
        "原稿的附录口诀里，有两段是专讲四时的。这一层随四时内容一并移入本册，正文附录只留理法一脉的口诀。"
    )
    out.append("")
    for line in VERSE:
        out.append(line)
        out.append("")

    out.append("## 结语")
    out.append("")
    out.append(
        "道法自然这一层义理，说到底只有一句话：八字是自然的缩影，看命要回到自然中去。"
        "命局原局用它定格局层次、富贵程度与职业取向，大运的吉凶好坏也由它来定，"
        "流年则与理法合看，断其应事。它与理法一致时，理法才是准确的理法；"
        "它与理法相左时，以自然实况为准，不可偏执理法。四时之序、十二个月与二十四节气的配置，"
        "是这一层落到实处的抓手。本册所辑，即以此义为纲，读者与正文参看，自明其法。"
    )
    text = "\n".join(out).rstrip() + "\n"

    # 与正文同一套再分段规则（提行引文/口诀、裂开并列项、切长段），只动换行不改字
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
