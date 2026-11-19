"""Make every component agree on which provider is actually serving chat.

The WebUI switches providers through agent_runner.config.model.provider_id, while
our plugins looked at data/api_mode.json. They drifted: the bot was already on
DeepSeek but the dashboard/plugins still thought "local".
"""

from pathlib import Path

CONFIG_REL = r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json"


def patch(path: str, replacements: list[tuple[str, str]]) -> None:
    """Apply literal replacements to one file."""
    file = Path(path)
    text = file.read_text(encoding="utf-8")
    for old, new in replacements:
        if old in text:
            text = text.replace(old, new, 1)
            print(f"  ok  {file.name}: {old.strip().splitlines()[0][:48]}")
        else:
            print(f"  MISS {file.name}: {old.strip().splitlines()[0][:48]}")
    file.write_text(text, encoding="utf-8")


# ---------- 1) dashboard：模式从配置推 ----------
patch(r"D:\QQNTBOT\dashboard\app.py", [(
    '''def api_mode() -> str:
    """Return the active API mode: ``local`` or ``third_party``.

    Returns:
        The mode string from ``data/api_mode.json``.
    """
    try:
        return str(json.loads(MODE_FILE.read_text(encoding="utf-8")).get("mode", "local"))
    except (json.JSONDecodeError, OSError):
        return "local"''',
    '''def api_mode() -> str:
    """Return the mode implied by the provider actually serving chat.

    The WebUI switches providers via agent_runner, so that is the source of
    truth; the json file is only a hint from the /切换 command.

    Returns:
        ``third_party`` when DeepSeek is the chat provider, else ``local``.
    """
    try:
        cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))
        model = (cfg.get("agent_runner", {}).get("config", {}).get("model", {}))
        provider_id = str(model.get("provider_id", ""))
        if provider_id:
            return "third_party" if "deepseek" in provider_id else "local"
    except (json.JSONDecodeError, OSError):
        pass
    try:
        return str(json.loads(MODE_FILE.read_text(encoding="utf-8")).get("mode", "local"))
    except (json.JSONDecodeError, OSError):
        return "local"''',
)])

# ---------- 2) peer：第三方判断也看配置 ----------
patch(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_peer\main.py", [(
    '''def _third_party_mode() -> bool:
    """Return True when the bot is switched to the third-party API.

    Returns:
        Whether ``data/api_mode.json`` says ``third_party``.
    """
    import json
    from pathlib import Path as _Path

    state = _Path(r"D:\\QQNTBOT\\data\\api_mode.json")
    if not state.exists():
        return False
    try:
        return json.loads(state.read_text(encoding="utf-8")).get("mode") == "third_party"
    except Exception:  # noqa: BLE001
        return False''',
    '''def _third_party_mode() -> bool:
    """Return True when the chat provider is the third-party API.

    Returns:
        Whether agent_runner currently points at DeepSeek.
    """
    import json
    from pathlib import Path as _Path

    try:
        cfg = json.loads(
            _Path(r"D:\\QQNTBOT\\apps\\AstrBot\\data\\cmd_config.json").read_text(
                encoding="utf-8-sig"
            )
        )
        pid = str(
            cfg.get("agent_runner", {})
            .get("config", {})
            .get("model", {})
            .get("provider_id", "")
        )
        if pid:
            return "deepseek" in pid
    except Exception:  # noqa: BLE001
        pass
    state = _Path(r"D:\\QQNTBOT\\data\\api_mode.json")
    if not state.exists():
        return False
    try:
        return json.loads(state.read_text(encoding="utf-8")).get("mode") == "third_party"
    except Exception:  # noqa: BLE001
        return False''',
)])

# ---------- 3) apimode：切换时同步 agent_runner ----------
patch(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_apimode\main.py", [(
    '''    cfg = json.loads(CONFIG.read_text(encoding="utf-8-sig"))
    providers = cfg.get("provider") or []
    local_ids = {"local-llama", "vl-ocr"}
    changed = []
    for p in providers:
        pid = p.get("id", "")
        if pid in local_ids:
            p["enable"] = mode == "local"
            changed.append(f"{pid}={p['enable']}")
        elif pid in ("deepseek", "deepseek-api"):
            p["enable"] = mode == "third_party"
            changed.append(f"{pid}={p['enable']}")
    CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    return " ".join(changed) or "没有找到可切换的 provider"''',
    '''    cfg = json.loads(CONFIG.read_text(encoding="utf-8-sig"))
    providers = cfg.get("provider") or []
    local_ids = {"local-llama", "vl-ocr"}
    changed = []
    for p in providers:
        pid = p.get("id", "")
        if pid in local_ids:
            p["enable"] = mode == "local"
            changed.append(f"{pid}={p['enable']}")
        elif pid in ("deepseek", "deepseek-api"):
            p["enable"] = mode == "third_party"
            changed.append(f"{pid}={p['enable']}")

    # 真正决定用哪个 provider 的地方是 agent_runner，必须一起改
    runner = cfg.setdefault("agent_runner", {})
    runner["runner_type"] = "local"
    model_cfg = runner.setdefault("config", {}).setdefault("model", {})
    if mode == "third_party":
        model_cfg["provider_id"] = "deepseek"
        model_cfg["fallback_provider_ids"] = ["local-llama"]
    else:
        model_cfg["provider_id"] = "local-llama"
        model_cfg["fallback_provider_ids"] = ["deepseek"]

    CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    return (
        " ".join(changed) + f" | 主模型={model_cfg['provider_id']}"
    ) or "没有找到可切换的 provider"''',
)])

# ---------- 4) ltm：同上 ----------
patch(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_ltm\main.py", [(
    '''        state = _Path(r"D:\\QQNTBOT\\data\\api_mode.json")
        if not state.exists():
            return False
        try:
            return json.loads(state.read_text(encoding="utf-8")).get("mode") == "third_party"
        except Exception:  # noqa: BLE001
            return False''',
    '''        try:
            cfg = json.loads(
                _Path(r"D:\\QQNTBOT\\apps\\AstrBot\\data\\cmd_config.json").read_text(
                    encoding="utf-8-sig"
                )
            )
            pid = str(
                cfg.get("agent_runner", {})
                .get("config", {})
                .get("model", {})
                .get("provider_id", "")
            )
            if pid:
                return "deepseek" in pid
        except Exception:  # noqa: BLE001
            pass
        state = _Path(r"D:\\QQNTBOT\\data\\api_mode.json")
        if not state.exists():
            return False
        try:
            return json.loads(state.read_text(encoding="utf-8")).get("mode") == "third_party"
        except Exception:  # noqa: BLE001
            return False''',
)])

print("done")
