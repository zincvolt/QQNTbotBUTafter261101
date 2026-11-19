from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\astrbot\builtin_stars\astrbot\group_chat_context.py")
s = p.read_text(encoding="utf-8")
old = "        self._record_ids: dict[str, deque[str]] = defaultdict(deque)"
new = ("        self._record_ids: dict[str, deque[str]] = defaultdict(deque)\n"
       "        self._record_times: dict[str, deque[float]] = defaultdict(deque)")
if "_record_times" not in s.split("self._record_ids")[0] and old in s:
    s = s.replace(old, new, 1)
    p.write_text(s, encoding="utf-8")
    print("init added")
else:
    print("already or pattern missing")
