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

MD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "【书名】.md")
OUT_DOCX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "【书名】.docx")


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


def wait_ready(file_id, tries=45):
    """create_doc 后编辑器实例可能尚未就绪（报 document is not open），轮询直到可读"""
    for k in range(tries):
        try:
            r = call("doc_get_last_operable_pos", {"file_id": file_id})
            if '"position"' in r:
                import re as _re
                m = _re.search(r'"position"\s*:\s*(\d+)', r)
                pos = int(m.group(1)) if m else 0
                print(f"编辑器就绪（尝试 {k+1} 次），position={pos}", flush=True)
                return pos
        except Exception as e:
            pass
        time.sleep(1)
    raise SystemExit("编辑器始终未就绪")


def insert_block(file_id, idx, markdown, retries=20):
    """单块插入，遇到 document is not open 等瞬时错误时重试"""
    for k in range(retries):
        try:
            r = call("doc_insert_markdown",
                     {"file_id": file_id, "idx": idx, "markdown": markdown})
            m = re.search(r'"last_edit_index"\s*:\s*(\d+)', r) or \
                re.search(r'"position"\s*:\s*(\d+)', r)
            if m:
                return int(m.group(1)), None
            err = r[:200]
        except Exception as e:
            err = str(e)[:200]
        time.sleep(1)
    return None, err


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

    # 等待编辑器实例就绪，并从文档末尾可操作位置开始
    idx = wait_ready(file_id)
    print("初始 idx:", idx, flush=True)

    t0 = time.time()
    for i, b in enumerate(blocks, 1):
        first_line = b.split("\n", 1)[0][:50]
        idx, err = insert_block(file_id, idx, b)
        if idx is None:
            print(f"[{i}] 插入失败: {err}", flush=True)
            raise SystemExit(1)
        if i % 10 == 0 or i == len(blocks):
            el = time.time() - t0
            print(f"[{i}/{len(blocks)}] {first_line}  idx={idx}  {el:.0f}s", flush=True)

    print("保存...", flush=True)
    r = call("save_file", {"file_id": file_id, "file_path": OUT_DOCX})
    print(r[:300], flush=True)
    print("DONE ->", OUT_DOCX, os.path.getsize(OUT_DOCX) // 1024, "KB" if os.path.exists(OUT_DOCX) else "(未落盘)", flush=True)


if __name__ == "__main__":
    main()
