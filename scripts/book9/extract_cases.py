# -*- coding: utf-8 -*-
"""把 OCR 文本切成「命例单元」，并跨文件去重、按讨论篇幅排序。
输出：cases.json（全部命例）+ cases_index.txt（人可读索引）"""
import glob, re, os, json, hashlib

SRC = r"<项目根>/book8/materials-ocr"
OUT = r"<项目根>/book9"

ALL = "甲乙丙丁戊己庚辛壬癸葵已巳卵卯王壬戍戊子丑寅卯辰巳午未申酉戌亥末玄西"
OK = ALL + "0123456789 \t：:，,、.。/（）()"
# 行首的 乾/坤，其后 26 字内出现「大运」，中间只允许干支/数字/标点
MARK = re.compile(r"(?m)(?:^|\n)[\s\d]{0,8}(乾|坤)\s*[：:，,、.。]?\s*([" + OK + r"]{0,26}?)大运")
# 主题行：形如 '食神制杀' '职业的看法（应用篇）' 这类小标题，用于给命例归主题
HEAD = re.compile(r"^\s*([\u4e00-\u9fa5]{2,14}(?:的看法|篇|的应用|关系|类象|论断|结构|规律|合|冲|穿|刑|破|库)?)\s*$")


def strip_ocr(s):
    s = re.sub(r"<<<PAGE:(\d+)>>>", lambda m: "\n[[PAGE:%s]]\n" % m.group(1), s)
    s = re.sub(r"传播盲派八字命理\s*弘扬易学传统文化", "", s)
    s = re.sub(r"命理内部复习资料、非出版物", "", s)
    s = re.sub(r"更多资料请联系主编微信：\d+", "", s)
    s = re.sub(r"正版请联系主编微信：\d+", "", s)
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
        gender = m.group(1)
        # 八字：标记后到「大运」之间的干支
        head = re.sub(r"[^" + ALL + r"]", "", text[m.start():m.end()])
        head = head[1:]                      # 去掉乾/坤
        # 干净的 8 字候选：从原文本取「乾：XXXXXXXX」形式
        m8 = re.search(r"[乾坤]\s*[：:]?\s*([" + ALL + r"]{8})", text[m.start():m.start() + 30])
        bazi = m8.group(1) if m8 else head[:8]
        # 大运串
        mdy = re.search(r"大运[：:]?\s*(.{0,80})", seg)
        dayun = re.sub(r"\s+", " ", mdy.group(1)).strip()[:70] if mdy else ""
        # 年份
        mny = re.search(r"年份[：:]?\s*([0-9\s]{4,60})", seg)
        years = re.sub(r"\s+", " ", mny.group(1)).strip()[:48] if mny else ""
        # 正文＝去掉表头那几行后的分析
        body = re.sub(r"^.*?年份[：:]?[0-9\s]{0,60}", "", seg, count=1, flags=re.S)
        body = body.strip()
        units.append({
            "gender": gender, "bazi": bazi, "dayun": dayun, "years": years,
            "page": page_of(text, start), "pos": start,
            "raw_head": re.sub(r"\s+", " ", text[start:start + 260]).strip(),
            "len": len(re.sub(r"\s", "", body)), "body": body,
        })
    return units


def key_of(bazi):
    """把 OCR 误字归一，用于跨文件去重"""
    tr = str.maketrans({"葵": "癸", "已": "巳", "己": "己", "卵": "卯", "王": "壬",
                        "戍": "戌", "末": "未", "玄": "亥", "西": "酉"})
    b = bazi.translate(tr)
    return b


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
        k = key_of(u["bazi"])[:8]
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
            fp.write("%4d  %s %s  大运 %s  年份 %s  %5d字  %s p%s%s\n" % (
                i, u["gender"], u["bazi"], u["dayun"][:34], u["years"][:34], u["len"],
                u["src"], u["page"],
                ("  重出于 " + ", ".join(u.get("dups", [])[:3])) if u.get("dups") else ""))
    print("已写 cases.json / cases_index.txt")


if __name__ == "__main__":
    main()
