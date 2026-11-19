from pathlib import Path
p = Path(r"D:\QQNTBOT\dashboard\index.html")
s = p.read_text(encoding="utf-8")

block = '''      <div>
        <div style="display:flex;justify-content:space-between;margin-bottom:6px">
          <span>每群回复预算 <span class="meta">10 分钟内最多回几条（@ 和喊名字也算在内）</span></span>
          <b id="budgetVal">–</b>
        </div>
        <input id="budgetSlider" type="range" min="1" max="30" step="1" style="width:100%" oninput="document.getElementById('budgetVal').textContent=this.value+' 条'">
      </div>
'''
anchor = '''      <div>
        <label>召唤词'''
if 'budgetSlider' not in s:
    s = s.replace(anchor, block + anchor, 1)
    print("budget slider inserted")

# 回填
s = s.replace(
    "  document.getElementById('summonBox').value = (r.summon || []).join(', ');",
    "  document.getElementById('budgetSlider').value = r.reply_budget || 8;\n"
    "  document.getElementById('budgetVal').textContent = (r.reply_budget || 8) + ' 条';\n"
    "  document.getElementById('summonBox').value = (r.summon || []).join(', ');",
)
# 提交
s = s.replace(
    "      history_minutes: historyMinutes,",
    "      history_minutes: historyMinutes,\n"
    "      reply_budget: parseInt((el('budgetSlider') || {}).value || 8, 10),",
)
p.write_text(s, encoding="utf-8")
print("committed:", "reply_budget: parseInt" in s)
