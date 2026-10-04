# -*- coding: utf-8 -*-
"""共享工具：解码媒体文件 -> 归一化 16k 单声道切片 wav"""
import av
import numpy as np
import wave

TARGET_SR = 16000
SLICE_SEC = 20 * 60  # 20 分钟切片
_MERGE_SEC = 10      # 每 10 秒做一次批量合并，避免逐帧 concatenate 的 O(n²) 拷贝


def iter_slices(path, slice_sec=SLICE_SEC):
    """逐切片产出 float32 单声道 16k 数组（峰值归一化到 0.9）。"""
    container = av.open(path)
    try:
        astreams = [s for s in container.streams if s.type == "audio"]
        if not astreams:
            raise RuntimeError("no audio stream")
        stream = astreams[0]
        resampler = av.AudioResampler(format="s16", layout="mono", rate=TARGET_SR)
        buf = np.empty(0, dtype=np.float32)
        pending = []
        pending_len = 0

        def flush_pending():
            nonlocal buf, pending, pending_len
            if not pending:
                return
            buf = np.concatenate(pending) if buf.size == 0 else \
                np.concatenate([buf] + pending)
            pending = []
            pending_len = 0

        for frame in container.decode(stream):
            if frame.pts is None:
                continue
            for rf in resampler.resample(frame):
                arr = rf.to_ndarray()
                if arr.ndim == 2:
                    arr = arr.reshape(-1)
                pending.append(arr.astype(np.float32) / 32768.0)
                pending_len += arr.size
                if pending_len >= TARGET_SR * _MERGE_SEC:
                    flush_pending()
                    if buf.size >= slice_sec * TARGET_SR:
                        yield _normalize(buf)
                        buf = np.empty(0, dtype=np.float32)
        flush_pending()
        if buf.size > TARGET_SR:  # 尾片至少 1 秒才算
            yield _normalize(buf)
    finally:
        container.close()


def _normalize(a):
    peak = float(np.abs(a).max())
    if peak > 1e-6:
        a = a * (0.90 / peak)
    return a


def write_wav(path, samples):
    s16 = (np.clip(samples, -1.0, 1.0) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(TARGET_SR)
        w.writeframes(s16.tobytes())
