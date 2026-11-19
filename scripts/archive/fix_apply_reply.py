import re
from pathlib import Path

p = Path(r"D:\QQNTBOT\dashboard\index.html")
s = p.read_text(encoding="utf-8")

new_fn = r'''async function applyReply() {
  const el = (id) => document.getElementById(id);
  const chance = parseFloat((el('memeSlider') || {}).value || 0.3);
  const replyChance = parseFloat((el('replySlider') || {}).value || 1);
  const historyMinutes = parseFloat((el('histSlider') || {}).value || 30);
  const summon = ((el('summonBox') || {}).value || '')
    .split(/[,，\s]+/).map(x => x.trim()).filter(Boolean);
  const rules = ((el('rulesBox') || {}).value || '').split('\n')
    .map(line => line.trim()).filter(Boolean)
    .map(line => {
      const i = line.indexOf('=>');
      if (i < 0) return null;
      const pattern = line.slice(0, i).trim();
      const to = line.slice(i + 2).trim();
      return pattern ? { pattern, to } : null;
    }).filter(Boolean);
  el('replyMsg').textContent = '保存中…';
  const r = await (await fetch('/api/reply', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({
      meme_chance: chance,
      reply_chance: replyChance,
      history_minutes: historyMinutes,
      summon: summon,
      text_rules: rules
    })
  })).json();
  el('replyMsg').textContent = r.msg || (r.ok ? '已保存' : '失败');
  loadReply();
}

function fillDefaultRule() {
  const box = document.getElementById('rulesBox');
  if (!box) return;
  const line = '。(?=\\s|$) => ~';
  box.value = box.value.trim() ? box.value + '\n' + line : line;
}
'''

pat = re.compile(r"async function applyReply\(\) \{[\s\S]*?\n\}\n", re.M)
if pat.search(s):
    s = pat.sub(lambda m: new_fn, s, count=1)
    print("applyReply replaced")

old_btn = '        <button class="primary" onclick="applyReply()">保存</button>'
new_btn = ('        <button class="primary" onclick="applyReply()">保存</button>\n'
           '        <button onclick="fillDefaultRule()">填入默认规则</button>')
if "fillDefaultRule()" not in s:
    s = s.replace(old_btn, new_btn, 1)
    print("button added")

p.write_text(s, encoding="utf-8")
