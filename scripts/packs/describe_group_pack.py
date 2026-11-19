import json
from pathlib import Path

base = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugin_data\meme_manager")
pack = base / "packs" / "group-feed"
mpath = pack / "manifest.json"
m = json.loads(mpath.read_text(encoding="utf-8"))

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
}

dirs = sorted([d.name for d in (pack / "memes").iterdir() if d.is_dir()])
categories = {}
for name in dirs:
    categories[name] = {"description": DESC.get(name, f"{name}类的兽人表情")}

m["categories"] = categories
mpath.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
print("categories:", len(categories))
for k, v in categories.items():
    print(f"  {k}: {v['description']}")

rules_path = base / "selection_rules.json"
rules = json.loads(rules_path.read_text(encoding="utf-8"))
rules["rules"] = [r for r in rules.get("rules", []) if r.get("id") != "default"]
rules["rules"].insert(0, {"id": "default", "scope": "default", "pack_id": "group-feed"})
rules_path.write_text(json.dumps(rules, ensure_ascii=False, indent=2), encoding="utf-8")
print("rules:", rules["rules"])
