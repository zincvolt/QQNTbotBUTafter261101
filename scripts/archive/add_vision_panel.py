"""Add the vision management panel to the dashboard page."""

from pathlib import Path

HTML = Path(r"D:\QQNTBOT\dashboard\index.html")
h = HTML.read_text(encoding="utf-8")

panel = '''  <div class="panel wide">
    <h2>识图（本地 VL / 第三方 / 关闭）</h2>
    <div class="hint" id="vmState">加载中…</div>
    <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:12px">
      <button id="vmLocal" onclick="setVisionMode('local')">本地 VL 读图</button>
      <button id="vmApi" onclick="setVisionMode('third_party')">交给第三方看图</button>
      <button id="vmOff" onclick="setVisionMode('off')">关闭读图</button>
    </div>
    <div style="margin-top:16px;display:flex;gap:10px;align-items:center;flex-wrap:wrap">
      <button onclick="vlControl('start')">启动本地 VL</button>
      <button onclick="vlControl('stop')">停止本地 VL</button>
      <span class="hint" id="vmMsg"></span>
    </div>
    <div class="hint" style="margin-top:10px">
      本地 VL 在第三方模式下会把图转成文字再发出去（不耗 token）；关闭读图则图片直接忽略。
      切到第三方 API 时，聊天/OCR/识图三个本地模型会被自动卸载。
    </div>
  </div>

'''

if 'id="vmState"' not in h:
    h = h.replace('  <div class="panel wide">\n    <h2>图片理解', panel + '  <div class="panel wide">\n    <h2>图片理解', 1)
    print("识图面板已插入")

js = '''
async function loadVisionMode() {
  try {
    const r = await (await fetch('/api/visionmode?t=' + Date.now())).json();
    const names = {local:'本地 VL 读图', third_party:'第三方看图', off:'关闭读图'};
    document.getElementById('vmState').textContent =
      '当前：' + (names[r.mode] || r.mode) +
      ' · 本地 VL ' + (r.up ? '在线' : '离线') +
      ' · 模型 ' + r.model + ' · 端口 ' + r.port +
      ' · 主模型模式 ' + (r.api_mode === 'third_party' ? '第三方' : '本地');
    for (const [id, mode] of [['vmLocal','local'],['vmApi','third_party'],['vmOff','off']]) {
      const btn = document.getElementById(id);
      const active = r.mode === mode;
      btn.className = active ? 'primary' : '';
      btn.style.opacity = active ? 1 : 0.75;
    }
  } catch (e) { console.error('loadVisionMode', e); }
}

async function setVisionMode(mode) {
  const r = await (await fetch('/api/visionmode', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({mode})
  })).json();
  document.getElementById('vmMsg').textContent = r.msg || (r.ok ? '已切换' : '失败');
  loadVisionMode();
}

async function vlControl(action) {
  document.getElementById('vmMsg').textContent = action === 'start' ? '启动中…' : '停止中…';
  const r = await (await fetch('/api/vl/' + action, {method: 'POST'})).json();
  document.getElementById('vmMsg').textContent = r.msg || (r.ok ? '完成' : '失败');
  setTimeout(loadVisionMode, 1500);
}

'''

if 'async function loadVisionMode()' not in h:
    h = h.replace('async function loadGuard() {', js + 'async function loadGuard() {', 1)
    print("识图 JS 已加")

h = h.replace('loadGuard();', 'loadGuard();\nloadVisionMode();', 1)
HTML.write_text(h, encoding="utf-8")
print("index.html 已更新")
