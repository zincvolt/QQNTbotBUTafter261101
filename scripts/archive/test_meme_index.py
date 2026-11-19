import importlib.util, sys
spec = importlib.util.spec_from_file_location("vc", r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_vision_context\main.py")
mod = importlib.util.module_from_spec(spec)
sys.modules["vc"] = mod
try:
    spec.loader.exec_module(mod)
except Exception as e:
    print("import err:", e)
    raise SystemExit
idx = mod.load_meme_index()
print("index size:", len(idx))
from collections import Counter
print(Counter((v[0], v[1]) for v in idx.values()).most_common(5))
