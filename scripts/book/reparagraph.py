# -*- coding: utf-8 -*-
"""正文再分段引擎（风水书版）：让转写稿的段落节奏接近正式出版物。

与 book8 版同源，针对风水书做了两点适配：
  1. 目标改为 book/ 下的 6 本合并稿（整本处理），备份到 md.bak-prepara/。
  2. 【经文】…【讲解】之间的韵文整块保护，一律不切行（韵文本身已逐句分行）。

处理三种病灶
  1. 长段一坨（>250 字的段落占 15%~24%，最长 1095 字）→ 按句末标点装箱切段。
  2. 古文引文埋在大段里 → 提行为 `> ` 引文块（排版脚本据此排楷体缩进）。
  3. 并列项挤在一段（「一是…二是…」「第一…第二…」「其一…其二…」）→ 各自成段。

铁律：只动换行，一个字、一个标点都不改。末尾硬校验，不一致就地回滚。

用法：
    python reparagraph.py                 # 处理 6 本
    python reparagraph.py 赋文课实录
    python reparagraph.py --dry 赋文课实录
"""
import os
import re
import shutil
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
BAK = os.path.join(BASE, "md.bak-prepara")

BOOKS = [
    "经典课实录",
    "赋文课实录",
    "图文课实录",
    "日课课实录",
    "实战课实录",
    "微课堂实录",
]

# ---- 段落长度阈值（按汉字数）----
# 可用环境变量覆盖，便于试算：RP_MAX / RP_TARGET / RP_MIN
MAX_PARA = int(os.environ.get("RP_MAX", 200))   # 超过此长度必须切
TARGET = int(os.environ.get("RP_TARGET", 165))  # 装箱目标：尽量不超过这个值
MIN_PARA = int(os.environ.get("RP_MIN", 12))    # 小于此长度的残段并回上一段
LEAD_MAX = 32         # 引文引导句（「孔子说：」）短于此长度则单独成段

# ---- 保护行：结构、小节标题、标记、已有的引文块 ----
RE_STRUCT = re.compile(r"^#{1,6}\s")
RE_MARK = re.compile(r"^【[^】]{1,10}】$")
RE_SUB_CN = re.compile(r"^[一二三四五六七八九十]{1,3}、\S")
RE_SUB_PAR = re.compile(r"^（[一二三四五六七八九十]{1,3}）\S")
RE_CITE_LINE = re.compile(r"^>\s")
SUB_MAXLEN = 34
END_PUNCT = ("。", "！", "？", "；", "…")

# ---- 引文提行 ----
RE_QUOTE = re.compile(r"\u201c[^\u201c\u201d]{18,}\u201d")
RE_LEAD = re.compile(
    r"(说|讲|云|道|曰|写道|认为|指出|记载|引用|提到|谈到|强调|主张"
    r"|如下|照录|录之|口诀|歌诀|原文)[，,。；;：:]?\s*$")
RE_NOT_LEAD = re.compile(r"(也就是说|比如说|就是说|再说|再说来|所以说|换句话说)[，,。；;：:]?\s*$")

# ---- 并列项 ----
# 仅在「第X，」「第X是/点/条/种…」这类真正的条目处裂开；
# 不能用宽泛的 `第[一二三]`——「。第一句讲的就是…」「。其实…」都会被误切。
RE_ENUM = re.compile(r"(?<=[。；！？])(?=[一二三四五六七八九十]是)")
RE_ENUM2 = re.compile(
    r"(?<=[。；！？])(?=第[一二三四五六七八九十]{1,2}(?:[，、是]|点|条|种|个|方面|部分|步))")
RE_ENUM3 = re.compile(
    r"(?<=[。；！？])(?=其[一二三四五六七八九](?:[，、是]|点|条|种|个))")
RE_END = re.compile(r"[。！？；]")
# 收尾标点：引文后紧跟的「。」属于上一段（引文），不能甩成孤立行
RE_CLOSE_PUNCT = re.compile(r"^[。，、；：！？…\u201d\u2019\u300d\u300f\uff09)]+")
RE_ONLY_PUNCT = re.compile(r"^[。，、；：！？…\u201d\u2019\u300d\u300f\uff09)+]+$")

# ---- 话题转换词：切点优先落在这里 ----
CONNECT = (
    "再说", "另外", "还要", "还有", "这里要", "这里讲", "因此", "所以", "于是",
    "总之", "可见", "由此可见", "换句话说", "也就是说", "反过来说", "反过来讲",
    "举个例子", "比如", "例如", "又如", "同样", "同样地", "事实上", "其实",
    "说到底", "总的来说", "归根结底", "要注意的是", "需要说明的是",
)

# 韵文块标记：进入后整块保护，直到遇到下一个标记
JING_START = "【经文】"
JING_STOP = ("【讲解】", "【原文】", "【白话】", "【注解】")


def is_protected(line):
    s = line.strip()
    if not s:
        return True
    if RE_STRUCT.match(s) or RE_MARK.match(s) or RE_CITE_LINE.match(s):
        return True
    if len(s) <= SUB_MAXLEN and not s.endswith(END_PUNCT):
        if RE_SUB_CN.match(s) or RE_SUB_PAR.match(s):
            return True
    return False


# ---------------- 规则 1：引文提行 ----------------

def split_cites(text):
    out, pos = [], 0
    for m in RE_QUOTE.finditer(text):
        lead = text[max(0, m.start() - 10):m.start()]
        if not RE_LEAD.search(lead.strip()) or RE_NOT_LEAD.search(lead.strip()):
            continue
        if m.start() > pos:
            body, tail = _split_lead(text[pos:m.start()])
            if body.strip():
                out.append(["p", body])
            if tail.strip():
                out.append(["p", tail])
        out.append(["cite", m.group(0)])
        pos = m.end()
    if pos < len(text):
        rest = text[pos:]
        # 引文后紧跟的收尾标点（如「”。」里的 。）并入引文行，避免孤立标点
        m2 = RE_CLOSE_PUNCT.match(rest)
        if m2 and out and out[-1][0] == "cite":
            out[-1][1] += m2.group(0)
            rest = rest[m2.end():]
        if rest.strip():
            out.append(["p", rest])
    return out or [["p", text]]


def _split_lead(pre):
    s = pre.rstrip()
    if not s:
        return "", ""
    cuts = [m.end() for m in RE_END.finditer(s)]
    if not cuts:
        if len(s.strip()) <= LEAD_MAX and RE_LEAD.search(s.strip()):
            return "", s
        return s, ""
    cut = cuts[-1]
    tail = s[cut:]
    if len(tail.strip()) <= LEAD_MAX and RE_LEAD.search(tail.strip()):
        return s[:cut], tail
    return s, ""


# ---------------- 规则 3：并列项裂开 ----------------

def split_enum(text):
    for rx in (RE_ENUM, RE_ENUM2, RE_ENUM3):
        text = rx.sub("\n", text)
    return text


# ---------------- 规则 2：长段切分 ----------------

def cut_sentences(text, maxlen=MAX_PARA):
    sents = re.findall(r"[^。！？]*[。！？]+|[^。！？]+$", text)
    sents = [s for s in sents if s.strip()]
    out, cur = [], ""
    for s in sents:
        break_here = bool(cur) and len(cur) >= TARGET * 0.5 and any(
            s.lstrip().startswith(c) for c in CONNECT)
        if cur and (len(cur) + len(s) > TARGET or break_here):
            out.append(cur)
            cur = s
        else:
            cur += s
    if cur.strip():
        out.append(cur)
    final = []
    for seg in out:
        while len(seg) > maxlen * 1.6:
            cut = seg.rfind("，", 0, maxlen)
            if cut < maxlen * 0.4:
                cut = maxlen
            final.append(seg[:cut + 1])
            seg = seg[cut + 1:]
        final.append(seg)
    return [x for x in final if x.strip()]


def verse_lines(seg):
    sents = re.findall(r"[^。！？；]+[。！？；]", seg)
    rest = seg[len("".join(sents)):]
    if rest.strip() and rest.strip().strip("\u201d\u2019\uff09\u300b\u3009"):
        sents.append(rest)
    elif sents:
        sents[-1] += rest
    else:
        return ["> " + seg]
    L = [len(x) for x in sents]
    if len(sents) >= 3 and (max(L) - min(L)) <= 8 and max(L) <= 20:
        return ["> " + x for x in sents]
    return ["> " + seg]


def reflow_paragraph(text):
    out_lines = []
    for kind, seg in split_cites(text):
        seg = seg.strip()
        if not seg:
            continue
        if kind == "cite":
            out_lines.extend(verse_lines(seg))
            continue
        for part in split_enum(seg).split("\n"):
            part = part.strip()
            if not part:
                continue
            # 段首若是收尾标点，说明它属于上一行，回贴过去
            m0 = RE_CLOSE_PUNCT.match(part)
            if m0 and out_lines:
                out_lines[-1] += m0.group(0)
                part = part[m0.end():].strip()
                if not part:
                    continue
            if len(part) <= MAX_PARA:
                out_lines.append(part)
            else:
                out_lines.extend(cut_sentences(part))
    merged = []
    for ln in out_lines:
        st = ln.strip()
        # 纯标点行（如残留的「。」）一律并回上一行，引文行也不例外
        if merged and RE_ONLY_PUNCT.match(st):
            merged[-1] += ln
            continue
        alone = ln.startswith("> ") or bool(RE_LEAD.search(st))
        if (merged and not alone and len(ln) < MIN_PARA
                and not merged[-1].startswith(">")):
            merged[-1] += ln
        else:
            merged.append(ln)
    return merged


# ---------------- 主处理 ----------------

def process_text(md):
    lines = md.split("\n")
    out = []
    stat = {"cite": 0, "split": 0, "enum": 0, "before": 0, "after": 0, "jing": 0}
    in_jing = False
    for raw in lines:
        s = raw.rstrip()
        t = s.strip()
        # 韵文块保护：标记进入 / 退出
        if t == JING_START:
            in_jing = True
        elif t in JING_STOP:
            in_jing = False
        if in_jing or is_protected(s):
            if in_jing and t:
                stat["jing"] += 1
            out.append(s)
            continue
        stat["before"] += 1
        new = reflow_paragraph(s.strip())
        stat["after"] += len(new)
        if len(new) > 1:
            stat["split"] += 1
        for ln in new:
            if ln.startswith("> "):
                stat["cite"] += 1
            out.append(ln)
            out.append("")
    text = "\n".join(out)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text, stat


def strip_all(t):
    t = t.replace("> ", "").replace(">", "")
    return re.sub(r"\s", "", t)


def process_file(path, dry=False):
    md = open(path, encoding="utf-8").read()
    new, stat = process_text(md)
    a, b = strip_all(md), strip_all(new)
    if a != b:
        i = 0
        while i < min(len(a), len(b)) and a[i] == b[i]:
            i += 1
        print("!! %s 校验失败：第 %d 字起不一致" % (os.path.basename(path), i))
        print("   原: ...%s" % a[max(0, i - 25):i + 25])
        print("   新: ...%s" % b[max(0, i - 25):i + 25])
        return False, stat
    if not dry:
        os.makedirs(BAK, exist_ok=True)
        dst = os.path.join(BAK, os.path.basename(path))
        if not os.path.exists(dst):
            shutil.copy2(path, dst)
        open(path, "w", encoding="utf-8").write(new)
    return True, stat


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry" in sys.argv
    names = args or BOOKS
    total = {"cite": 0, "split": 0, "before": 0, "after": 0}
    bad = 0
    for name in names:
        p = os.path.join(BASE, name + ".md")
        ok, st = process_file(p, dry=dry)
        for k in total:
            total[k] += st.get(k, 0)
        print("%s %-34s 段 %4d→%-4d  切 %3d 段  提行 %3d 条  韵文保护 %4d 行"
              % ("OK " if ok else "FAIL", name, st["before"], st["after"],
                 st["split"], st["cite"], st["jing"]))
        bad += 0 if ok else 1
    print("-" * 74)
    print("合计：正文段 %d → %d（+%d），切开 %d 段，提行 %d 条引文"
          % (total["before"], total["after"], total["after"] - total["before"],
             total["split"], total["cite"]))
    if bad:
        print("!! 有 %d 个文件校验失败，已回滚" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
