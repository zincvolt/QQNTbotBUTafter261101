from pathlib import Path
p = Path(r"D:\QQNTBOT\dashboard\index.html")
s = p.read_text(encoding="utf-8")

# loadReply 容错：元素不存在就跳过
s = s.replace(
    "async function loadReply() {\n  const r = await (await fetch('/api/reply?t=' + Date.now())).json();",
    "async function loadReply() {\n  try {\n  const r = await (await fetch('/api/reply?t=' + Date.now())).json();",
)
s = s.replace(
    "  document.getElementById('rulesBox').value = (r.text_rules || [])\n    .map(x => `${x.pattern} => ${x.to}`).join('\\n');\n}",
    "  document.getElementById('rulesBox').value = (r.text_rules || [])\n    .map(x => `${x.pattern} => ${x.to}`).join('\\n');\n  } catch (e) { console.error('loadReply', e); }\n}",
)
# applyReply 里也做保护
s = s.replace(
    "  const chance = parseFloat(document.getElementById('memeSlider').value);",
    "  const chance = parseFloat((document.getElementById('memeSlider') || {}).value || 0.3);",
)
s = s.replace(
    "    reply_chance: parseFloat(document.getElementById('replySlider').value), text_rules: rules})",
    "    reply_chance: parseFloat((document.getElementById('replySlider') || {}).value || 1), text_rules: rules})",
)
# 初始化顺序改成逐个 try，互不影响
s = s.replace(
    "loadReply();\nloadSampling();",
    "try { await loadReply(); } catch (e) { console.error(e); }\n"
    "try { await loadSampling(); } catch (e) { console.error(e); }",
)
p.write_text(s, encoding="utf-8")
print("ui guarded")
