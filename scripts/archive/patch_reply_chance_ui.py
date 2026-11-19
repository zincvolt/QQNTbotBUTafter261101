from pathlib import Path
p = Path(r"D:\QQNTBOT\dashboard\index.html")
s = p.read_text(encoding="utf-8")

# 1) 面板里加回复概率滑块（放在表情概率之前）
slider = '''      <div>
        <div style="display:flex;justify-content:space-between;margin-bottom:6px">
          <span>主动回复概率 <span class="meta">判官说接之后，再按这个概率抽一次</span></span>
          <b id="replyVal">–</b>
        </div>
        <input id="replySlider" type="range" min="0" max="1" step="0.05" style="width:100%" oninput="document.getElementById('replyVal').textContent=Math.round(this.value*100)+'%'">
      </div>
'''
anchor = '''      <div>
        <div style="display:flex;justify-content:space-between;margin-bottom:6px">
          <span>附带表情概率'''
if 'replySlider' not in s:
    s = s.replace(anchor, slider + anchor, 1)
    print("slider inserted")

# 2) loadReply 里回填
s = s.replace(
    "  document.getElementById('memeSlider').value = r.meme_chance;",
    "  document.getElementById('replySlider').value = r.reply_chance;\n"
    "  document.getElementById('replyVal').textContent = Math.round(r.reply_chance * 100) + '%';\n"
    "  document.getElementById('memeSlider').value = r.meme_chance;",
)
# 3) applyReply 里带上
s = s.replace(
    "    body: JSON.stringify({meme_chance: chance, text_rules: rules})",
    "    body: JSON.stringify({meme_chance: chance, "
    "reply_chance: parseFloat(document.getElementById('replySlider').value), text_rules: rules})",
)
p.write_text(s, encoding="utf-8")
print("ui patched:", "replySlider" in s)
