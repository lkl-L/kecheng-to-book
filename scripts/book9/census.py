# -*- coding: utf-8 -*-
"""示例：扫描 OCR 文本，统计"案例"条数（案例集素材盘点的第一步）。

OCR 版式举例：'<标志词>：<要素串> … <收尾词>：<演变串>'
要素常被 OCR 误识（形近字），故用**宽字符集**：把本领域要素用到的字符、
连同常见的误认识别字一并列进去，宁可多不可少。

用法：改 SRC / OUT / CHARS / MARK_A / MARK_B 后运行，输出 census.json。
"""
import glob
import re
import os
import json

SRC = r"<项目根>/book8/materials-ocr"
OUT = r"<项目根>/book9"

# 要素用到的全部字符 + OCR 常见误识字（宽字符集）
CHARS = "【把你的要素字符与常见误识字都放进来】"
ALL = "".join(sorted(set(CHARS)))

# 主标志：<标志词> …(要素串若干)… <收尾词>
MARK_A = re.compile(r"(【标志词1】|【标志词2】)\s*[：:，,、.。]?\s*([" + ALL + r"\s]{4,20}?)\s*【收尾词】")
# 备用：<标志词> + 固定长度的要素串（同行完整）
MARK_B = re.compile(r"(【标志词1】|【标志词2】)\s*[：:，,、.。]?\s*(([" + ALL + r"])[\s，,、]*){7,8}")


def norm(s):
    return re.sub(r"[\s，,、.。]", "", s)


def main():
    files = sorted(glob.glob(os.path.join(SRC, "*.txt")))
    detail, grand = {}, 0
    for f in files:
        t = open(f, encoding="utf-8", errors="ignore").read()
        a = [(m.start(), norm(m.group(2))) for m in MARK_A.finditer(t)]
        b = [(m.start(), norm(m.group(2))[:8]) for m in MARK_B.finditer(t)]
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
        print("%-26s 案例 %4d" % (name, len(cases)))
    print("-" * 40)
    print("案例合计 %d" % grand)
    json.dump(detail, open(os.path.join(OUT, "census.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
