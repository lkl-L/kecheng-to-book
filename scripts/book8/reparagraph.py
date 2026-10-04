# -*- coding: utf-8 -*-
"""正文再分段引擎（v3）：让转写稿的段落节奏接近正式出版物。

处理的三种病灶
  1. 长段一坨（>300 字的段落占 6%，最长 675 字）→ 按句末标点切成 120~260 字的自然段，
     切点优先落在话题转换词前（再说 / 另外 / 因此 / 所以 / 总之 / 举个例子 ……）。
  2. 古文引文埋在大段里（如「孔子在《周易·系辞上》说："易与天地准……"」）→ 提行成
     独立引文块，md 里加 `> ` 前缀；排版脚本据此排成楷体、左右缩进、无首行缩进。
  3. 并列项挤在一段（「一是……二是……三是……」「第一……第二……」「其一……其二……」）
     → 每一项另起一段。

铁律：只动换行，一个字、一个标点都不改。
  文件末尾会做硬校验——去掉所有空白和 `>` 前缀后，输出必须与输入逐字相同，
  不一致就地回滚（打印报错并以 1 退出）。

用法：
    python reparagraph.py                 # 处理 sec-md/ 全部
    python reparagraph.py sec-md/bz-001.md
    python reparagraph.py --dry sec-md/bz-001.md    # 只看统计，不写文件
"""
import os
import re
import shutil
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SEC = os.path.join(BASE, "sec-md")
BAK = os.path.join(BASE, "sec-md.bak-v3")

# ---- 段落长度阈值（按汉字数）----
MAX_PARA = 250        # 超过此长度必须切
TARGET = 200          # 装箱目标：尽量不超过这个值
MIN_PARA = 12         # 小于此长度的残段并回上一段
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
# 引号内 ≥ 18 字，且前面紧邻「说／讲／云／道／曰／写道／认为／指出／记载／引用／如下」+ 标点
RE_QUOTE = re.compile(r"“[^“”]{18,}”")
RE_LEAD = re.compile(
    r"(说|讲|云|道|曰|写道|认为|指出|记载|引用|提到|谈到|强调|主张"
    r"|如下|照录|录之|口诀|歌诀)[，,。；;：:]?\s*$")
# 这些「说」不算引文引导语（是「也就是说」「比如说」这类）
RE_NOT_LEAD = re.compile(r"(也就是说|比如说|就是说|再说|再说来|所以说|换句话说)[，,。；;：:]?\s*$")

# ---- 并列项 ----
RE_ENUM = re.compile(r"(?<=[。；！？])(?=[一二三四五六七八九十]是)")
RE_ENUM2 = re.compile(r"(?<=[。；！？])(?=第[一二三四五六七八九])")
RE_ENUM3 = re.compile(r"(?<=[。；！？])(?=其[一二三四五六七八九])")
RE_END = re.compile(r"[。！？；]")

# ---- 话题转换词：切点优先落在这里 ----
CONNECT = (
    "再说", "另外", "还要", "还有", "这里要", "这里讲", "因此", "所以", "于是",
    "总之", "可见", "由此可见", "换句话说", "也就是说", "反过来说", "反过来讲",
    "举个例子", "比如", "例如", "又如", "同样", "同样地", "事实上", "其实",
    "换句话说", "说到底", "总的来说", "归根结底", "要注意的是", "需要说明的是",
)


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
    """把段落拆成 [(kind, text)]；kind ∈ {'p','cite'}。只有长古文引文才算 cite。"""
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
                out.append(["p", tail])          # 「孔子在《系辞》上说：」单独成段
        out.append(["cite", m.group(0)])
        pos = m.end()
    if pos < len(text):
        out.append(["p", text[pos:]])
    return out or [["p", text]]


def _split_lead(pre):
    """把引文前的文字切成 (主体, 最后一句引导语)；引导语够短且确为「……说：」才切出。"""
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
    """按句末标点装箱切段；段长尽量 ≤ TARGET，硬上限 maxlen。"""
    sents = re.findall(r"[^。！？]*[。！？]+|[^。！？]+$", text)
    sents = [s for s in sents if s.strip()]
    out, cur = [], ""
    for s in sents:
        # 当前段已经够长，且下一句以转换词起头 → 在此断开
        break_here = bool(cur) and len(cur) >= TARGET * 0.5 and any(
            s.lstrip().startswith(c) for c in CONNECT)
        if cur and (len(cur) + len(s) > TARGET or break_here):
            out.append(cur)
            cur = s
        else:
            cur += s
    if cur.strip():
        out.append(cur)
    # 兜底：单句仍超上限的，硬切
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
    """引文块：只有真正的韵文（口诀、歌诀——句多、句短且长短齐整）才逐句成行；
    散文式引文（如古文段落，句子长短悬殊）整块保留，避免拆得过碎。"""
    sents = re.findall(r"[^。！？；]+[。！？；]", seg)
    rest = seg[len("".join(sents)):]
    if rest.strip() and rest.strip().strip("”\"’）」》》）"):
        sents.append(rest)                 # 尾部还有实字，单独成句
    elif sents:
        sents[-1] += rest                  # 尾巴只是闭引号，并回上一句
    else:
        return ["> " + seg]
    L = [len(x) for x in sents]
    if len(sents) >= 3 and (max(L) - min(L)) <= 8 and max(L) <= 20:
        return ["> " + x for x in sents]
    return ["> " + seg]


def reflow_paragraph(text):
    """一段正文 → 若干行（含 `> ` 引文行）。"""
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
            if len(part) <= MAX_PARA:
                out_lines.append(part)
            else:
                out_lines.extend(cut_sentences(part))
    # 残段并回上一段（避免「……。二是」这类把孤字甩出来）
    merged = []
    for ln in out_lines:
        alone = ln.startswith("> ") or bool(RE_LEAD.search(ln.strip()))
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
    stat = {"cite": 0, "split": 0, "enum": 0, "before": 0, "after": 0}
    for raw in lines:
        s = raw.rstrip()
        if is_protected(s):
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
            out.append("")          # 每行后补空行，末尾统一把连续空行收缩掉
    # 收尾：去掉多余空行
    text = "\n".join(out)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text, stat


def strip_all(t):
    """用于校验：去掉空白与引文前缀后应逐字相同。"""
    t = t.replace("> ", "").replace(">", "")
    return re.sub(r"\s", "", t)


def process_file(path, dry=False):
    md = open(path, encoding="utf-8").read()
    new, stat = process_text(md)
    a, b = strip_all(md), strip_all(new)
    if a != b:
        # 定位第一处差异
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
    targets = args or sorted(
        os.path.join(SEC, f) for f in os.listdir(SEC) if f.endswith(".md"))
    total = {"cite": 0, "split": 0, "before": 0, "after": 0}
    bad = 0
    for p in targets:
        ok, st = process_file(p, dry=dry)
        for k in total:
            total[k] += st.get(k, 0)
        flag = "OK " if ok else "FAIL"
        print("%s %-14s 段 %3d→%-3d  切 %2d 段  提行 %2d 条"
              % (flag, os.path.basename(p), st["before"], st["after"],
                 st["split"], st["cite"]))
        bad += 0 if ok else 1
    print("-" * 62)
    print("合计：正文段 %d → %d（+%d），切开 %d 段，提行 %d 条引文"
          % (total["before"], total["after"], total["after"] - total["before"],
             total["split"], total["cite"]))
    if bad:
        print("!! 有 %d 个文件校验失败，已回滚" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
