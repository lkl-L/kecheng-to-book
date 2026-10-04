# -*- coding: utf-8 -*-
"""扫描 OCR 文本，统计八字命例。
OCR 版式：'乾：辛乙丁葵大运：6丙申16丁酉...' —— 以 '乾/坤 + 若干干支 + 大运' 为命例标志。
干支常有 OCR 误识（癸→葵、巳→已/己、卯→卵、壬→王、戌→戍、未→末、酉→西 等），故用宽字符集。"""
import glob, re, os, json

SRC = r"<项目根>/book8/materials-ocr"
OUT = r"<项目根>/book9"

GAN = "甲乙丙丁戊己庚辛壬癸葵已巳卵卯王戍戊"
ZHI = "子丑寅卯辰巳午未申酉戌亥末卵已己戍玄亥亥西南"
ALL = "".join(sorted(set(GAN + ZHI)))

# 主标志：乾/坤 …(干支若干)… 大运
PAT_A = re.compile(r"(乾|坤)\s*[：:，,、.。]?\s*([" + ALL + r"\s]{4,20}?)\s*大运")
# 备用：乾/坤 + 八字符（同行完整）
PAT_B = re.compile(r"(乾|坤)\s*[：:，,、.。]?\s*(([" + ALL + r"])[\s，,、]*){7,8}")


def main():
    files = sorted(glob.glob(os.path.join(SRC, "*.txt")))
    detail, grand = {}, 0
    for f in files:
        t = open(f, encoding="utf-8", errors="ignore").read()
        a = [(m.start(), norm(m.group(2))) for m in PAT_A.finditer(t)]
        b = [(m.start(), norm(m.group(2))[:8]) for m in PAT_B.finditer(t)]
        # 合并去重（按位置邻近）
        seen, cases = set(), []
        for pos, s in a + b:
            key = pos // 40
            if key in seen:
                continue
            seen.add(key)
            cases.append((pos, s))
        cases.sort()
        name = os.path.basename(f)
        detail[name] = {"cases": len(cases)}
        grand += len(cases)
        print("%-26s 命例 %4d" % (name, len(cases)))
    print("-" * 40)
    print("命例合计 %d" % grand)
    json.dump(detail, open(os.path.join(OUT, "census.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


def norm(s):
    return re.sub(r"[\s，,、.。]", "", s)


if __name__ == "__main__":
    main()
