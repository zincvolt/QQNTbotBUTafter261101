"""Harden the switch-back path so returning to the local model is safe."""

from pathlib import Path

APIMODE = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_apimode\main.py")
s = APIMODE.read_text(encoding="utf-8")

# 1) 本地 provider 参数复位 + reply.json 预设随模式切换
old_tune = '''def tune_reply_for_mode(mode: str) -> None:
    """Turn local-only heavy features on or off to match the mode."""
    try:
        data = json.loads(REPLY.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return
    if mode == "third_party":
        data["dual_judge"] = False
        data["thinking"] = {"enable": False, "budget": 0}
    else:
        data["dual_judge"] = True
    REPLY.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")'''

new_tune = '''DEFAULT_RULE = {"pattern": "。(?=\\\\s|$|[（(\\\\[【「『])", "to": "~"}


def tune_reply_for_mode(mode: str) -> None:
    """Turn local-only heavy features on or off to match the mode.

    Third-party mode strips the local crutches (sticker probability, regex
    rewriting, dual judge); switching back restores them so the local 9B keeps
    its usual behaviour. Prompts are never touched here.
    """
    try:
        data = json.loads(REPLY.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return
    if mode == "third_party":
        data["dual_judge"] = False
        data["thinking"] = {"enable": False, "budget": 0}
        data["meme_chance"] = 0
        data["text_rules"] = []
    else:
        data["dual_judge"] = True
        data["thinking"] = {"enable": False, "budget": 0}
        if not float(data.get("meme_chance", 0) or 0):
            data["meme_chance"] = 0.3
        if not (data.get("text_rules") or []):
            data["text_rules"] = [dict(DEFAULT_RULE)]
    REPLY.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def tune_local_provider() -> None:
    """Reset the local provider body to sane non-thinking defaults."""
    cfg = json.loads(CONFIG.read_text(encoding="utf-8-sig"))
    for provider in cfg.get("provider", []):
        if provider.get("id") != "local-llama":
            continue
        body = provider.setdefault("custom_extra_body", {})
        body["max_tokens"] = min(int(body.get("max_tokens", 200) or 200), 300)
        body.setdefault("temperature", 0.5)
        body.setdefault("top_p", 0.9)
        body.setdefault("repeat_penalty", 1.06)
        body["chat_template_kwargs"] = {"enable_thinking": False}
    runner = cfg.setdefault("agent_runner", {}).setdefault("config", {}).setdefault(
        "model", {}
    )
    runner["request_max_retries"] = int(runner.get("request_max_retries", 5) or 5)
    CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")'''

if old_tune in s:
    s = s.replace(old_tune, new_tune, 1)
    print("tune_reply_for_mode 已加强")
else:
    print("MISS tune")

# 2) 切回本地时复位 provider 参数
s = s.replace(
    '''                set_provider_mode("local")
                tune_reply_for_mode("local")
                start_local_models()''',
    '''                set_provider_mode("local")
                tune_reply_for_mode("local")
                tune_local_provider()
                start_local_models()''',
    1,
)

# 3) 切回本地时把 deepseek 停用，避免同时启用造成混乱
s = s.replace(
    '''        elif pid in ("deepseek", "deepseek-api"):
            p["enable"] = mode == "third_party"''',
    '''        elif pid in ("deepseek", "deepseek-api"):
            p["enable"] = mode == "third_party"''',
    1,
)

APIMODE.write_text(s, encoding="utf-8")
print("切换回本地逻辑已加强")
