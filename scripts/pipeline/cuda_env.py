# -*- coding: utf-8 -*-
"""把 venv 里 nvidia 包的 CUDA DLL 目录注入 PATH + DLL 搜索路径。
用法：import cuda_env  # 必须在 import ctranslate2/faster_whisper 之前
"""
import glob
import os
import sys

_sp = os.path.join(sys.prefix, "Lib", "site-packages")  # venv 根目录下才是正确位置
_dll_dirs = glob.glob(os.path.join(_sp, "nvidia", "*", "bin"))
if _dll_dirs:
    os.environ["PATH"] = ";".join(_dll_dirs) + ";" + os.environ.get("PATH", "")
    for d in _dll_dirs:
        try:
            os.add_dll_directory(d)
        except OSError:
            pass
