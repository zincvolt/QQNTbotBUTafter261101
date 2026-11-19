from pathlib import Path
p = Path(r"D:\QQNTBOT\dashboard\index.html")
s = p.read_text(encoding="utf-8")

# 1) 清掉误放进 clearContext 的调用
bad = """  if (!r.ok) { alert(r.msg); return; }
  try { await loadReply(); } catch (e) { console.error(e); }
try { await loadSampling(); } catch (e) { console.error(e); }
loadContexts();
}"""
good = """  if (!r.ok) { alert(r.msg); return; }
  loadContexts();
}"""
if bad in s:
    s = s.replace(bad, good, 1)
    print("clearContext cleaned")

# 2) 在真正的初始化块补回调用
old = """loadAutoReply();
loadPersona();"""
new = """loadAutoReply();
loadReply();
loadSampling();
loadPersona();"""
if "loadSampling();\nloadPersona" not in s:
    s = s.replace(old, new, 1)
    print("init calls restored")

p.write_text(s, encoding="utf-8")
