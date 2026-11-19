from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_peer\main.py")
s = p.read_text(encoding="utf-8")

# 1) 加载器改成正则字段
old_rules = '''        "text_rules": [
            {"find": str(r.get("find", "")), "to": str(r.get("to", ""))}
            for r in raw.get("text_rules", [])
            if isinstance(r, dict) and r.get("find")
        ],'''
new_rules = '''        "text_rules": [
            {"pattern": str(r.get("pattern", "")), "to": str(r.get("to", ""))}
            for r in raw.get("text_rules", [])
            if isinstance(r, dict) and r.get("pattern")
        ],'''
if old_rules in s:
    s = s.replace(old_rules, new_rules)
    print("loader -> regex")

# 2) 替换逻辑改成 re.sub
old_apply = '''        for rule in load_reply_config()["text_rules"]:
            for comp in result.chain:
                inner = getattr(comp, "text", None)
                if isinstance(inner, str) and rule["find"] in inner:
                    comp.text = inner.replace(rule["find"], rule["to"])'''
new_apply = '''        for rule in load_reply_config()["text_rules"]:
            try:
                pattern = re.compile(rule["pattern"])
            except re.error as exc:
                logger.warning(f"[peer] bad regex {rule['pattern']}: {exc}")
                continue
            for comp in result.chain:
                inner = getattr(comp, "text", None)
                if isinstance(inner, str):
                    comp.text = pattern.sub(rule["to"], inner)'''
if old_apply in s:
    s = s.replace(old_apply, new_apply)
    print("apply -> re.sub")

p.write_text(s, encoding="utf-8")
