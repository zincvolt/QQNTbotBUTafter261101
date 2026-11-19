from pathlib import Path
p = Path(r"D:\QQNTBOT\dashboard\index.html")
s = p.read_text(encoding="utf-8")

panel = '''  <div class="panel wide">
    <h2>手动加记忆</h2>
    <div class="hint">勾选最近群聊里的消息，直接存成长期记忆（会走向量去重）</div>
    <div id="ltmList" style="max-height:280px;overflow:auto;margin-top:8px"><span class="hint">加载中…</span></div>
    <div style="margin-top:10px">
      <button class="primary" onclick="addSelectedMemories()">加入记忆</button>
      <span class="hint" id="ltmMsg"></span>
    </div>
  </div>

'''
anchor = '  <div class="panel">\n    <h2>最近记住的事'
if '手动加记忆' not in s:
    s = s.replace(anchor, panel + anchor, 1)
    print("panel inserted")

js = '''async function loadLtmRecent() {
  try {
    const r = await (await fetch('/api/ltm/recent?limit=40&t=' + Date.now())).json();
    document.getElementById('ltmList').innerHTML = r.items.length
      ? r.items.map(m => `<label style="display:flex;gap:8px;align-items:flex-start;padding:5px 0;border-bottom:1px solid var(--line);color:var(--text)">
          <input type="checkbox" class="ltmPick" data-uid="${esc(m.uid)}" data-text="${esc(m.text)}" style="margin-top:3px">
          <span style="flex:1"><span class="meta">${esc(m.at)} · QQ ${esc(m.uid)} · ${esc(m.name)}</span>${esc(m.text)}</span>
        </label>`).join('')
      : '<span class="hint">没有可用消息</span>';
  } catch (e) { console.error(e); }
}

async function addSelectedMemories() {
  const picked = [...document.querySelectorAll('.ltmPick:checked')].map(c => ({
    uid: c.dataset.uid, text: c.dataset.text
  }));
  if (!picked.length) { document.getElementById('ltmMsg').textContent = '先勾选几条'; return; }
  document.getElementById('ltmMsg').textContent = '写入中…';
  const r = await (await fetch('/api/ltm/add', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({items: picked})
  })).json();
  document.getElementById('ltmMsg').textContent = r.msg || (r.ok ? '已加入' : '失败');
  if (r.ok) refresh();
}

async function loadReply() {'''
if 'function loadLtmRecent' not in s:
    s = s.replace('async function loadReply() {', js, 1)
    print("js inserted")

if 'loadLtmRecent();' not in s:
    s = s.replace("loadReply();\nloadThinking();", "loadLtmRecent();\nloadReply();\nloadThinking();", 1)
    print("init hook")

p.write_text(s, encoding="utf-8")
