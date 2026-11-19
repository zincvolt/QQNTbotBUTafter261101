from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\astrbot\builtin_stars\astrbot\group_chat_context.py")
s = p.read_text(encoding="utf-8")

# 1) 预算加载器
loader = '''

def load_reply_budget() -> tuple[int, float]:
    """每群回复预算：(窗口内最大条数, 窗口秒数)。

    Returns:
        tuple[int, float]: (最大条数, 窗口秒数)，默认 (8, 600)。
    """
    try:
        raw = json.loads(REPLY_CONFIG_PATH.read_text(encoding="utf-8-sig"))
        limit = int(raw.get("reply_budget", 8))
        window = float(raw.get("reply_budget_minutes", 10)) * 60.0
    except (json.JSONDecodeError, OSError, TypeError, ValueError):
        return 8, 600.0
    return max(1, min(60, limit)), max(60.0, min(3600.0, window))

'''
if "def load_reply_budget" not in s:
    s = s.replace("\n\ndef load_autoreply_config()", loader + "\ndef load_autoreply_config()", 1)

# 2) 初始化计数器
old_init = "        self._record_times: dict[str, deque[float]] = defaultdict(deque)"
new_init = ("        self._record_times: dict[str, deque[float]] = defaultdict(deque)\n"
            "        self._reply_times: dict[str, deque[float]] = defaultdict(deque)")
if "_reply_times" not in s and old_init in s:
    s = s.replace(old_init, new_init, 1)

# 3) 记录一次已回复 + 判断是否超预算
helpers = '''
    def _note_reply(self, umo: str) -> None:
        """记一次回复（@、召唤词、随机插话都算）。"""
        self._reply_times[umo].append(time.time())

    def _over_budget(self, umo: str) -> tuple[bool, int]:
        """当前窗口内回复数是否已超预算。

        Returns:
            tuple[bool, int]: (是否超预算, 窗口内条数)。
        """
        limit, window = load_reply_budget()
        cutoff = time.time() - window
        times = self._reply_times[umo]
        while times and times[0] < cutoff:
            times.popleft()
        return len(times) >= limit, len(times)
'''
anchor = "    async def _judge_reply(self, event: AstrMessageEvent, cfg: dict) -> bool:"
if "_note_reply" not in s:
    s = s.replace(anchor, helpers + "\n" + anchor, 1)

p.write_text(s, encoding="utf-8")
print("budget helpers added")
