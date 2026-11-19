from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_ltm\main.py")
s = p.read_text(encoding="utf-8")

# 1) 频率
s = s.replace("SCAN_INTERVAL = 300  # 每 5 分钟扫一次群历史",
              "SCAN_INTERVAL = 1800  # 每 30 分钟扫一次群历史")
s = s.replace("SCAN_BUDGET = 3  # 每轮最多为几个人抽取记忆",
              "SCAN_BUDGET = 1  # 每轮最多为 1 个人抽取记忆")

# 2) 提示词：要求证据
old_start = s.index("EXTRACT_PROMPT = ")
old_end = s.index('"""', s.index('"""', old_start) + 3) + 3
new_prompt = '''EXTRACT_PROMPT = """从下面这段对话里提取关于「用户」的、可长期记住的稳定事实。

硬性要求：
- 必须是用户自己原话里明确说过的，不能是推测、补全或从上下文猜的
- 只收这五类：身份/称呼、长期偏好、固定习惯、和谁的关系、长期在做的事
- 不收：一次性闲聊、临时的情绪和状态、别人的事、任何你不确定的内容
- 每条事实不超过 30 字，且必须附上证据 evidence
- evidence 必须是用户原话里一字不差出现的片段（4~20 字），不能改写

只输出 JSON 数组，格式：
[{"fact": "用户的陈述", "evidence": "用户原话片段"}]
没有可记的就输出 []，不要任何解释。

对话：
用户：{user}
对方：{bot}
"""'''
s = s[:old_start] + new_prompt + s[old_end:]

# 3) 解析：校验证据
old_parse = '''        candidates = []
        for item in items:
            if not isinstance(item, str):
                continue
            text = item.strip().strip("-• ").strip()
            if 4 <= len(text) <= MAX_FACT_CHARS:
                candidates.append(text)'''
new_parse = '''        flat_user = re.sub(r"\\s+", "", user_text)
        banned = ("可能", "也许", "好像", "估计", "应该", "大概", "似乎")
        candidates = []
        for item in items:
            if isinstance(item, dict):
                text = str(item.get("fact", "")).strip()
                evidence = re.sub(r"\\s+", "", str(item.get("evidence", "")))
            else:
                continue
            # 证据必须能在用户原话里找到，否则视为编造
            if not evidence or evidence not in flat_user:
                logger.debug(f"[ltm] drop unverified fact: {text[:30]}")
                continue
            if any(word in text for word in banned):
                continue
            if not 6 <= len(text) <= MAX_FACT_CHARS:
                continue
            candidates.append(text)
            if len(candidates) >= 2:
                break'''
if old_parse in s:
    s = s.replace(old_parse, new_parse)
    print("parse block replaced")
else:
    print("WARN: parse block not found")

p.write_text(s, encoding="utf-8")
print("interval:", "SCAN_INTERVAL = 1800" in s)
print("budget  :", "SCAN_BUDGET = 1" in s)
print("prompt  :", "evidence" in s)
