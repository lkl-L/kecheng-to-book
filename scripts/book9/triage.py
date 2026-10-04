# -*- coding: utf-8 -*-
"""对去重后的命例做主题粗分类，并导出人可读摘要 digest.txt 供人工核对。"""
import json, re, os
from collections import Counter

BASE = r"<项目根>/book9"

THEMES = [
    ("婚姻感情", "婚|离婚|结婚|老公|老婆|丈夫|妻子|配偶|夫星|妻星|再婚|二婚|同居|感情|外遇|桃花|寡|夫妻"),
    ("财富事业", "发财|破财|财运|财富|生意|老板|企业家|亿万|千万|百万|投资|股东|负债|欠债|亏损|挣钱|赚钱|收入|资产|房产|车|经营"),
    ("官贵学历", "当官|官职|仕途|公务员|升职|提拔|公职|体制|事业单位|学历|大学|研究生|博士|考学|升学|考试|职称|领导|地位|贵气"),
    ("六亲子女", "父亲|母亲|父母|爸|妈|子女|孩子|儿子|女儿|流产|堕胎|兄弟|姐妹|哥哥|弟弟|爷爷|奶奶|姥姥|六亲|亲人"),
    ("身体疾病", "生病|有病|疾病|癌|瘤|手术|住院|受伤|车祸|骨折|残疾|瘫痪|抑郁|自杀|灾|伤疤|烫伤|疼|血压|心脏|肝|肾|胃|精神|夭折|短命"),
    ("子女与婚姻应期", "应期"),
]


def score(body):
    c = Counter()
    for name, pat in THEMES:
        c[name] = len(re.findall(pat, body))
    return c


def main():
    d = json.load(open(os.path.join(BASE, "cases.json"), encoding="utf-8"))
    units = [u for u in d["units"] if u["len"] >= 400]
    for u in units:
        u["body"] = re.sub(r"\[\[PAGE:\d+\]\]", "", u["body"])
        c = score(u["body"])
        top = c.most_common(2)
        u["theme"] = top[0][0] if top and top[0][1] > 0 else "综合断例"
        u["scores"] = dict(c)
    dist = Counter(u["theme"] for u in units)
    print(">=400 字命例 %d 例，主题粗分：" % len(units))
    for k, v in dist.most_common():
        print("   %-12s %3d" % (k, v))

    with open(os.path.join(BASE, "digest.txt"), "w", encoding="utf-8") as fp:
        for i, u in enumerate(units, 1):
            fp.write("#%03d [%s] %s %s  大运%s  年份%s  (%s p%s, %d字)\n" % (
                i, u["theme"], u["gender"], u["bazi"], u["dayun"][:40], u["years"][:30],
                u["src"], u["page"], u["len"]))
            fp.write(re.sub(r"\n+", " ", u["body"][:760]) + "\n\n")
    json.dump(units, open(os.path.join(BASE, "cases_tagged.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("已写 digest.txt / cases_tagged.json")


if __name__ == "__main__":
    main()
