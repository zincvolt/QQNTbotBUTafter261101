from pathlib import Path
import importlib.util, sys
spec = importlib.util.spec_from_file_location("bfp", r"D:\QQNTBOT\scripts\build_furry_pack.py")
mod = importlib.util.module_from_spec(spec)
sys.modules["bfp"] = mod
spec.loader.exec_module(mod)
files = sorted(Path(r"D:\QQNTBOT\_downloads\furry-emoji").glob("*"))
pack = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugin_data\meme_manager\packs\furry-emoji\memes")
present = {p.name for p in pack.rglob("*") if p.is_file()}
exp = {}
for cat, idxs in mod.ASSIGN.items():
    for i in idxs:
        if i < len(files):
            exp[files[i].name] = cat
missing = {n: c for n, c in exp.items() if n not in present}
print("期望", len(exp), "实际", len(present), "缺失", len(missing))
for n, c in list(missing.items())[:10]:
    print("  ", c, n)
