from pathlib import Path
p = Path(r"D:\QQNTBOT\dashboard\index.html")
s = p.read_text(encoding="utf-8")

panel = '''  <div class="panel wide">
    <h2>回复行为（保存即生效，无需重启）</h2>
    <div style="display:grid;gap:16px;margin-top:6px">
      <div>
        <div style="display:flex;justify-content:space-between;margin-bottom:6px">
          <span>附带表情概率 <span class="meta">正常回复时随机挂一张表情</span></span>
          <b id="memeVal">–</b>
        </div>
        <input id="memeSlider" type="range" min="0" max="1" step="0.05" style="width:100%" oninput="document.getElementById('memeVal').textContent=Math.round(this.value*100)+'%'">
      </div>
      <div>
        <label>文本替换（每行一条，格式：原字符 => 替换成）</label>
        <textarea id="rulesBox" rows="4" style="width:100%;background:#11141a;color:var(--text);border:1px solid var(--line);border-radius:9px;padding:10px;font-family:monospace;font-size:13px"></textarea>
        <div class="hint">例：<code>。 =&gt; ~</code> 会把句号换成波浪号；留空表示不替换</div>
      </div>
      <div style="display:flex;gap:10px;align-items:center">
        <button class="primary" onclick="applyReply()">保存</button>
        <span class="hint" id="replyMsg"></span>
      </div>
    </div>
  </div>

'''

anchor = '  <div class="panel wide">\n    <h2>模型采样参数'
if '回复行为' not in s:
    s = s.replace(anchor, panel + anchor, 1)
    print("panel inserted")

js = '''async function loadReply() {
  const r = await (await fetch('/api/reply?t=' + Date.now())).json();
  document.getElementById('memeSlider').value = r.meme_chance;
  document.getElementById('memeVal').textContent = Math.round(r.meme_chance * 100) + '%';
  document.getElementById('rulesBox').value = (r.text_rules || [])
    .map(x => `${x.find} => ${x.to}`).join('\\n');
}

async function applyReply() {
  const chance = parseFloat(document.getElementById('memeSlider').value);
  const rules = document.getElementById('rulesBox').value.split('\\n')
    .map(line => line.trim()).filter(Boolean)
    .map(line => {
      const i = line.indexOf('=>');
      if (i < 0) return null;
      return { find: line.slice(0, i).trim(), to: line.slice(i + 2).trim() };
    }).filter(Boolean);
  document.getElementById('replyMsg').textContent = '保存中…';
  const r = await (await fetch('/api/reply', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({meme_chance: chance, text_rules: rules})
  })).json();
  document.getElementById('replyMsg').textContent = r.msg || (r.ok ? '已保存' : '失败');
}

async function loadSampling() {'''

if 'function loadReply' not in s:
    s = s.replace('async function loadSampling() {', js, 1)
    print("js inserted")

if 'loadReply();' not in s:
    s = s.replace('loadSampling();', 'loadReply();\nloadSampling();', 1)
    print("init hook")

p.write_text(s, encoding="utf-8")
