"""一次性配置 AstrBot：接入本地 llama.cpp 与 LLBot(OneBot v11)。

用法：
    .venv\\Scripts\\python.exe ..\\..\\scripts\\patch_astrbot_config.py
运行前请先停掉 AstrBot，运行后再启动，避免运行中被覆盖。
"""

import json
import sys
from pathlib import Path

ROOT = Path(r"D:\QQNTBOT\apps\AstrBot")
sys.path.insert(0, str(ROOT))

from astrbot.core.utils.auth_password import hash_dashboard_password  # noqa: E402

CFG = ROOT / "data" / "cmd_config.json"

provider_id = "local-llama"
model_name = "Grey-9B-Heretic"

cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))

# ---- 1. 模型：指向本地 llama.cpp 路由 ----
cfg["provider"] = [
    {
        "id": provider_id,
        "provider": "openai",
        "type": "openai_chat_completion",
        "provider_type": "chat_completion",
        "enable": True,
        "key": ["sk-llm-7d41c9e2"],
        "api_base": "http://127.0.0.1:8080/v1",
        "model": model_name,
        "timeout": 180,
        "proxy": "",
        "custom_headers": {},
    }
]
cfg["provider_sources"] = []
cfg["agent_runner"]["config"]["model"]["provider_id"] = provider_id

# ---- 2. 平台：OneBot v11 反向 WS（AstrBot 当服务端，LLBot 连进来）----
cfg["platform"] = [
    {
        "id": "qq",
        "type": "aiocqhttp",
        "enable": True,
        "ws_reverse_host": "127.0.0.1",
        "ws_reverse_port": 6199,
        "ws_reverse_token": "",
    }
]

# ---- 3. 上下文长度：24 轮滚动 + 溢出时 LLM 压缩 ----
comp = cfg["agent_runner"]["config"]["compression"]
comp["max_turns"] = 24
comp["trim_turns"] = 2
comp["overflow_strategy"] = "llm_compress"
comp["keep_recent_ratio"] = 0.15
comp["fallback_max_tokens"] = 8000

# ---- 4. 平台行为：按会话隔离上下文、分段回复像真人 ----
ps = cfg["platform_settings"]
ps["unique_session"] = True
ps["reply_with_mention"] = False
ps["reply_with_quote"] = False
ps["friend_message_needs_wake_prefix"] = False  # 私聊直接回
ps["ignore_bot_self_message"] = True
ps["segmented_reply"]["enable"] = True
ps["segmented_reply"]["interval"] = "0.8,2.0"

# ---- 5. 群聊：只记录不打扰 + 小概率主动接话 ----
ltm = cfg["provider_ltm_settings"]
ltm["group_message_history_enable"] = True
ltm["group_message_history_max_cnt"] = 200
ltm["group_message_max_cnt"] = 1000
ltm["active_reply"]["enable"] = True
ltm["active_reply"]["method"] = "possibility_reply"
ltm["active_reply"]["possibility_reply"] = 0.06
ltm["active_reply"]["whitelist"] = []

# ---- 6. 唤醒前缀：@ 必回；"/" 命令前缀保留 ----
cfg["wake_prefix"] = ["/"]

# ---- 7. 面板：只监听本机 + 固定密码 ----
dash = cfg["dashboard"]
dash["host"] = "127.0.0.1"
dash["username"] = "astrbot"
dash["pbkdf2_password"] = hash_dashboard_password("qqbot2026")
dash["password_change_required"] = False

CFG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
print("patched:", CFG)
print("provider:", cfg["provider"][0]["id"], cfg["provider"][0]["model"])
print("platform:", cfg["platform"][0]["type"], cfg["platform"][0]["ws_reverse_port"])
print("active_reply possibility:", ltm["active_reply"]["possibility_reply"])
