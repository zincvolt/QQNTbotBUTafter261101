"""Add the optimization preset panel and memory-prompt editor to the page."""

from pathlib import Path

HTML = Path(r"D:\QQNTBOT\dashboard\index.html")
h = HTML.read_text(encoding="utf-8")

panel = '''  <div class="panel wide">
    <h2>本地优化 / 第三方精简（一键切换）</h2>
    <div class="hint" id="profileMode">加载中…</div>
    <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:12px">
      <button class="primary" onclick="applyProfile('local')">套用本地优化</button>
      <button class="primary" onclick="applyProfile('third')">套用第三方精简</button>
      <span class="hint" id="profileMsg"></span>
    </div>
    <div style="display:grid;gap:10px;margin-top:16px">
      <label style="display:flex;align-items:center;gap:10px;color:var(--text)">
        <input type="checkbox" id="profMeme" onchange="toggleProfile('meme')">
        附带表情（本地模型自己不会调工具，靠概率挂图）
        <span class="meta" id="profMemeMeta"></span>
      </label>
      <label style="display:flex;align-items:center;gap:10px;color:var(--text)">
        <input type="checkbox" id="profRules" onchange="toggleProfile('rules')">
        正则文本替换（句号换波浪号等；第三方也能靠提示词守规则）
        <span class="meta" id="profRulesMeta"></span>
      </label>
    </div>
    <div class="hint" style="margin-top:10px">
      第三方模型能自己调用 send_meme 工具、也能理解“别每句都用句号”这类提示词，
      所以切到 API 后建议关掉这两项，省 token 也更自然。
    </div>
  </div>

  <div class="panel wide">
    <h2>记忆提取提示词（写入 data\\ltm_prompt.txt）</h2>
    <label>必须保留 {user} 和 {bot} 两个占位符</label>
    <textarea id="ltmPrompt" rows="12" style="width:100%;background:#11141a;color:var(--text);border:1px solid var(--line);border-radius:9px;padding:10px;font-family:monospace;font-size:12.5px" placeholder="加载中…"></textarea>
    <div style="margin-top:12px;display:flex;gap:10px;align-items:center;flex-wrap:wrap">
      <button class="primary" onclick="saveLtmPrompt()">保存提示词</button>
      <button onclick="loadLtmPrompt()">重新载入</button>
      <span class="hint" id="ltmPromptMsg"></span>
    </div>
    <div class="hint">记忆质量基本由这段提示词决定；觉得记了莫名其妙的东西，就把“不收”那几条写狠一点</div>
  </div>

'''

if 'id="profMeme"' not in h:
    h = h.replace('  <div class="panel wide">\n    <h2>审查 · 额度', panel + '  <div class="panel wide">\n    <h2>审查 · 额度', 1)
    print("面板已插入")

js = '''
async function loadProfile() {
  try {
    const r = await (await fetch('/api/profile?t=' + Date.now())).json();
    document.getElementById('profileMode').textContent =
      '当前模式：' + (r.mode === 'third_party' ? '第三方 API' : '本地模型') +
      ' · 表情概率 ' + Math.round(r.meme_chance * 100) + '%' +
      ' · 文本规则 ' + r.rule_count + ' 条';
    document.getElementById('profMeme').checked = !!r.meme_on;
    document.getElementById('profRules').checked = !!r.rules_on;
    document.getElementById('profMemeMeta').textContent = r.meme_on ? '（已开）' : '（已关）';
    document.getElementById('profRulesMeta').textContent = r.rules_on ? '（' + r.rule_count + ' 条）' : '（已关）';
  } catch (e) { console.error('loadProfile', e); }
}

async function applyProfile(preset) {
  document.getElementById('profileMsg').textContent = '应用中…';
  const r = await (await fetch('/api/profile', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({preset})
  })).json();
  document.getElementById('profileMsg').textContent = r.msg || (r.ok ? '已应用' : '失败');
  loadProfile(); loadReply();
}

async function toggleProfile(which) {
  const body = which === 'meme'
    ? {meme_on: document.getElementById('profMeme').checked}
    : {rules_on: document.getElementById('profRules').checked};
  const r = await (await fetch('/api/profile', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body)
  })).json();
  document.getElementById('profileMsg').textContent = r.msg || '已更新';
  loadProfile();
}

async function loadLtmPrompt() {
  try {
    const r = await (await fetch('/api/ltm/prompt?t=' + Date.now())).json();
    document.getElementById('ltmPrompt').value = r.text || '';
    if (!r.has_placeholders) {
      document.getElementById('ltmPromptMsg').textContent = '警告：缺少占位符，提取会失败';
    }
  } catch (e) { console.error('loadLtmPrompt', e); }
}

async function saveLtmPrompt() {
  const text = document.getElementById('ltmPrompt').value;
  document.getElementById('ltmPromptMsg').textContent = '保存中…';
  const r = await (await fetch('/api/ltm/prompt', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({text})
  })).json();
  document.getElementById('ltmPromptMsg').textContent = r.msg || (r.ok ? '已保存' : '失败');
}

'''

if 'async function loadProfile()' not in h:
    h = h.replace('async function loadVisionMode() {', js + 'async function loadVisionMode() {', 1)
    print("JS 已加")

h = h.replace('loadVisionMode();', 'loadVisionMode();\nloadProfile();\nloadLtmPrompt();', 1)
HTML.write_text(h, encoding="utf-8")
print("index.html 已更新")
