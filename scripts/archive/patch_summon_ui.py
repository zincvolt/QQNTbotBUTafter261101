from pathlib import Path
p = Path(r"D:\QQNTBOT\dashboard\index.html")
s = p.read_text(encoding="utf-8")

# 1) 面板加两个输入：召唤词 + 上下文时间窗
block = '''      <div>
        <label>召唤词（逗号分隔，命中就直接回，不看概率闸）</label>
        <input id="summonBox" type="text" placeholder="阿灰, 小灰, 灰狼"
          style="width:100%;background:#11141a;color:var(--text);border:1px solid var(--line);border-radius:9px;padding:9px 12px;font-size:13px">
      </div>
      <div>
        <div style="display:flex;justify-content:space-between;margin-bottom:6px">
          <span>群上下文时间窗 <span class="meta">只把最近 N 分钟的群聊喂给模型</span></span>
          <b id="histVal">–</b>
        </div>
        <input id="histSlider" type="range" min="5" max="120" step="5" style="width:100%" oninput="document.getElementById('histVal').textContent=this.value+' 分钟'">
      </div>
'''
anchor = '''      <div>
        <div style="display:flex;justify-content:space-between;margin-bottom:6px">
          <span>附带表情概率'''
if 'summonBox' not in s:
    s = s.replace(anchor, block + anchor, 1)
    print("inputs inserted")

# 2) loadReply 回填
s = s.replace(
    "  document.getElementById('memeSlider').value = r.meme_chance;",
    "  document.getElementById('summonBox').value = (r.summon || []).join(', ');\n"
    "  document.getElementById('histSlider').value = r.history_minutes || 30;\n"
    "  document.getElementById('histVal').textContent = (r.history_minutes || 30) + ' 分钟';\n"
    "  document.getElementById('memeSlider').value = r.meme_chance;",
)

# 3) applyReply 提交
s = s.replace(
    "    reply_chance: parseFloat((document.getElementById('replySlider') || {}).value || 1), text_rules: rules})",
    "    reply_chance: parseFloat((document.getElementById('replySlider') || {}).value || 1),\n"
    "    history_minutes: parseFloat(document.getElementById('histSlider').value),\n"
    "    summon: document.getElementById('summonBox').value.split(/[,，\\s]+/).filter(Boolean),\n"
    "    text_rules: rules})",
)
p.write_text(s, encoding="utf-8")
print("ui patched")
