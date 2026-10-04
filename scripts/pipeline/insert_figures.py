# -*- coding: utf-8 -*-
"""把 captions.md 的图说按锚点插入 sec-md 正文，并合并成 captions_all.md。"""
import glob
import os
import re
import sys

BASE = r"<项目根>"
FIGDIR = os.path.join(BASE, "figures/qjj")


def parse_captions(md_path):
    figs, cur = [], None
    for raw in open(md_path, encoding="utf-8"):
        line = raw.rstrip("\n")
        m = re.match(r"^###\s*(.+)$", line)
        if m:
            if cur:
                figs.append(cur)
            cur = {"编号": m.group(1).strip()}
            continue
        if cur is None:
            continue
        m2 = re.match(r"^-\s*(讲次|标题|时间|文件|锚点):\s*(.*)$", line)
        if m2:
            cur[m2.group(1)] = m2.group(2).strip()
        elif line.startswith("- 图说:"):
            cur["图说"] = [line[len("- 图说:"):].strip()]
        elif "图说" in cur and isinstance(cur.get("图说"), list):
            if line.strip():
                cur["图说"].append(line.strip())
            else:
                cur["图说"] = "".join(cur["图说"])
    if cur:
        if isinstance(cur.get("图说"), list):
            cur["图说"] = "".join(cur["图说"])
        figs.append(cur)
    return figs


def norm(s):
    for ch in "“”\"‘’'":
        s = s.replace(ch, "")
    return s


def main():
    all_figs = []
    errors = []
    for n in range(1, 10):
        cap = os.path.join(FIGDIR, f"lesson0{n}", "captions.md")
        if not os.path.exists(cap):
            errors.append(f"!! 缺 {cap}")
            continue
        figs = parse_captions(cap)
        figs = [f for f in figs if f.get("文件")]
        all_figs.extend(figs)

        # 插入正文
        sec = os.path.join(BASE, "book/sec-md", f"02-{n:03d}.md")
        paras = open(sec, encoding="utf-8").read().split("\n\n")
        fig_id = None  # 已无占位用途
        insert_at = {}  # 段索引 -> [图说文本]
        for f in figs:
            fid = f["编号"].replace(" ", "")
            # 幂等：已插入过就跳过
            if any(fid in p for p in paras):
                continue
            anchor = norm((f.get("锚点") or "").strip())
            m = re.match(r"^(.*?)段(之前|之后)$", anchor)
            if not m:
                errors.append(f"!! 锚点格式错 {fid}: {anchor}")
                continue
            phrase, pos = m.group(1), m.group(2)
            idx = None
            for i, p in enumerate(paras):
                if phrase and phrase in norm(p):
                    idx = i if pos == "之前" else i + 1
                    break
            if idx is None:
                errors.append(f"!! 锚点未找到 {fid}: {phrase}")
                continue
            text = f"（{fid}　{f.get('标题','')}——{f.get('图说','')}）"
            insert_at.setdefault(idx, []).append((f.get("时间", ""), text))

        # 从后往前插，避免索引失效；同一位置按时间排序
        for idx in sorted(insert_at, reverse=True):
            items = sorted(insert_at[idx])
            for _, text in items:
                paras.insert(idx, text)

        open(sec, "w", encoding="utf-8").write("\n\n".join(paras))
        print(f"第{n}讲: 插入 {sum(len(v) for v in insert_at.values())}/{len(figs)} 张图说")

    # 合并 captions_all.md（按讲次+编号排序）
    def key(f):
        m = re.match(r"图\s*(\d+)-(\d+)", f.get("编号", ""))
        return (int(m.group(1)), int(m.group(2))) if m else (99, 99)

    all_figs.sort(key=key)
    out = os.path.join(FIGDIR, "captions_all.md")
    with open(out, "w", encoding="utf-8") as w:
        for f in all_figs:
            w.write(f"### {f['编号']}\n")
            for k in ("讲次", "标题", "时间", "文件"):
                if f.get(k):
                    w.write(f"- {k}: {f[k]}\n")
            w.write(f"- 图说: {f.get('图说','')}\n\n")
    print(f"captions_all.md: {len(all_figs)} 张图")
    for e in errors:
        print(e)
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
