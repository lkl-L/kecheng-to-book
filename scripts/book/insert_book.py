# -*- coding: utf-8 -*-
"""把全书 markdown 插入新建 docx：create_doc -> 逐块 doc_insert_markdown -> save_file"""
import json
import os
import re
import sys
import time

SKILL_DIR = r"<HOME><WorkBuddy安装目录>\...\tencent-local-office-edit"
sys.path.insert(0, SKILL_DIR)
sys.stdout.reconfigure(encoding="utf-8")

import edsdk  # noqa: E402

MD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "经典课实录.md")
OUT_DOCX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "经典课实录.docx")


def call(tool, args, timeout=180):
    r = edsdk._rpc("tools/call", {"name": tool, "arguments": args})
    content = r.get("content") or []
    text = "".join(c.get("text", "") for c in content if isinstance(c, dict))
    return text


def split_blocks(md):
    """按一级/二级标题切块，每块以标题行开头"""
    blocks = []
    cur = []
    for ln in md.split("\n"):
        if (ln.startswith("# ") or ln.startswith("## ")) and cur:
            blocks.append("\n".join(cur).strip())
            cur = [ln]
        else:
            cur.append(ln)
    if cur:
        blocks.append("\n".join(cur).strip())
    return [b for b in blocks if b]


def main():
    md = open(MD, encoding="utf-8").read()
    blocks = split_blocks(md)
    print(f"切块数: {len(blocks)}", flush=True)

    file_id = call("create_doc", {})
    # create_doc 返回文本里提取 file_id
    m = re.search(r"(new_doc_[A-Za-z0-9_-]+)", file_id)
    if not m:
        print("create_doc 返回:", file_id[:500], flush=True)
        raise SystemExit(1)
    file_id = m.group(1)
    print("file_id:", file_id, flush=True)

    # 新建空文档直接从 0 开始插入（get_last_operable_pos 对新建实例有时序问题）
    idx = 0
    print("初始 idx:", idx, flush=True)

    t0 = time.time()
    for i, b in enumerate(blocks, 1):
        first_line = b.split("\n", 1)[0][:50]
        r = call("doc_insert_markdown",
                 {"file_id": file_id, "idx": idx, "markdown": b})
        m = re.search(r'"last_edit_index"\s*:\s*(\d+)', r) or \
            re.search(r"last_edit_index[\"':= ]+(\d+)", r)
        if not m:
            # 备选：从 position 取
            m = re.search(r'"position"\s*:\s*(\d+)', r)
        if not m:
            print(f"[{i}] 插入失败: {r[:300]}", flush=True)
            raise SystemExit(1)
        idx = int(m.group(1))
        if i % 10 == 0 or i == len(blocks):
            el = time.time() - t0
            print(f"[{i}/{len(blocks)}] {first_line}  idx={idx}  {el:.0f}s", flush=True)

    print("保存...", flush=True)
    r = call("save_file", {"file_id": file_id, "file_path": OUT_DOCX})
    print(r[:300], flush=True)
    print("DONE ->", OUT_DOCX, os.path.getsize(OUT_DOCX) // 1024, "KB" if os.path.exists(OUT_DOCX) else "(未落盘)", flush=True)


if __name__ == "__main__":
    main()
