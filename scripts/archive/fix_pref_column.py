from pathlib import Path
p = Path(r"D:\QQNTBOT\dashboard\app.py")
s = p.read_text(encoding="utf-8")
s = s.replace(
    '"DELETE FROM preferences WHERE scope = \'umo\' AND name = ? "\n                "AND key = \'sel_conv_id\'",',
    '"DELETE FROM preferences WHERE scope = \'umo\' AND scope_id = ? "\n                "AND key = \'sel_conv_id\'",',
)
p.write_text(s, encoding="utf-8")
print("scope_id" in s)
