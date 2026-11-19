import json
from pathlib import Path

DESC = {
    "吃喝": "吃东西、喝奶茶、端着快餐，饭点和闲聊时用",
    "困惑": "问号脸、歪头、看不懂，适合表示没听懂",
    "害羞": "脸红、捂脸、被夸了不好意思",
    "开心": "笑、兴奋、比耶，适合接好消息和打闹",
    "惊讶": "瞪眼、被吓一跳、愣住",
    "感谢": "鞠躬、比心、说谢谢，适合回应别人的好意",
    "拒绝": "摆手、摇头、不要，适合推掉事情",
    "无语": "翻白眼、脸垮下来、看傻子一样",
    "日常": "平常的动作和表情，适合随口接一句",
    "生气": "炸毛、凶人、拍桌，适合假装发火",
    "累了": "趴着、打哈欠、瘫着，适合说累了想躺",
    "难过": "哭、委屈、低落，适合认怂和求安慰",
    "未分类": "还没归类的表情，暂存区",
}

base = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugin_data\meme_manager\packs")
for name in ("furry", "unsorted"):
    pack = base / name
    memes = pack / "memes"
    if not memes.is_dir():
        continue
    dirs = sorted([d.name for d in memes.iterdir() if d.is_dir()])
    flat = {d: DESC.get(d, f"{d}类的兽人表情") for d in dirs}
    (pack / "memes_data.json").write_text(json.dumps(flat, ensure_ascii=False, indent=2), encoding="utf-8")
    man = pack / "manifest.json"
    m = json.loads(man.read_text(encoding="utf-8")) if man.exists() else {"schema_version": 1, "id": name, "name": name, "version": "1.0.0"}
    m["categories"] = {k: {"description": v} for k, v in flat.items()}
    man.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
    print(name, "->", len(flat), "条")
    for k, v in flat.items():
        print(f"   {k}: {v}")
