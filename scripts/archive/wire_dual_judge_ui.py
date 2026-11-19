from pathlib import Path

# 1) API 读写 dual_judge
p = Path(r"D:\QQNTBOT\dashboard\app.py")
s = p.read_text(encoding="utf-8")
s = s.replace(
    '''            "summon": read_json(JUDGE_FILE, {}).get("summon", []),''',
    '''            "summon": read_json(JUDGE_FILE, {}).get("summon", []),
            "dual_judge": bool(data.get("dual_judge", False)),''',
)
s = s.replace(
    '''    current["meme_chance"] = chance''',
    '''    if "dual_judge" in body:
        current["dual_judge"] = bool(body["dual_judge"])
        cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))
        current["dual_judge_model"] = cfg["provider"][0]["model"]
    current["meme_chance"] = chance''',
)
p.write_text(s, encoding="utf-8")
print("api dual:", "dual_judge" in s)

# 2) UI 回填与提交
h = Path(r"D:\QQNTBOT\dashboard\index.html")
t = h.read_text(encoding="utf-8")
t = t.replace(
    "  document.getElementById('budgetSlider').value = r.reply_budget || 8;",
    "  document.getElementById('dualJudgeBox').checked = !!r.dual_judge;\n"
    "  document.getElementById('budgetSlider').value = r.reply_budget || 8;",
)
t = t.replace(
    "      reply_budget: parseInt((el('budgetSlider') || {}).value || 8, 10),",
    "      reply_budget: parseInt((el('budgetSlider') || {}).value || 8, 10),\n"
    "      dual_judge: !!(el('dualJudgeBox') || {}).checked,",
)
h.write_text(t, encoding="utf-8")
print("ui dual:", "dualJudgeBox').checked" in t)
