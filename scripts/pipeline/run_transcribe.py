# -*- coding: utf-8 -*-
"""批量转写：manifest 里所有音视频 -> _out/<课程>/<文件名>.txt
- float16 + beam=1（实测最快，8.8x 实时）
- 断点续跑：输出文件已达标则跳过
- 每 20 分钟切片处理，逐片落盘
用法：
  python run_transcribe.py                # 全部
  python run_transcribe.py --course 01    # 只转课程名包含 "01" 的
  python run_transcribe.py --limit 2      # 只转前 2 个文件
"""
import argparse
import json
import os
import sys
import time
import traceback

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cuda_env  # noqa: F401
from audio_utils import iter_slices, write_wav, SLICE_SEC, TARGET_SR  # noqa
from faster_whisper import WhisperModel  # noqa

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, ".."))
MANIFEST = os.path.join(HERE, "manifest.json")
OUT_ROOT = os.path.join(BASE, "out")
MODEL_DIR = os.path.join(BASE, "models", "faster-whisper-medium")
MAX_CHARS_PER_SLICE = 2_000_000

PROMPT = ("这是【课程领域】讲座。术语：【把本课程的专有名词、术语、人名罗列在此，"
          "越全越好】。")


def log(msg, logfile):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(logfile, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def transcribe_file(path, out_txt, model, logfile):
    """整文件转写，逐切片追加落盘。返回字数。"""
    total_chars = 0
    os.makedirs(os.path.dirname(out_txt), exist_ok=True)
    with open(out_txt, "w", encoding="utf-8") as fo:
        n_slice = 0
        for samples in iter_slices(path, slice_sec=SLICE_SEC):
            n_slice += 1
            tmp_wav = os.path.join(HERE, "_slice.wav")
            write_wav(tmp_wav, samples)
            segs, info = model.transcribe(
                tmp_wav, language="zh", beam_size=1,
                initial_prompt=PROMPT, condition_on_previous_text=False,
                vad_filter=False)
            for s in segs:
                t = s.text.strip()
                if t:
                    fo.write(t + "\n")
                    total_chars += len(t)
            fo.flush()
            log(f"    切片{n_slice} 累计 {total_chars} 字", logfile)
        duration = n_slice * SLICE_SEC / 3600
    return total_chars, duration


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--course", default=None, help="仅转课程名包含该字符串的")
    ap.add_argument("--file", default=None, help="仅转相对路径包含该字符串的文件")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--logfile", default=os.path.join(HERE, "transcribe.log"))
    args = ap.parse_args()

    items = json.load(open(MANIFEST, encoding="utf-8"))
    items = [x for x in items if not x.get("err") and x["dur_sec"] > 60]
    if args.course:
        items = [x for x in items if args.course in x["course"]]
    if args.file:
        items = [x for x in items if args.file in x["rel"]]
    items.sort(key=lambda x: (x["course"], x["rel"]))
    if args.limit:
        items = items[:args.limit]

    log(f"待转写 {len(items)} 个文件，共 {sum(x['dur_sec'] for x in items)/3600:.1f} 小时",
        args.logfile)
    log("加载模型...", args.logfile)
    model = WhisperModel(MODEL_DIR, device="cuda",
                         compute_type="float16", cpu_threads=4)
    log("模型就绪", args.logfile)

    done = skipped = failed = 0
    t_start = time.time()
    total_sec_done = 0.0
    for i, it in enumerate(items, 1):
        rel = it["rel"]
        out_txt = os.path.join(OUT_ROOT, rel)
        out_txt = os.path.splitext(out_txt)[0] + ".txt"
        # 断点续跑：已有输出且字数合理则跳过
        if os.path.exists(out_txt) and os.path.getsize(out_txt) > 500:
            est_min = it["dur_sec"] / 60 * 246
            if os.path.getsize(out_txt) > est_min * 1.5:  # UTF-8 中文约 3 字节/字
                skipped += 1
                continue

        log(f"[{i}/{len(items)}] {it['dur_sec']/60:.1f}min {rel}", args.logfile)
        t0 = time.time()
        try:
            chars, dur_h = transcribe_file(it["path"], out_txt, model, args.logfile)
            el = time.time() - t0
            rate = it["dur_sec"] / el if el else 0
            done += 1
            total_sec_done += it["dur_sec"]
            log(f"    完成 {chars} 字，用时 {el/60:.1f}min（{rate:.1f}x）", args.logfile)
        except Exception as e:
            failed += 1
            log(f"    !! 失败: {e}", args.logfile)
            with open(os.path.join(HERE, "failed.txt"), "a", encoding="utf-8") as f:
                f.write(rel + "\t" + repr(e) + "\n")
            traceback.print_exc()

        # 进度与 ETA
        elapsed_h = (time.time() - t_start) / 3600
        done_h = total_sec_done / 3600
        if done_h > 0:
            all_h = sum(x["dur_sec"] for x in items) / 3600
            eta = (elapsed_h / done_h) * (all_h - done_h)
            log(f"    进度 {done_h:.1f}/{all_h:.1f}h  已用 {elapsed_h:.1f}h  ETA {eta:.1f}h",
                args.logfile)

    log(f"结束：完成 {done}，跳过 {skipped}，失败 {failed}，"
        f"总用时 {(time.time()-t_start)/3600:.2f}h", args.logfile)


if __name__ == "__main__":
    main()
