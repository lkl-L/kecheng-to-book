# -*- coding: utf-8 -*-
"""示例：把 OCR 文本切成「案例单元」，并跨文件去重、按讨论篇幅排序。
输出：cases.json（全部案例）+ cases_index.txt（人可读索引）

思路（与领域无关）：
  1) 用"案例表头"作切分标志——本领域里每条案例开头都有的固定形式；
  2) 从表头提取：标志词 / 要素串 / 演变串 / 时间串 / 出处页；
  3) 跨文件按"要素串"去重（先把 OCR 形近误字归一），同一案例保留讨论最详细的一条。

用法：改 SRC / OUT / CHARS / MARK / WATERMARKS / FIX 后运行。
"""
import glob
import re
import os
import json

SRC = r"<项目根>/book8/materials-ocr"
OUT = r"<项目根>/book9"

# 要素字符集：本领域"要素"用到的字符 + OCR 常见误识字（宽字符集）
CHARS = "【把要素字符与常见误识字都放进来】"
OK = CHARS + "0123456789 \t：:，,、.。/（）()"

# 案例表头：行首的标志词，其后 26 字内出现收尾词，中间只允许要素字符/数字/标点
MARK = re.compile(r"(?m)(?:^|\n)[\s\d]{0,8}(【标志词1】|【标志词2】)\s*[：:，,、.。]?\s*([" + OK + r"]{0,26}?)【收尾词】")
# 主题行：形如 '某主题' '某主题（应用篇）' 这类小标题，用于给案例归类
HEAD = re.compile(r"^\s*([\u4e00-\u9fa5]{2,14}(?:的看法|篇|的应用|关系|类象|论断|结构|规律)?)\s*$")

# OCR 页眉水印／推广语（按源文件实际内容改）
WATERMARKS = [
    r"【页眉水印文字】",
    r"【推广语】",
    r"更多资料请联系主编微信：\d+",
    r"正版请联系主编微信：\d+",
]

# 形近误字归一表（用于跨文件去重；按你的领域补）
FIX = {"葵": "癸", "已": "巳", "卵": "卯", "王": "壬",
       "戍": "戌", "末": "未", "玄": "亥", "西": "酉"}


def strip_ocr(s):
    s = re.sub(r"<<<PAGE:(\d+)>>>", lambda m: "\n[[PAGE:%s]]\n" % m.group(1), s)
    for pat in WATERMARKS:
        s = re.sub(pat, "", s)
    s = re.sub(r"[ \t]+", " ", s)
    return s


def page_of(text, pos):
    pg = None
    for m in re.finditer(r"\[\[PAGE:(\d+)\]\]", text[:pos]):
        pg = m.group(1)
    return pg


def split_cases(text):
    ms = list(MARK.finditer(text))
    units = []
    for i, m in enumerate(ms):
        start = m.start()
        end = ms[i + 1].start() if i + 1 < len(ms) else len(text)
        seg = text[start:end]
        mark = m.group(1)
        # 要素串：标记后到收尾词之间的要素字符
        head = re.sub(r"[^" + CHARS + r"]", "", text[m.start():m.end()])
        head = head[1:]                      # 去掉标志词
        m8 = re.search(r"[【标志词1】【标志词2】]\s*[：:]?\s*([" + CHARS + r"]{8})",
                       text[m.start():m.start() + 30])
        key = m8.group(1) if m8 else head[:8]
        # 演变串
        mseq = re.search(r"【收尾词】[：:]?\s*(.{0,80})", seg)
        seq = re.sub(r"\s+", " ", mseq.group(1)).strip()[:70] if mseq else ""
        # 时间串
        mtime = re.search(r"时间[：:]?\s*([0-9\s]{4,60})", seg)
        time = re.sub(r"\s+", " ", mtime.group(1)).strip()[:48] if mtime else ""
        # 正文＝去掉表头那几行后的分析
        body = re.sub(r"^.*?时间[：:]?[0-9\s]{0,60}", "", seg, count=1, flags=re.S)
        body = body.strip()
        units.append({
            "mark": mark, "key": key, "seq": seq, "time": time,
            "page": page_of(text, start), "pos": start,
            "raw_head": re.sub(r"\s+", " ", text[start:start + 260]).strip(),
            "len": len(re.sub(r"\s", "", body)), "body": body,
        })
    return units


def key_of(key):
    """把 OCR 形近误字归一，用于跨文件去重"""
    return key.translate(str.maketrans(FIX))


def main():
    files = sorted(glob.glob(os.path.join(SRC, "*.txt")))
    allu = []
    for f in files:
        raw = open(f, encoding="utf-8", errors="ignore").read()
        text = strip_ocr(raw)
        us = split_cases(text)
        for u in us:
            u["src"] = os.path.basename(f)[:-4]
        allu += us
        rich = sum(1 for u in us if u["len"] >= 300)
        print("%-24s 单元 %4d  其中详批(>=300字) %3d" % (os.path.basename(f)[:-4], len(us), rich))

    # 去重：同 key 保留 len 最大的一条，记录其他出处
    best = {}
    for u in allu:
        k = key_of(u["key"])[:8]
        if k not in best or u["len"] > best[k]["len"]:
            if k in best:
                u.setdefault("dups", [])
                u["dups"] = best[k].get("dups", []) + ["%s p%s" % (best[k]["src"], best[k]["page"])]
            best[k] = u
        else:
            best[k].setdefault("dups", []).append("%s p%s" % (u["src"], u["page"]))
    uniq = sorted(best.values(), key=lambda x: -x["len"])
    print("-" * 58)
    print("切出 %d 例，去重后 %d 例" % (len(allu), len(uniq)))
    for th in (1500, 800, 400, 200, 100):
        print("  讨论 >=%4d 字：%3d 例" % (th, sum(1 for u in uniq if u["len"] >= th)))

    json.dump({"units": uniq, "total_raw": len(allu)},
              open(os.path.join(OUT, "cases.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    with open(os.path.join(OUT, "cases_index.txt"), "w", encoding="utf-8") as fp:
        for i, u in enumerate(uniq, 1):
            fp.write("%4d  %s %s  演变 %s  时间 %s  %5d字  %s p%s%s\n" % (
                i, u["mark"], u["key"], u["seq"][:34], u["time"][:34], u["len"],
                u["src"], u["page"],
                ("  重出于 " + ", ".join(u.get("dups", [])[:3])) if u.get("dups") else ""))
    print("已写 cases.json / cases_index.txt")


if __name__ == "__main__":
    main()
