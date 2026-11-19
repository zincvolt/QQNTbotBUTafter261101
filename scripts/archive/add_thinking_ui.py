from pathlib import Path
p = Path(r"D:\QQNTBOT\dashboard\index.html")
s = p.read_text(encoding="utf-8")

panel = '''  <div class="panel wide">
    <h2>判官与思维链</h2>
    <div style="display:grid;gap:14px;margin-top:6px">
      <label style="display:flex;align-items:center;gap:10px;color:var(--text)">
        <input type="checkbox" id="dualJudgeBox">
        双判官（1.5B 判完再由 9B 复核，两次都同意才回）
      </label>
      <div class="hint">开启后每次"疑似要回"会多花约 1.2~1.6 秒；9B 只在 1.5B 判 1 时才被调用</div>
      <label style="display:flex;align-items:center;gap:10px;color:var(--text)">
        <input type="checkbox" id="thinkBox">
        开启模型思考链（会慢很多，群聊不建议）
      </label>
      <div>
        <div style="display:flex;justify-content:space-between;margin-bottom:6px">
          <span>思考预算 <span class="meta">总输出 token 上限；当前模型不认 thinking_budget，只能控总长</span></span>
          <b id="thinkBudgetVal">–</b>
        </div>
        <input id="thinkBudget" type="range" min="200" max="3000" step="100" style="width:100%" oninput="document.getElementById('thinkBudgetVal').textContent=this.value+' tok'">
      </div>
      <div style="display:flex;gap:10px;align-items:center">
        <button class="primary" onclick="applyThinking()">保存（重启 AstrBot）</button>
        <span class="hint" id="thinkMsg"></span>
      </div>
    </div>
  </div>

'''

anchor = '  <div class="panel wide">\n    <h2>回复行为'
if '判官与思维链' not in s:
    s = s.replace(anchor, panel + anchor, 1)
    print("panel inserted")

js = '''async function loadThinking() {
  try {
    const r = await (await fetch('/api/thinking?t=' + Date.now())).json();
    document.getElementById('thinkBox').checked = r.enable;
    document.getElementById('thinkBudget').value = r.budget;
    document.getElementById('thinkBudgetVal').textContent = r.budget + ' tok';
  } catch (e) { console.error(e); }
}

async function applyThinking() {
  const body = {
    enable: document.getElementById('thinkBox').checked,
    budget: parseInt(document.getElementById('thinkBudget').value, 10)
  };
  document.getElementById('thinkMsg').textContent = '保存中…';
  const r = await (await fetch('/api/thinking', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify(body)
  })).json();
  document.getElementById('thinkMsg').textContent = r.msg || (r.ok ? '已保存' : '失败');
}

async function loadReply() {'''
if 'function loadThinking' not in s:
    s = s.replace('async function loadReply() {', js, 1)
    print("js inserted")

if 'loadThinking();' not in s:
    s = s.replace("loadReply();\nloadSampling();", "loadReply();\nloadThinking();\nloadSampling();", 1)
    print("init hook")

p.write_text(s, encoding="utf-8")
