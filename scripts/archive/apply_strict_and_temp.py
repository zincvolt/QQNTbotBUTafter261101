import json
from pathlib import Path

# 1) 温度
cfg_path = Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json")
cfg = json.loads(cfg_path.read_text(encoding="utf-8-sig"))
body = cfg["provider"][0]["custom_extra_body"]
print("before:", body)
body["temperature"] = 0.55
body["top_p"] = 0.9
body["max_tokens"] = 80
cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
print("after :", body)

# 2) 在插件里追加"回答要求"，不改 persona.json
peer = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_peer\main.py")
s = peer.read_text(encoding="utf-8")

const = '''STRICT_HINT = (
    "\\n\\n（回答要求，优先于上面的写法偏好：一次最多两句、总共不超过50字；"
    "不写括号里的动作和神态；不确定的事实直接说不确定，不要编名字）"
)

'''
if "STRICT_HINT" not in s:
    s = s.replace("@filter\nclass Main", const + "@filter\nclass Main", 1)
    if "STRICT_HINT" not in s:
        # 兜底：插在第一个 @filter 装饰器之前
        idx = s.index("@filter")
        s = s[:idx] + const + s[idx:]

old = '''        if self._prompt_logged:
            return
        self._prompt_logged = True'''
new = '''        req.system_prompt = (req.system_prompt or "") + STRICT_HINT
        if self._prompt_logged:
            return
        self._prompt_logged = True'''
if old in s:
    s = s.replace(old, new)
    print("hint injected")
peer.write_text(s, encoding="utf-8")
