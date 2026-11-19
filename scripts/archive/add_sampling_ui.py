from pathlib import Path
p = Path(r"D:\QQNTBOT\dashboard\index.html")
s = p.read_text(encoding="utf-8")

panel = '''  <div class="panel wide">
    <h2>模型采样参数（保存后自动重启 AstrBot，约 10 秒）</h2>
    <div style="display:grid;gap:16px;margin-top:6px">
      <div>
        <div style="display:flex;justify-content:space-between;margin-bottom:6px">
          <span>温度 <span class="meta">越低越守设定，越高越发散</span></span>
          <b id="tempVal">–</b>
        </div>
        <input id="tempSlider" type="range" min="0.1" max="1.5" step="0.05" value="0.55" style="width:100%" oninput="document.getElementById('tempVal').textContent=this.value">
      </div>
      <div>
        <div style="display:flex;justify-content:space-between;margin-bottom:6px">
          <span>重复惩罚 <span class="meta">压口癖和复读，1.0 为关闭</span></span>
          <b id="rpVal">–</b>
        </div>
        <input id="rpSlider" type="range" min="1.0" max="1.5" step="0.01" value="1.0" style="width:100%" oninput="document.getElementById('rpVal').textContent=this.value">
      </div>
      <div>
        <div style="display:flex;justify-content:space-between;margin-bottom:6px">
          <span>单条上限 <span class="meta">token 数，80 约 55 个汉字</span></span>
          <b id="mtVal">–</b>
        </div>
        <input id="mtSlider" type="range" min="40" max="200" step="10" value="80" style="width:100%" oninput="document.getElementById('mtVal').textContent=this.value">
      </div>
      <div style="display:flex;gap:10px;align-items:center">
        <button class="primary" onclick="applySampling()">应用</button>
        <span class="hint" id="sampMsg"></span>
      </div>
    </div>
  </div>

'''

anchor = '  <div class="panel wide">\n    <h2>对话上下文'
if '模型采样参数' not in s:
    s = s.replace(anchor, panel + anchor, 1)
    print("panel inserted")

js = '''async function loadSampling() {
  try {
    const r = await (await fetch('/api/sampling?t=' + Date.now())).json();
    document.getElementById('tempSlider').value = r.temperature;
    document.getElementById('rpSlider').value = r.repeat_penalty;
    document.getElementById('mtSlider').value = r.max_tokens;
    document.getElementById('tempVal').textContent = r.temperature;
    document.getElementById('rpVal').textContent = r.repeat_penalty;
    document.getElementById('mtVal').textContent = r.max_tokens;
  } catch (e) {}
}

async function applySampling() {
  const body = {
    temperature: parseFloat(document.getElementById('tempSlider').value),
    repeat_penalty: parseFloat(document.getElementById('rpSlider').value),
    max_tokens: parseInt(document.getElementById('mtSlider').value, 10),
  };
  document.getElementById('sampMsg').textContent = '保存中…';
  const r = await (await fetch('/api/sampling', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify(body)
  })).json();
  document.getElementById('sampMsg').textContent = r.msg || (r.ok ? '已保存' : '失败');
}

async function loadContexts() {'''

if 'function loadSampling' not in s:
    s = s.replace('async function loadContexts() {', js, 1)
    print("js inserted")

if 'loadSampling();' not in s:
    s = s.replace('loadContexts();', 'loadSampling();\nloadContexts();', 1)
    print("init hook added")

p.write_text(s, encoding="utf-8")
