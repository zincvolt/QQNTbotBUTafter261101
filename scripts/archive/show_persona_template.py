from pathlib import Path
import re
s = Path(r"D:\QQNTBOT\apps\AstrBot\astrbot\core\astr_main_agent.py").read_text(encoding="utf-8")
i = s.find("Persona Instructions")
print(s[max(0,i-700):i+400])
