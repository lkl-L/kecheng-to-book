# -*- coding: utf-8 -*-
"""案例集：清掉品牌名残留。

对象（放在派子代理之前做，否则子代理会照抄）：
  · sec-md/<前缀>-*.md   已写出的章节稿（正文）
  · cases/*.txt          分节素材（子代理直接读，必须干净）
  · digest.txt           分类摘要
"""
import glob
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

# 素材里的页眉残留与正文里的品牌称谓，一并中性化
# 注意 ORDER：长者优先，且清到空串的规则（如页眉）要放在最后。
MAP = [
    ("【品牌名】", "本门"),
    ("【机构名】", "本门"),
    ("【讲授者】", "老师"),
    ("【源文件里的页眉字样】", ""),   # 如「XX 93」→「 93」
    ("【另一个页眉变体】", ""),
]


def clean(text):
    for old, new in MAP:
        text = text.replace(old, new)
    return text


def main():
    targets = (
        sorted(glob.glob("sec-md/*.md"))
        + sorted(glob.glob("cases/*.txt"))
        + ["digest.txt"]
    )
    tot_before = tot_after = 0
    for path in targets:
        if not os.path.exists(path):
            continue
        t = open(path, encoding="utf-8").read()
        n = t.count("")
        if not n:
            continue
        tot_before += n
        t2 = clean(t)
        t2 = re.sub(r"[ \t]+\n", "\n", t2)
        open(path, "w", encoding="utf-8").write(t2)
        after = t2.count("")
        tot_after += after
        print("%-28s %3d → %d" % (os.path.basename(path), n, after))
    print("合计  %d → %d" % (tot_before, tot_after))


if __name__ == "__main__":
    main()
