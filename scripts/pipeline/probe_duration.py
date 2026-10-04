# -*- coding: utf-8 -*-
"""探测 <媒体盘>/<课程目录> 下所有音视频文件的时长，生成 manifest.json"""
import av
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"<媒体盘>/<课程目录>"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "manifest.json")

EXTS = {".mp4", ".m4a", ".mp3", ".wav", ".flac", ".aac", ".wmv",
        ".avi", ".mkv", ".mov", ".ts", ".rmvb", ".flv"}

items = []
errors = []
for dirpath, dirnames, filenames in os.walk(ROOT):
    for fn in filenames:
        ext = os.path.splitext(fn)[1].lower()
        if ext not in EXTS:
            continue
        full = os.path.join(dirpath, fn)
        rel = os.path.relpath(full, ROOT)
        course = rel.split(os.sep)[0]
        size_mb = round(os.path.getsize(full) / 1048576, 1)
        rec = {"path": full, "rel": rel, "course": course,
               "size_mb": size_mb, "dur_sec": 0, "err": None}
        try:
            with av.open(full) as c:
                rec["dur_sec"] = round((c.duration or 0) / av.time_base, 1)
                auds = [s for s in c.streams if s.type == "audio"]
                if auds:
                    rec["sample_rate"] = auds[0].codec_context.sample_rate
                    rec["channels"] = auds[0].codec_context.channels
                else:
                    rec["err"] = "no_audio_stream"
        except Exception as e:
            rec["err"] = str(e)[:200]
            errors.append(rec["rel"])
        items.append(rec)
        print(f"[{len(items)}] {rec['dur_sec']:>8.0f}s {size_mb:>8.1f}MB {rel}", flush=True)

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(items, f, ensure_ascii=False, indent=1)

# 汇总
total_sec = sum(x["dur_sec"] for x in items)
by_course = {}
for x in items:
    d = by_course.setdefault(x["course"], {"n": 0, "sec": 0})
    d["n"] += 1
    d["sec"] += x["dur_sec"]

print("\n===== 汇总 =====")
print(f"文件总数: {len(items)}  出错: {len(errors)}")
for k in sorted(by_course):
    h = by_course[k]["sec"] / 3600
    print(f"{by_course[k]['n']:>4}个 {h:>7.2f}小时  {k}")
print(f"总计: {total_sec/3600:.1f} 小时")
