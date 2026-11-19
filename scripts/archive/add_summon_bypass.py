from pathlib import Path
import json

# 1) judge.json 加 summon 名单
jp = Path(r"D:\QQNTBOT\data\judge.json")
d = json.loads(jp.read_text(encoding="utf-8"))
d.setdefault("summon", ["阿灰", "小灰", "灰狼", "本灰"])
jp.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
print("summon:", d["summon"])

# 2) 核心：读 summon 并在判官之前直通
gp = Path(r"D:\QQNTBOT\apps\AstrBot\astrbot\builtin_stars\astrbot\group_chat_context.py")
s = gp.read_text(encoding="utf-8")

# 2a) load_judge_config 里带上 summon
old = '''        "force_patterns": [
            str(x).strip()
            for x in raw.get("force_patterns", [])
            if str(x).strip()
        ],
    }'''
new = '''        "force_patterns": [
            str(x).strip()
            for x in raw.get("force_patterns", [])
            if str(x).strip()
        ],
        "summon": [
            str(x).strip() for x in raw.get("summon", []) if str(x).strip()
        ],
    }'''
if old in s and '"summon"' not in s:
    s = s.replace(old, new, 1)
    print("summon added to config loader")

# 2b) need_active_reply：喊名字直通，不过概率闸
old2 = '''        match cfg["ar_method"]:
            case "possibility_reply":'''
new2 = '''        # 喊名字 = 明确在叫它，直接接，不经过判官和概率闸
        judge_cfg = load_judge_config()
        text = event.message_str or ""
        for word in judge_cfg.get("summon", []):
            if word and word in text:
                logger.info(f"group judge | 召唤词({word})直通 | {text[:30]}")
                return True

        match cfg["ar_method"]:
            case "possibility_reply":'''
if old2 in s and "召唤词" not in s:
    s = s.replace(old2, new2, 1)
    print("summon bypass added")

gp.write_text(s, encoding="utf-8")
