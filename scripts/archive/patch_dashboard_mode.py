"""Make dashboard panels aware of local vs third-party API mode."""

from pathlib import Path

APP = Path(r"D:\QQNTBOT\dashboard\app.py")
s = APP.read_text(encoding="utf-8")

# ---------- 1) 端口表补 VL / OCR ----------
s = s.replace(
    '''    "judge": (8082, "判官模型"),
    "dash": (6190, "控制台"),''',
    '''    "judge": (8082, "判官模型"),
    "vl": (8085, "本地读图"),
    "ocr": (8083, "OCR"),
    "dash": (6190, "控制台"),''',
    1,
)

# ---------- 2) 模式判断助手 ----------
helper = '''MODE_FILE = ROOT / "data" / "api_mode.json"


def api_mode() -> str:
    """Return the active API mode: ``local`` or ``third_party``.

    Returns:
        The mode string from ``data/api_mode.json``.
    """
    try:
        return str(json.loads(MODE_FILE.read_text(encoding="utf-8")).get("mode", "local"))
    except (json.JSONDecodeError, OSError):
        return "local"


def active_provider(cfg: dict) -> dict:
    """Return the provider dict that currently serves chat.

    Args:
        cfg: Parsed AstrBot config.

    Returns:
        The DeepSeek provider in third-party mode, otherwise the local one.
    """
    target = "deepseek" if api_mode() == "third_party" else "local-llama"
    for provider in cfg.get("provider", []):
        if provider.get("id") == target:
            return provider
    return (cfg.get("provider") or [{}])[0]


'''

s = s.replace("def port_open(port: int) -> bool:", helper + "def port_open(port: int) -> bool:", 1)

# ---------- 3) 状态接口带上模式 ----------
s = s.replace(
    '''            {
                "components": comps,
                "memories": memory_total(),
                "activity": recent_activity(),
            }''',
    '''            {
                "mode": api_mode(),
                "components": comps,
                "memories": memory_total(),
                "activity": recent_activity(),
            }''',
    1,
)

# ---------- 4) 思维链面板 ----------
old_get_thinking = '''@app.get("/api/thinking")
def get_thinking() -> JSONResponse:
    """Return the thinking switch and token budget."""
    cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))
    body = cfg["provider"][0].get("custom_extra_body", {})
    kwargs = body.get("chat_template_kwargs", {}) or {}
    return JSONResponse(
        {
            "enable": bool(kwargs.get("enable_thinking", False)),
            "budget": int(body.get("max_tokens", 80)),
        }
    )'''
new_get_thinking = '''@app.get("/api/thinking")
def get_thinking() -> JSONResponse:
    """Return the thinking switch and token budget for the active provider."""
    cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))
    body = active_provider(cfg).get("custom_extra_body", {})
    if api_mode() == "third_party":
        thinking = body.get("thinking") or {}
        enable = str(thinking.get("type", "disabled")) == "enabled"
        effort = str(body.get("reasoning_effort", "high"))
        budget_map = {"low": 600, "high": 1200, "max": 2000}
        return JSONResponse(
            {
                "enable": enable,
                "budget": budget_map.get(effort, int(body.get("max_tokens", 1200))),
                "mode": "third_party",
                "effort": effort,
            }
        )
    kwargs = body.get("chat_template_kwargs", {}) or {}
    return JSONResponse(
        {
            "enable": bool(kwargs.get("enable_thinking", False)),
            "budget": int(body.get("max_tokens", 80)),
            "mode": "local",
        }
    )'''
if old_get_thinking in s:
    s = s.replace(old_get_thinking, new_get_thinking, 1)
    print("get_thinking 已模式化")

old_save_thinking = '''    cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))
    extra = cfg["provider"][0].setdefault("custom_extra_body", {})
    extra["chat_template_kwargs"] = {"enable_thinking": enable}
    extra["max_tokens"] = budget if enable else min(budget, 120)'''
new_save_thinking = '''    cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))
    provider = active_provider(cfg)
    extra = provider.setdefault("custom_extra_body", {})
    if api_mode() == "third_party":
        # DeepSeek：thinking.type + reasoning_effort，预算用强度档位表达
        extra["thinking"] = {"type": "enabled" if enable else "disabled"}
        if enable:
            effort = "low" if budget <= 800 else ("high" if budget <= 1500 else "max")
            extra["reasoning_effort"] = effort
            extra.pop("temperature", None)
        else:
            extra.pop("reasoning_effort", None)
            extra.setdefault("temperature", 0.8)
        extra["max_tokens"] = budget
    else:
        extra["chat_template_kwargs"] = {"enable_thinking": enable}
        extra["max_tokens"] = budget if enable else min(budget, 120)'''
if old_save_thinking in s:
    s = s.replace(old_save_thinking, new_save_thinking, 1)
    print("save_thinking 已模式化")

# ---------- 5) 采样面板 ----------
old_get_sampling = '''    cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))
    body = cfg["provider"][0].get("custom_extra_body", {})
    return JSONResponse(
        {
            "temperature": float(body.get("temperature", 0.7)),
            "top_p": float(body.get("top_p", 0.9)),
            "repeat_penalty": float(body.get("repeat_penalty", 1.0)),
            "max_tokens": int(body.get("max_tokens", 90)),
        }
    )'''
new_get_sampling = '''    cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))
    body = active_provider(cfg).get("custom_extra_body", {})
    return JSONResponse(
        {
            "temperature": float(body.get("temperature", 0.7)),
            "top_p": float(body.get("top_p", 0.9)),
            "repeat_penalty": float(body.get("repeat_penalty", 1.0)),
            "max_tokens": int(body.get("max_tokens", 90)),
            "mode": api_mode(),
        }
    )'''
if old_get_sampling in s:
    s = s.replace(old_get_sampling, new_get_sampling, 1)
    print("get_sampling 已模式化")

old_save_sampling = '''    cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))
    extra = cfg["provider"][0].setdefault("custom_extra_body", {})
    extra["temperature"] = temperature
    extra["top_p"] = top_p
    extra["repeat_penalty"] = repeat_penalty
    extra["max_tokens"] = max_tokens'''
new_save_sampling = '''    cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))
    extra = active_provider(cfg).setdefault("custom_extra_body", {})
    extra["temperature"] = temperature
    extra["top_p"] = top_p
    extra["max_tokens"] = max_tokens
    if api_mode() == "local":
        extra["repeat_penalty"] = repeat_penalty'''
if old_save_sampling in s:
    s = s.replace(old_save_sampling, new_save_sampling, 1)
    print("save_sampling 已模式化")

# ---------- 6) 主模型面板 ----------
old_models = '''@app.get("/api/models")
def models() -> JSONResponse:
    """List switchable presets and the active one."""
    return JSONResponse({"items": available_models(), "current": current_model()})'''
new_models = '''API_MODELS = ["deepseek-flash", "deepseek-v4-pro"]


@app.get("/api/models")
def models() -> JSONResponse:
    """List switchable models and the active one for the current mode."""
    if api_mode() == "third_party":
        cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))
        return JSONResponse(
            {
                "items": API_MODELS,
                "current": str(active_provider(cfg).get("model", "")),
                "mode": "third_party",
            }
        )
    return JSONResponse(
        {"items": available_models(), "current": current_model(), "mode": "local"}
    )'''
if old_models in s:
    s = s.replace(old_models, new_models, 1)
    print("models 已模式化")

old_switch = '''    name = str(body.get("model", "")).strip()
    if name not in available_models():
        return JSONResponse({"ok": False, "msg": f"没有这个预设：{name}"})
    cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))
    cfg["provider"][0]["model"] = name'''
new_switch = '''    name = str(body.get("model", "")).strip()
    third = api_mode() == "third_party"
    allowed = API_MODELS if third else available_models()
    if name not in allowed:
        return JSONResponse({"ok": False, "msg": f"没有这个预设：{name}"})
    cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))
    active_provider(cfg)["model"] = name'''
if old_switch in s:
    s = s.replace(old_switch, new_switch, 1)
    print("switch_model 已模式化")

APP.write_text(s, encoding="utf-8")
print("app.py 已更新")
