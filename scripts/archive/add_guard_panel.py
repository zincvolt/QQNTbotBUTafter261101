"""Add the guard panel (review / quota / save-token / history slider) to the dashboard."""

from pathlib import Path

APP = Path(r"D:\QQNTBOT\dashboard\app.py")
HTML = Path(r"D:\QQNTBOT\dashboard\index.html")

# ---------------- app.py: /api/guard ----------------
s = APP.read_text(encoding="utf-8")

endpoint = '''
GUARD_FILE = ROOT / "data" / "api_mode.json"


def read_guard() -> dict:
    """Return guard settings with defaults filled in.

    Returns:
        Dict with mode, review_groups, daily_limit, used, save_token, history_keep.
    """
    try:
        state = json.loads(GUARD_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        state = {}
    state.setdefault("review_groups", {})
    state.setdefault("daily_limit", 200000)
    state.setdefault("used", {"date": "", "tokens": 0})
    state.setdefault("save_token", True)
    state.setdefault("history_keep", 10)
    state["mode"] = api_mode()
    return state


@app.get("/api/guard")
def get_guard() -> JSONResponse:
    """Return review switches, quota, save-token flag and history window."""
    state = read_guard()
    cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))
    groups = cfg.get("platform_settings", {}).get("groups", {}).get("id", [])
    return JSONResponse(
        {
            "mode": state["mode"],
            "groups": groups,
            "review_groups": state.get("review_groups", {}),
            "daily_limit": state.get("daily_limit", 0),
            "used": state.get("used", {}),
            "save_token": bool(state.get("save_token", True)),
            "history_keep": int(state.get("history_keep", 10)),
        }
    )


@app.post("/api/guard")
async def save_guard(request: Request) -> JSONResponse:
    """Save review switches, quota and save-token settings (no restart needed)."""
    body = await request.json()
    state = read_guard()
    state.pop("mode", None)

    if "review_groups" in body and isinstance(body["review_groups"], dict):
        state["review_groups"] = {
            str(k): bool(v) for k, v in body["review_groups"].items()
        }
    if "daily_limit" in body:
        try:
            state["daily_limit"] = max(0, int(body["daily_limit"]))
        except (TypeError, ValueError):
            return JSONResponse({"ok": False, "msg": "额度必须是数字"})
    if "save_token" in body:
        state["save_token"] = bool(body["save_token"])
    if "history_keep" in body:
        try:
            state["history_keep"] = max(2, min(40, int(body["history_keep"])))
        except (TypeError, ValueError):
            return JSONResponse({"ok": False, "msg": "历史条数不对"})

    GUARD_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    return JSONResponse({"ok": True, "msg": "已保存（立即生效）"})


'''

anchor = '@app.get("/api/water")'
if '/api/guard' not in s:
    s = s.replace(anchor, endpoint + anchor, 1)
    APP.write_text(s, encoding="utf-8")
    print("app.py: /api/guard 已加")

# ---------------- index.html: 面板 ----------------
h = HTML.read_text(encoding="utf-8")

panel = '''  <div class="panel wide">
    <h2>审查 · 额度 · 省 token（第三方模式生效）</h2>
    <div class="hint" id="guardMode">加载中…</div>
    <div class="two" style="margin-top:12px">
      <div>
        <label>本群审查开关</label>
        <div class="plist" id="reviewList"><span class="hint">加载中…</span></div>
        <div class="hint">命中 data\\review_words.txt 里的词就把整条回复替换掉；只有第三方模式生效</div>
      </div>
      <div>
        <label>每日额度（tokens，0 = 不限）</label>
        <input id="quotaBox" type="number" min="0" step="10000" placeholder="200000"
          style="width:100%;background:#11141a;color:var(--text);border:1px solid var(--line);border-radius:9px;padding:9px 12px;font-size:13px">
        <div class="hint" id="quotaUsed">今日已用 –</div>

        <label style="margin-top:16px;display:flex;align-items:center;gap:10px;color:var(--text)">
          <input type="checkbox" id="saveTokenBox">
          省 token 模式（关闭后历史按完整上下文发送）
        </label>

        <div style="margin-top:14px">
          <div style="display:flex;justify-content:space-between;margin-bottom:6px">
            <span>历史消息数量 <span class="meta">省 token 时只发最近 N 条</span></span>
            <b id="histKeepVal">–</b>
          </div>
          <input id="histKeep" type="range" min="2" max="40" step="1" style="width:100%"
            oninput="document.getElementById('histKeepVal').textContent=this.value+' 条'">
        </div>
      </div>
    </div>
    <div style="margin-top:14px">
      <button class="primary" onclick="saveGuardConfig()">保存</button>
      <span class="hint" id="guardMsg"></span>
    </div>
  </div>

'''

if 'id="reviewList"' not in h:
    h = h.replace('  <div class="panel wide">\n    <h2>人格', panel + '  <div class="panel wide">\n    <h2>人格', 1)
    print("index.html: 面板已插入")

# ---------------- index.html: JS ----------------
js = '''
async function loadGuard() {
  try {
    const r = await (await fetch('/api/guard?t=' + Date.now())).json();
    const modeText = r.mode === 'third_party'
      ? '当前模式：第三方 API（审查与额度生效）'
      : '当前模式：本地模型（审查与额度不生效）';
    document.getElementById('guardMode').textContent = modeText;
    const groups = r.groups || [];
    document.getElementById('reviewList').innerHTML = groups.length
      ? groups.map(g => `<label style="display:flex;gap:8px;align-items:center;padding:4px 0;color:var(--text)">
          <input type="checkbox" class="reviewPick" data-gid="${esc(g)}" ${r.review_groups[g] ? 'checked' : ''}>
          <span>${esc(g)}</span></label>`).join('')
      : '<span class="hint">白名单里还没有群</span>';
    document.getElementById('quotaBox').value = r.daily_limit || 0;
    const used = r.used || {};
    document.getElementById('quotaUsed').textContent =
      '今日已用 ' + (used.tokens || 0) + ' tokens' + (used.date ? '（' + used.date + '）' : '');
    document.getElementById('saveTokenBox').checked = !!r.save_token;
    document.getElementById('histKeep').value = r.history_keep || 10;
    document.getElementById('histKeepVal').textContent = (r.history_keep || 10) + ' 条';
  } catch (e) { console.error('loadGuard', e); }
}

async function saveGuardConfig() {
  const review = {};
  document.querySelectorAll('.reviewPick').forEach(c => { review[c.dataset.gid] = c.checked; });
  const body = {
    review_groups: review,
    daily_limit: parseInt(document.getElementById('quotaBox').value || '0', 10),
    save_token: document.getElementById('saveTokenBox').checked,
    history_keep: parseInt(document.getElementById('histKeep').value, 10)
  };
  document.getElementById('guardMsg').textContent = '保存中…';
  const r = await (await fetch('/api/guard', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body)
  })).json();
  document.getElementById('guardMsg').textContent = r.msg || (r.ok ? '已保存' : '失败');
}

'''

if 'async function loadGuard()' not in h:
    h = h.replace('async function loadThinking() {', js + 'async function loadThinking() {', 1)
    print("index.html: JS 已加")

# init 里加载
h = h.replace('loadThinking();', 'loadThinking();\nloadGuard();', 1)

# ---------------- 置灰不支持的功能 ----------------
h = h.replace(
    '''    document.getElementById('rpVal').textContent = r.repeat_penalty;
    document.getElementById('mtVal').textContent = r.max_tokens;''',
    '''    document.getElementById('rpVal').textContent = r.repeat_penalty;
    document.getElementById('mtVal').textContent = r.max_tokens;

    // 第三方模式：repeat_penalty 不支持，置灰
    const api = r.mode === 'third_party';
    const rp = document.getElementById('rpSlider');
    rp.disabled = api;
    rp.style.opacity = api ? 0.35 : 1;
    const rpNote = document.getElementById('rpVal');
    rpNote.textContent = api ? 'API 不支持' : r.repeat_penalty;''',
    1,
)

h = h.replace(
    '''    document.getElementById('thinkBudget').value = r.budget;
    document.getElementById('thinkBudgetVal').textContent = r.budget + ' tok';''',
    '''    document.getElementById('thinkBudget').value = r.budget;
    document.getElementById('thinkBudgetVal').textContent = r.budget + ' tok';

    // 第三方模式：双判官要本地 9B，按规定停用；预算改用强度档
    const api = r.mode === 'third_party';
    const dj = document.getElementById('dualJudgeBox');
    dj.disabled = api;
    dj.style.opacity = api ? 0.35 : 1;
    if (api) {
      dj.checked = false;
      document.getElementById('thinkBudgetVal').textContent =
        ({low:'低', high:'中', max:'高'}[r.effort] || '中') + '（reasoning_effort）';
      document.getElementById('thinkBudget').disabled = true;
      document.getElementById('thinkBudget').style.opacity = 0.35;
    }''',
    1,
)

HTML.write_text(h, encoding="utf-8")
print("index.html 已更新")
