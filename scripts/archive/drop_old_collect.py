from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_vision_context\main.py")
s = p.read_text(encoding="utf-8")
start = s.index("    async def _collect(self, ref: str) -> None:")
end = s.index("    @filter.on_llm_request()", start)
s = s[:start] + s[end:]
p.write_text(s, encoding="utf-8")
print("removed old _collect, lines now:", len(s.splitlines()))
