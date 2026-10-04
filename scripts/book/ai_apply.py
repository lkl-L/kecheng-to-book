# -*- coding: utf-8 -*-
"""落地 AI 复核结果：读取 ai_out/<书名>.txt，把 SPLIT 指令应用到正文。

铁律（与 reparagraph.py 同样的硬校验）：片段拼接后必须与原段逐字相同，
去空白后不一致就整条拒绝，绝不让 AI 改动正文一个字、一个标点。

ai_out 行格式（Tab 分隔）：
    L<行号>\tKEEP
    L<行号>\tSPLIT\t片段1||片段2||片段3
    L<行号>\tMERGE_NEXT            ← 与下一段正文合并（去掉中间换行）

用法：python ai_apply.py [书名...]
"""
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "ai_out")
BAK = os.path.join(BASE, "md.bak-airules")


def norm(s):
    return re.sub(r"\s", "", s.replace(">", ""))


def load_actions(path):
    """解析 ai_out 文件。返回 {行号: (动作, [片段...])}。

    兼容两种写法（子代理可能用 Tab 或竖线分隔）：
        L1234<TAB>KEEP
        L1234<TAB>SPLIT
        L1234<TAB>F<TAB>片段一
        L1234<TAB>F<TAB>片段二
        L1234<TAB>SPLIT<TAB>片段一||片段二      （旧写法，仍兼容）
    """
    acts = {}
    if not os.path.exists(path):
        return acts
    for raw in open(path, encoding="utf-8"):
        ln = raw.rstrip("\n").replace("\\t", "\t").strip()
        if not ln:
            continue
        m = re.match(r"^L\s*(\d+)\b", ln)
        if not m:
            continue
        no = int(m.group(1))
        rest = ln[m.end():].strip().strip("|").strip()
        parts = [p.strip() for p in re.split(r"[\t|]+", rest, maxsplit=2)]
        act = (parts[0] if parts else "").upper()
        if act.startswith("KEEP") or act == "保留":
            acts.setdefault(no, ("KEEP", []))
        elif act.startswith("SPLIT") or act == "切":
            frags = []
            if len(parts) > 1 and parts[1]:
                frags = [f.strip() for f in parts[1].split("||") if f.strip()]
            if len(parts) > 2 and parts[2]:
                frags += [f.strip() for f in parts[2].split("||") if f.strip()]
            acts[no] = ("SPLIT", frags)
        elif act in ("F", "FRAG", "片段", "段"):
            content = parts[1] if len(parts) > 1 else ""
            if no in acts and acts[no][0] == "SPLIT":
                acts[no][1].append(content)
            else:
                acts[no] = ("SPLIT", [content])
        elif not act:                    # 只有行号没有动作 → 视为 KEEP
            acts.setdefault(no, ("KEEP", []))
    # 片段只有 1 个的 SPLIT 实为 KEEP
    for no in list(acts):
        if acts[no][0] == "SPLIT" and len([f for f in acts[no][1] if f]) < 2:
            acts[no] = ("KEEP", [])
    return acts


def next_body_index(lines, i):
    j = i + 1
    while j < len(lines) and not lines[j].strip():
        j += 1
    return j if j < len(lines) else -1


def apply_book(name, dry=False):
    md_path = os.path.join(BASE, name + ".md")
    acts = load_actions(os.path.join(OUT, name + ".txt"))
    lines = open(md_path, encoding="utf-8").read().split("\n")
    orig = list(lines)
    ok_n = bad_n = keep_n = merge_n = 0
    problems = []

    # 先把 MERGE_NEXT 处理掉（用待删标记，避免索引漂移）
    drop = set()
    for no, (act, frags) in acts.items():
        i = no - 1
        if not (0 <= i < len(lines)):
            problems.append("L%d 越界" % no)
            bad_n += 1
            continue
        if act == "MERGE_NEXT":
            j = next_body_index(lines, i)
            if j < 0:
                problems.append("L%d 无可合并的下一段" % no)
                bad_n += 1
                continue
            if lines[j].startswith("> ") or lines[i].startswith("> "):
                problems.append("L%d 引文行不合并" % no)
                bad_n += 1
                continue
            lines[i] = lines[i].rstrip() + lines[j].strip()
            drop.add(j)
            merge_n += 1

    out, replaced = [], {}
    for idx, ln in enumerate(lines):
        no = idx + 1
        if idx in drop:
            continue
        if no not in acts or acts[no][0] != "SPLIT":
            out.append(ln)
            continue
        i = idx
        act, frags = acts[no]
        core = lines[i].strip()
        prefix = "> " if core.startswith("> ") else ""
        if prefix:
            core = core[2:].strip()
        frags = [f.strip() for f in frags if f.strip()]
        if len(frags) < 2 or norm("".join(frags)) != norm(core):
            problems.append("L%d SPLIT 校验失败，已忽略" % no)
            bad_n += 1
            out.append(ln)
            continue
        for f in frags:
            out.append(prefix + f if prefix else f)
            out.append("")
        replaced[no] = len(frags)
        ok_n += 1

    text = "\n".join(out)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 全书总校验：只允许增删空白与引文前缀（以最初读入的正文为基准）
    if norm(text) != norm("\n".join(orig)):
        print("!! %s 全书校验失败，未写入" % name)
        for p in problems:
            print("   ", p)
        return False, ok_n, keep_n, merge_n, bad_n

    if not dry:
        os.makedirs(BAK, exist_ok=True)
        dst = os.path.join(BAK, name + ".md")
        if not os.path.exists(dst):
            open(dst, "w", encoding="utf-8").write(
                open(md_path, encoding="utf-8").read())
        open(md_path, "w", encoding="utf-8").write(text)

    print("%-34s SPLIT %3d 条（%d 段）  MERGE %2d 条  异常 %d 条%s"
          % (name, ok_n, sum(replaced.values()), merge_n, bad_n,
             "" if not problems else "  ← " + problems[0][:40]))
    return True, ok_n, keep_n, merge_n, bad_n


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry" in sys.argv
    import ai_candidates as C
    names = args or C.BOOKS
    bad = 0
    for n in names:
        ok, *_rest, b = apply_book(n, dry=dry)
        bad += 0 if ok else 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.path.insert(0, BASE)
    sys.exit(main())
