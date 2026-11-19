from pathlib import Path
p = Path(r"D:\QQNTBOT\dashboard\index.html")
s = p.read_text(encoding="utf-8")
s = s.replace(".map(x => `${x.find} => ${x.to}`).join('\\n');", ".map(x => `${x.pattern} => ${x.to}`).join('\\n');")
s = s.replace("      return { find: line.slice(0, i).trim(), to: line.slice(i + 2).trim() };",
              "      return { pattern: line.slice(0, i).trim(), to: line.slice(i + 2).trim() };")
s = s.replace("原字符 => 替换成", "正则 => 替换成")
s = s.replace("例：<code>。 =&gt; ~</code> 会把句号换成波浪号；留空表示不替换",
              "例：<code>。(?=\\s|$) =&gt; ~</code> 只替换句末句号；<code>。 =&gt; ~</code> 替换所有句号")
p.write_text(s, encoding="utf-8")
print("ui patched")
