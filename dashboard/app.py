"""QQ bot dashboard: status, system load, logs, memories, chats, access, tuning.

Reads existing SQLite databases read-only and tails existing log files.
State changes only happen through the start/stop/restart scripts, or by
writing the JSON config files that the plugins read.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import socket
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
import psutil
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

def _detect_root() -> Path:
    """Find the project root that owns data/ and apps/.

    Order: QQNTBOT_ROOT env var > directory layout > legacy hardcoded path.
    In a GitHub checkout this file sits in <root>/dashboard, so the parent is
    the root; on the original install it resolves to D:\\QQNTBOT as before.
    """
    env = os.environ.get("QQNTBOT_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    here = Path(__file__).resolve().parent
    if (here.parent / "data").is_dir() or (here.parent / "apps").is_dir():
        return here.parent
    legacy = Path(r"D:\QQNTBOT")
    return legacy if legacy.exists() else here.parent


ROOT = _detect_root()
MEM_DB = ROOT / "data" / "memory.db"
BOT_DB = ROOT / "apps" / "AstrBot" / "data" / "data_v4.db"
CFG = ROOT / "apps" / "AstrBot" / "data" / "cmd_config.json"
NAPCAT_LOG_DIR = ROOT / "apps" / "NapCat" / "logs"
BOT_LOG_DIR = ROOT / "apps" / "AstrBot" / "data" / "logs"
PERSONA_FILE = ROOT / "data" / "persona.json"
JUDGE_FILE = ROOT / "data" / "judge.json"
JUDGE_API_FILE = ROOT / "data" / "judge_api.json"
API_MODE_FILE = ROOT / "data" / "api_mode.json"
WATER_FILE = ROOT / "data" / "water.json"
AFFECTION_EDIT_FILE = ROOT / "data" / "affection_edit.json"
AUTOREPLY_FILE = ROOT / "data" / "autoreply.json"
REPLY_FILE = ROOT / "data" / "reply.json"
LTM_FILE = ROOT / "data" / "ltm.json"
PLUGIN_DIR = ROOT / "apps" / "AstrBot" / "data" / "plugins"
CREATOR_DATA_FILE = PLUGIN_DIR / "astrbot_plugin_creator" / "creator_data.json"
JUDGE_URL = "http://127.0.0.1:8082/v1/chat/completions"

CAPTION_DB = ROOT / "data" / "caption_cache.db"
MEME_DIR = ROOT / "apps" / "AstrBot" / "data" / "plugin_data" / "meme_manager"
MODELS_INI = Path(os.environ.get("LLAMA_MODELS_INI", r"D:\LLM\scripts\models.ini"))
LLM_LOG = Path(os.environ.get("LLAMA_LOG_FILE", r"D:\LLM\logs\llama-router.log"))

PORTS = {
    "model": (8080, "本地模型"),
    "astrbot": (6185, "AstrBot"),
    "onebot": (6199, "OneBot WS"),
    "napcat": (6099, "NapCat"),
    "judge": (8082, "判官模型"),
    "vl": (8085, "本地读图"),
    "ocr": (8083, "OCR"),
    "embed": (8097, "向量"),
    "dash": (6190, "控制台"),
}

DEFAULT_JUDGE_PROMPT = (
    "你在一个 QQ 群里，是个老群友。下面是刚才的对话和一条新消息。\n"
    "判断你要不要接这句话。\n"
    "接的情况：有人 @ 你或点名；有人提了一个具体、能回答的问题；"
    "有人在倾诉、情绪不好、骂街吐槽（接一句安慰或共鸣）；"
    "话题正好是兽圈、猎奇、gore 设定、游戏这类你熟的；你能补一句有用的。\n"
    "不接的情况：普通寒暄、已经有人在回答、你看不懂、"
    "或者你接了也只能说不知道。\n"
    "最近聊天：\n{recent}\n\n"
    "新消息：{message}\n\n"
    "只输出 1 或 0，不要解释。"
)

app = FastAPI(title="QQNT Bot Dashboard")


@app.middleware("http")
async def no_cache_headers(request: Request, call_next):
    """Never let the browser cache API responses (stale lists confused users)."""
    response = await call_next(request)
    path = request.url.path
    if path.startswith("/api/") or path in ("/", "/index.html"):
        response.headers["Cache-Control"] = "no-store, max-age=0"
        response.headers["Pragma"] = "no-cache"
    return response


MODE_FILE = ROOT / "data" / "api_mode.json"


def api_mode() -> str:
    """Return the mode implied by the provider actually serving chat.

    The WebUI switches providers via agent_runner, so that is the source of
    truth; the json file is only a hint from the /切换 command.

    Returns:
        ``third_party`` when DeepSeek is the chat provider, else ``local``.
    """
    try:
        cfg = read_json(CFG, {})
        model = (cfg.get("agent_runner", {}).get("config", {}).get("model", {}))
        provider_id = str(model.get("provider_id", ""))
        if provider_id:
            return "third_party" if "deepseek" in provider_id else "local"
    except (json.JSONDecodeError, OSError):
        pass
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


def port_open(port: int) -> bool:
    """Return True when something is listening on the local port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.4)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def read_memories(limit: int = 30) -> list[dict]:
    """Return the most recent long-term memories."""
    if not MEM_DB.exists():
        return []
    con = sqlite3.connect(f"file:{MEM_DB}?mode=ro", uri=True, timeout=5)
    try:
        rows = con.execute(
            "SELECT id, uid, text, created FROM facts ORDER BY created DESC LIMIT ?", (limit,)
        ).fetchall()
    except sqlite3.Error:
        return []
    finally:
        con.close()
    return [
        {
            "id": r[0],
            "uid": r[1],
            "text": r[2],
            "at": datetime.fromtimestamp(r[3]).strftime("%m-%d %H:%M"),
        }
        for r in rows
    ]


def memory_total() -> int:
    """Count stored memories."""
    if not MEM_DB.exists():
        return 0
    con = sqlite3.connect(f"file:{MEM_DB}?mode=ro", uri=True, timeout=5)
    try:
        return con.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
    except sqlite3.Error:
        return 0
    finally:
        con.close()


def recent_chats(limit: int = 5) -> list[dict]:
    """Return the latest conversations with their last exchange."""
    if not BOT_DB.exists():
        return []
    con = sqlite3.connect(f"file:{BOT_DB}?mode=ro", uri=True, timeout=5)
    try:
        rows = con.execute(
            "SELECT updated_at, user_id, content FROM conversations "
            "ORDER BY updated_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    except sqlite3.Error:
        return []
    finally:
        con.close()

    out = []
    for ts, umo, content in rows:
        try:
            msgs = json.loads(content)
        except json.JSONDecodeError:
            continue
        user = ""
        bot = ""
        for msg in reversed(msgs):
            text = msg.get("content")
            if isinstance(text, list):
                text = " ".join(str(c.get("text", c)) for c in text)
            text = str(text or "").split("<system_reminder>")[0].strip()
            if msg.get("role") == "assistant" and not bot:
                bot = text
            elif msg.get("role") == "user" and not user:
                user = text
        scope = "群" if "GroupMessage" in str(umo) else "私聊"
        out.append(
            {"at": str(ts)[5:16], "scope": scope, "user": user[:80], "bot": bot[:160]}
        )
    return out


def recent_activity() -> dict:
    """Return minutes since the newest group message."""
    if not BOT_DB.exists():
        return {"idle_min": None}
    con = sqlite3.connect(f"file:{BOT_DB}?mode=ro", uri=True, timeout=5)
    try:
        row = con.execute("SELECT MAX(created_at) FROM platform_message_history").fetchone()
    except sqlite3.Error:
        return {"idle_min": None}
    finally:
        con.close()
    if not row or not row[0]:
        return {"idle_min": None}
    try:
        stamp = (
            datetime.fromisoformat(str(row[0])).replace(tzinfo=timezone.utc).timestamp()
        )
    except ValueError:
        return {"idle_min": None}
    return {"idle_min": int((time.time() - stamp) / 60)}


def read_access() -> dict:
    """Return the allowlist split into groups and private accounts."""
    cfg = read_json(CFG, {})
    entries = (cfg.get("platform_settings") or {}).get("id_whitelist", []) or []
    groups = [str(e) for e in entries if str(e).isdigit()]
    friends = [str(e).rsplit(":", 1)[-1] for e in entries if "FriendMessage" in str(e)]
    return {"groups": groups, "friends": friends, "admin": cfg.get("admins_id", [])}


def write_access(groups: list[str], friends: list[str]) -> list[str]:
    """Persist a new allowlist into the AstrBot config."""
    cfg = read_json(CFG, {})
    entries = [f"qq:FriendMessage:{u}" for u in friends] + groups
    cfg["platform_settings"]["id_whitelist"] = entries
    CFG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    return entries


def known_groups() -> list[dict]:
    """List group ids seen in history, with message counts and last activity."""
    if not BOT_DB.exists():
        return []
    con = sqlite3.connect(f"file:{BOT_DB}?mode=ro", uri=True, timeout=5)
    try:
        rows = con.execute(
            "SELECT user_id, COUNT(*), MAX(created_at) FROM platform_message_history "
            "WHERE user_id LIKE 'qq:GroupMessage:%' GROUP BY user_id"
        ).fetchall()
    except sqlite3.Error:
        return []
    finally:
        con.close()

    seen: dict[str, dict] = {}
    for umo, count, last in rows:
        # umo 可能是 qq:GroupMessage:123456 或 qq:GroupMessage:发送者_123456
        tail = str(umo).rsplit(":", 1)[-1]
        gid = tail.rsplit("_", 1)[-1]
        if not gid.isdigit():
            continue
        item = seen.setdefault(gid, {"id": gid, "count": 0, "last": ""})
        item["count"] += count
        if str(last) > item["last"]:
            item["last"] = str(last)[5:16]
    return sorted(seen.values(), key=lambda x: x["last"], reverse=True)


def proc_rows() -> list[dict]:
    """Return aggregated memory/uptime for the processes this stack owns."""
    buckets: dict[str, dict] = {}

    def add(label: str, rss: int, started: float) -> None:
        item = buckets.setdefault(
            label, {"label": label, "rss_mb": 0, "count": 0, "start": started}
        )
        item["rss_mb"] += round(rss / 1048576)
        item["count"] += 1
        item["start"] = min(item["start"], started)

    for proc in psutil.process_iter(["pid", "name", "memory_info", "cmdline", "create_time"]):
        try:
            name = proc.info["name"] or ""
            cmd = " ".join(proc.info["cmdline"] or "")
            rss = proc.info["memory_info"].rss
            started = proc.info["create_time"]

            if name.startswith("QQ"):
                add("QQ + NapCat", rss, started)
            elif name.startswith("llama-server"):
                if "8082" in cmd:
                    add("判官 (1.5B, CPU)", rss, started)
                elif "--models-preset" in cmd or "b12274" in cmd:
                    add("本地模型 (llama.cpp)", rss, started)
            elif name.startswith("python"):
                if "uvicorn" in cmd and "6190" in cmd:
                    add("控制台", rss, started)
                elif "QQNTBOT" in cmd or "main.py" in cmd:
                    add("AstrBot", rss, started)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    now = time.time()
    rows = []
    for item in buckets.values():
        rows.append(
            {
                "label": item["label"],
                "rss_mb": item["rss_mb"],
                "count": item["count"],
                "uptime_min": int((now - item["start"]) / 60),
            }
        )
    return sorted(rows, key=lambda x: x["rss_mb"], reverse=True)


def system_snapshot() -> dict:
    """Return CPU, memory and disk usage plus process rows."""
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("D:\\")
    return {
        "cpu": psutil.cpu_percent(interval=0.3),
        "mem_used_gb": round(mem.used / 1073741824, 1),
        "mem_total_gb": round(mem.total / 1073741824, 1),
        "mem_percent": mem.percent,
        "disk_free_gb": round(disk.free / 1073741824, 1),
        "disk_total_gb": round(disk.total / 1073741824, 1),
        "boot_min": int((time.time() - psutil.boot_time()) / 60),
        "procs": proc_rows(),
    }


def tail(path: Path, lines: int = 120) -> list[str]:
    """Return the last N lines of a text file, tolerating encoding issues."""
    if not path.exists():
        return [f"(没有这个文件: {path})"]
    try:
        data = path.read_bytes()[-200000:]
    except OSError as exc:
        return [f"(读不了: {exc})"]
    for enc in ("utf-8", "gb18030"):
        try:
            text = data.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = data.decode("utf-8", "replace")
    return text.splitlines()[-lines:]


def newest(directory: Path, pattern: str) -> Path | None:
    """Return the most recently modified file matching a glob."""
    if not directory.exists():
        return None
    files = sorted(directory.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def read_json(path: Path, default: dict) -> dict:
    """Read a JSON file, falling back to a default when missing or broken."""
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return default


def write_json(path: Path, data: dict) -> None:
    """Write JSON with UTF-8 and stable formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def restart_bot() -> None:
    """Restart AstrBot in the background (keeps QQ running)."""
    subprocess.Popen(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ROOT / "scripts" / "restart-astrbot.ps1"),
        ],
        creationflags=subprocess.CREATE_NO_WINDOW,
    )


def capability_report() -> dict:
    """Tell the UI which optional backends this install can actually serve.

    This repo ships code and config templates only - a fresh checkout has no
    SQLite databases, no model services and no patched binaries.  The dashboard
    uses this map to grey out panels whose API would otherwise fail or hang on
    "loading".  Absence is reported with a human-readable reason.
    """
    scripts_ok = all((ROOT / s).exists() for s in ("start-all.ps1", "stop-all.ps1"))
    logs_ok = any(p.exists() for p in (BOT_LOG_DIR, NAPCAT_LOG_DIR, LLM_LOG.parent))
    if api_mode() == "third_party":
        models_ok = True
    else:
        try:
            # Switching models writes into cmd_config.json, so the config must
            # exist even when models.ini is present.
            models_ok = CFG.exists() and bool(available_models() or current_model())
        except (OSError, ValueError, json.JSONDecodeError):
            models_ok = False

    caps = {
        "core": (True, ""),
        "config": (CFG.exists(), "缺少 apps/AstrBot/data/cmd_config.json"),
        "botdb": (BOT_DB.exists(), "缺少聊天数据库 data_v4.db"),
        "memdb": (MEM_DB.exists(), "缺少记忆数据库 memory.db"),
        "embedding": (port_open(8097), "向量服务 8097 未启动"),
        "judge": (port_open(8082), "判官服务 8082 未启动"),
        "vl": (port_open(8085), "本地读图服务 8085 未启动"),
        "models": (models_ok, "没有可用模型预设，也没有配置第三方模型"),
        "logs": (logs_ok, "找不到日志文件目录"),
        "scripts": (scripts_ok, "缺少 start-all.ps1 / stop-all.ps1"),
        "plugins": (PLUGIN_DIR.exists(), "缺少 plugins 目录"),
        "caption": (CAPTION_DB.exists(), "缺少图片缓存 caption_cache.db"),
    }
    return {
        name: {"available": ok, "reason": "" if ok else reason}
        for name, (ok, reason) in caps.items()
    }


@app.get("/api/capabilities")
def capabilities() -> JSONResponse:
    """Return which optional panels this deployment can actually use."""
    return JSONResponse(capability_report())
LTM_DEFAULTS = {
    "enabled": True,
    "scan_interval": 90,
    "scan_budget": 4,
    "user_cooldown": 300,
    "extract_cooldown": 45,
    "max_tokens": 500,
    "third_party_scan": True,
}


def read_ltm_settings() -> dict:
    """Return the memory-extraction rhythm with defaults filled in.

    Returns:
        Dict with enabled / scan_interval / scan_budget / user_cooldown /
        extract_cooldown / max_tokens / third_party_scan.
    """
    data = read_json(LTM_FILE, {})
    out = dict(LTM_DEFAULTS)
    for key, default in LTM_DEFAULTS.items():
        value = data.get(key, default)
        if isinstance(default, bool):
            out[key] = bool(value)
        else:
            try:
                out[key] = int(value)
            except (TypeError, ValueError):
                out[key] = default
    return out


@app.get("/api/ltm/settings")
def get_ltm_settings() -> JSONResponse:
    """Return how often group history is mined for memories."""
    return JSONResponse(read_ltm_settings())


@app.post("/api/ltm/settings")
async def save_ltm_settings(request: Request) -> JSONResponse:
    """Save the extraction rhythm. The plugin re-reads ltm.json by mtime."""
    body = await request.json()
    current = read_json(LTM_FILE, {})
    limits = {
        "scan_interval": (30, 3600),
        "scan_budget": (1, 20),
        "user_cooldown": (0, 86400),
        "extract_cooldown": (0, 3600),
        "max_tokens": (100, 2000),
    }
    for key, (low, high) in limits.items():
        if key not in body:
            continue
        try:
            value = int(body[key])
        except (TypeError, ValueError):
            return JSONResponse({"ok": False, "msg": f"{key} 不是数字"})
        current[key] = max(low, min(high, value))
    for key in ("enabled", "third_party_scan"):
        if key in body:
            current[key] = bool(body[key])
    write_json(LTM_FILE, current)
    return JSONResponse({"ok": True, "msg": "已保存，下一轮扫描生效（无需重启）"})


@app.get("/api/status")
def status() -> JSONResponse:
    """Return component health plus the mode snapshot."""
    comps = [
        {"key": key, "label": label, "port": port, "up": port_open(port)}
        for key, (port, label) in PORTS.items()
    ]
    mode = api_mode()
    model_name = ""
    judge_model = ""
    try:
        cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))
        model_name = str(active_provider(cfg).get("model") or "")
        for provider in cfg.get("provider", []):
            if provider.get("id") == "local-llama":
                judge_model = str(provider.get("model") or "")
                break
    except (json.JSONDecodeError, OSError):
        pass
    return JSONResponse(
        {
            "components": comps,
            "memories": memory_total(),
            "activity": recent_activity(),
            "mode": mode,
            "model": model_name,
            "judge_model": judge_model,
            "vision": read_vision_state().get("mode"),
            "ltm": read_ltm_settings(),
            "reply": {
                "history_minutes": float(read_json(REPLY_FILE, {}).get("history_minutes", 20)),
                "history_min_count": int(
                    read_json(REPLY_FILE, {}).get("history_min_count", 3)
                ),
                "history_fallback_count": int(
                    read_json(REPLY_FILE, {}).get("history_fallback_count", 12)
                ),
            },
        }
    )


@app.get("/api/system")
def system() -> JSONResponse:
    """Return system load and per-process usage."""
    return JSONResponse(system_snapshot())


@app.get("/api/logs")
def logs(src: str = "astrbot", lines: int = 120) -> JSONResponse:
    """Return the tail of one log source."""
    if src == "napcat":
        path = newest(NAPCAT_LOG_DIR, "*.log")
        data = tail(path, lines) if path else ["(还没有 NapCat 日志)"]
    elif src == "router":
        data = tail(LLM_LOG, lines)
    elif src == "astrbot":
        data = tail(BOT_LOG_DIR / "astrbot.log", lines)
    else:
        data = ["(未知日志源)"]
    return JSONResponse({"source": src, "lines": data})


@app.get("/api/access")
def access() -> JSONResponse:
    """Return current access control plus known groups."""
    data = read_access()
    data["known"] = known_groups()
    return JSONResponse(data)


@app.post("/api/access")
async def save_access(request: Request) -> JSONResponse:
    """Save the allowlist and restart AstrBot so it takes effect."""
    body = await request.json()
    groups = [str(g).strip() for g in body.get("groups", []) if str(g).strip().isdigit()]
    friends = [str(f).strip() for f in body.get("friends", []) if str(f).strip().isdigit()]
    entries = write_access(groups, friends)
    restart_bot()
    return JSONResponse(
        {"ok": True, "entries": entries, "msg": "已保存，AstrBot 正在重启（约 15 秒）"}
    )


@app.get("/api/ltm/recent")
def ltm_recent(limit: int = 40) -> JSONResponse:
    """Return recent group messages that could be turned into memories."""
    limit = max(1, min(200, limit))
    if not BOT_DB.exists():
        return JSONResponse({"items": []})
    con = sqlite3.connect(f"file:{BOT_DB}?mode=ro", uri=True, timeout=5)
    try:
        rows = con.execute(
            "SELECT id, created_at, sender_id, sender_name, content "
            "FROM platform_message_history ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    except sqlite3.Error:
        return JSONResponse({"items": []})
    finally:
        con.close()

    items = []
    for mid, created, umo, name, content in rows:
        try:
            data = json.loads(content)
            text = " ".join(
                str(part.get("text", ""))
                for part in data.get("message", [])
                if part.get("type") == "plain"
            ).strip()
        except (ValueError, AttributeError):
            continue
        if not text or len(text) < 2 or text.strip("[]") in ("Image", "图片"):
            continue
        uid = str(umo) or "unknown"
        if uid == "1474388967":  # 机器人自己说的话不进记忆
            continue
        items.append(
            {
                "id": mid,
                "uid": uid,
                "name": str(name or "")[:16],
                "text": text[:200],
                "at": str(created or "")[:16],
            }
        )
    return JSONResponse({"items": items})


@app.post("/api/ltm/add")
async def ltm_add(request: Request) -> JSONResponse:
    """Append selected messages to the memory store (with embedding + dedupe)."""
    body = await request.json()
    items = [i for i in body.get("items", []) if isinstance(i, dict)]
    items = [i for i in items if str(i.get("text", "")).strip()][:30]
    if not items:
        return JSONResponse({"ok": False, "msg": "没有选中任何消息"})

    texts = [str(i["text"]).strip()[:120] for i in items]
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "http://127.0.0.1:8097/v1/embeddings",
                json={"model": "bge-small-zh-v1.5", "input": texts},
            )
            resp.raise_for_status()
            vectors = [d["embedding"] for d in resp.json()["data"]]
    except Exception as exc:  # noqa: BLE001
        return JSONResponse({"ok": False, "msg": f"向量服务不可用：{exc}"})

    con = sqlite3.connect(MEM_DB, timeout=10)
    added = skipped = 0
    try:
        existing = {}
        for uid in {str(i.get("uid", "")) for i in items}:
            rows = con.execute(
                "SELECT uid, emb FROM facts WHERE uid = ? ORDER BY created DESC LIMIT 300",
                (uid,),
            ).fetchall()
            existing[uid] = [json.loads(e) for _u, e in rows if e]
        now = datetime.now().timestamp()
        for item, text, vec in zip(items, texts, vectors, strict=False):
            uid = str(item.get("uid", "")) or "unknown"
            dup = False
            for other in existing.get(uid, []):
                dot = sum(a * b for a, b in zip(vec, other))
                na = sum(a * a for a in vec) ** 0.5
                nb = sum(b * b for b in other) ** 0.5
                if na and nb and dot / (na * nb) >= 0.92:
                    dup = True
                    break
            if dup:
                skipped += 1
                continue
            con.execute(
                "INSERT INTO facts (uid, text, emb, created) VALUES (?, ?, ?, ?)",
                (uid, text, json.dumps(vec), now),
            )
            existing.setdefault(uid, []).append(vec)
            added += 1
        con.commit()
    finally:
        con.close()
    return JSONResponse(
        {"ok": True, "msg": f"已加入 {added} 条，跳过重复 {skipped} 条", "added": added}
    )


@app.get("/api/memories")
def memories() -> JSONResponse:
    """Return recent memories."""
    return JSONResponse({"items": read_memories()})


@app.post("/api/memories/delete")
async def delete_memories(request: Request) -> JSONResponse:
    """Delete memories by id, or every memory of one user.

    Body: {"ids": [1,2]} or {"uid": "1154487120"}.
    """
    body = await request.json()
    ids = [int(i) for i in body.get("ids", []) if str(i).isdigit()]
    uid = str(body.get("uid", "")).strip()
    delete_all = bool(body.get("all"))
    if not ids and not uid and not delete_all:
        return JSONResponse({"ok": False, "msg": "没有指定要删的内容"})
    con = sqlite3.connect(MEM_DB, timeout=10)
    try:
        if delete_all:
            cur = con.execute("DELETE FROM facts")
        elif ids:
            marks = ",".join("?" for _ in ids)
            cur = con.execute(f"DELETE FROM facts WHERE id IN ({marks})", ids)
        else:
            cur = con.execute("DELETE FROM facts WHERE uid = ?", (uid,))
        con.commit()
        deleted = cur.rowcount
    except sqlite3.Error as exc:
        return JSONResponse({"ok": False, "msg": f"删除失败：{exc}"})
    finally:
        con.close()
    return JSONResponse({"ok": True, "msg": f"已删除 {deleted} 条", "deleted": deleted})


@app.get("/api/thinking")
def get_thinking() -> JSONResponse:
    """Return the thinking switch and token budget for the active provider."""
    cfg = read_json(CFG, {})
    body = active_provider(cfg).get("custom_extra_body", {})
    if api_mode() == "third_party":
        thinking = body.get("thinking") or {}
        enable = str(thinking.get("type", "disabled")) == "enabled"
        effort = str(body.get("reasoning_effort", "high"))
        budget_map = {"low": 600, "high": 1200, "max": 2000}
        budget = (
            budget_map.get(effort, int(body.get("max_tokens", 800)))
            if enable
            else int(body.get("max_tokens", 400))
        )
        return JSONResponse(
            {
                "enable": enable,
                "budget": budget,
                "mode": "third_party",
                "effort": effort if enable else "",
            }
        )
    kwargs = body.get("chat_template_kwargs", {}) or {}
    return JSONResponse(
        {
            "enable": bool(kwargs.get("enable_thinking", False)),
            "budget": int(body.get("max_tokens", 80)),
            "mode": "local",
        }
    )


@app.post("/api/thinking")
async def save_thinking(request: Request) -> JSONResponse:
    """Toggle the model thinking chain and set its token budget (restarts AstrBot)."""
    body = await request.json()
    enable = bool(body.get("enable"))
    try:
        budget = int(body.get("budget", 800))
    except (TypeError, ValueError):
        return JSONResponse({"ok": False, "msg": "预算格式不对"})
    budget = max(200, min(4000, budget))

    cfg = read_json(CFG, {})
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
        extra["max_tokens"] = budget if enable else min(budget, 120)
    CFG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    restart_bot()
    state = "开启" if enable else "关闭"
    return JSONResponse(
        {"ok": True, "msg": f"{state}思考链，预算 {budget} tokens，AstrBot 重启中"}
    )


@app.get("/api/reply")
def get_reply() -> JSONResponse:
    """Return meme chance and text replacement rules."""
    data = read_json(REPLY_FILE, {"meme_chance": 0.3, "text_rules": []})
    return JSONResponse(
        {
            "meme_chance": float(data.get("meme_chance", 0.3)),
            "reply_chance": float(data.get("reply_chance", 1.0)),
            "history_minutes": float(data.get("history_minutes", 30)),
            "history_min_count": int(data.get("history_min_count", 3)),
            "history_fallback_count": int(data.get("history_fallback_count", 12)),
            "reply_budget": int(data.get("reply_budget", 8)),
            "reply_budget_minutes": float(data.get("reply_budget_minutes", 10)),
            "summon": read_json(JUDGE_FILE, {}).get("summon", []),
            "dual_judge": bool(data.get("dual_judge", False)),
            "text_rules": data.get("text_rules", []),
        }
    )


@app.post("/api/reply")
async def save_reply(request: Request) -> JSONResponse:
    """Save meme chance and text rules. Picked up without a restart."""
    body = await request.json()
    try:
        chance = round(float(body.get("meme_chance", 0.3)), 2)
    except (TypeError, ValueError):
        return JSONResponse({"ok": False, "msg": "概率格式不对"})
    if not 0.0 <= chance <= 1.0:
        return JSONResponse({"ok": False, "msg": "概率要在 0~1 之间"})
    try:
        reply_chance = round(float(body.get("reply_chance", 1.0)), 2)
    except (TypeError, ValueError):
        reply_chance = 1.0
    reply_chance = max(0.0, min(1.0, reply_chance))
    rules = []
    for item in body.get("text_rules", []):
        find = str(item.get("find", ""))
        to = str(item.get("to", ""))
        if find:
            rules.append({"find": find, "to": to})
    # 合并保存：只覆盖这次真的传上来的字段，避免空值把旧配置冲掉
    current = read_json(REPLY_FILE, {})
    summon = [str(x).strip() for x in body.get("summon", []) if str(x).strip()]
    if summon:
        judge_cfg = read_json(JUDGE_FILE, {})
        judge_cfg["summon"] = summon
        write_json(JUDGE_FILE, judge_cfg)

    if "dual_judge" in body:
        current["dual_judge"] = bool(body["dual_judge"])
        cfg = read_json(CFG, {})
        current["dual_judge_model"] = cfg["provider"][0]["model"]
    current["meme_chance"] = chance
    current["reply_chance"] = reply_chance
    if "history_minutes" in body:
        current["history_minutes"] = max(1.0, min(240.0, float(body["history_minutes"])))
    if "history_min_count" in body:
        try:
            low = int(body["history_min_count"])
        except (TypeError, ValueError):
            return JSONResponse({"ok": False, "msg": "最少条数不是整数"})
        current["history_min_count"] = max(1, min(20, low))
    if "history_fallback_count" in body:
        try:
            fallback = int(body["history_fallback_count"])
        except (TypeError, ValueError):
            return JSONResponse({"ok": False, "msg": "兜底条数不是整数"})
        current["history_fallback_count"] = max(1, min(40, fallback))
    # 兜底条数不能比阈值还少，否则等于没补
    if current.get("history_fallback_count", 12) < current.get("history_min_count", 3):
        current["history_fallback_count"] = current["history_min_count"]
    if "reply_budget" in body:
        current["reply_budget"] = int(body["reply_budget"])
    if "reply_budget_minutes" in body:
        current["reply_budget_minutes"] = float(body["reply_budget_minutes"])
    # 正则规则：空列表视为"这次没传"，只有显式 clear_rules 才清空
    if rules or body.get("clear_rules"):
        current["text_rules"] = rules
    current.setdefault("history_minutes", 30)
    current.setdefault("history_min_count", 3)
    current.setdefault("history_fallback_count", 12)
    current.setdefault("reply_budget", 8)
    current.setdefault("reply_budget_minutes", 10)
    current.setdefault("text_rules", [{"pattern": "。(?=\\s|$)", "to": "~"}])
    write_json(REPLY_FILE, current)
    return JSONResponse(
        {
            "ok": True,
            "msg": (
                f"已保存：回复概率 {int(reply_chance * 100)}%、"
                f"表情概率 {int(chance * 100)}%、替换规则 {len(rules)} 条"
            ),
        }
    )


@app.get("/api/sampling")
def get_sampling() -> JSONResponse:
    """Return the sampling parameters used for chat."""
    cfg = read_json(CFG, {})
    body = active_provider(cfg).get("custom_extra_body", {})
    return JSONResponse(
        {
            "temperature": float(body.get("temperature", 0.7)),
            "top_p": float(body.get("top_p", 0.9)),
            "repeat_penalty": float(body.get("repeat_penalty", 1.0)),
            "max_tokens": int(body.get("max_tokens", 90)),
            "mode": api_mode(),
        }
    )


@app.post("/api/sampling")
async def save_sampling(request: Request) -> JSONResponse:
    """Save sampling parameters and restart AstrBot so they take effect."""
    body = await request.json()
    try:
        temperature = round(float(body.get("temperature", 0.7)), 2)
        top_p = round(float(body.get("top_p", 0.9)), 2)
        repeat_penalty = round(float(body.get("repeat_penalty", 1.0)), 3)
        max_tokens = int(body.get("max_tokens", 90))
    except (TypeError, ValueError):
        return JSONResponse({"ok": False, "msg": "参数格式不对"})

    if not 0.0 <= temperature <= 2.0:
        return JSONResponse({"ok": False, "msg": "温度要在 0~2 之间"})
    if not 1.0 <= repeat_penalty <= 2.0:
        return JSONResponse({"ok": False, "msg": "重复惩罚要在 1.0~2.0 之间"})

    cfg = read_json(CFG, {})
    extra = active_provider(cfg).setdefault("custom_extra_body", {})
    extra["temperature"] = temperature
    extra["top_p"] = top_p
    extra["max_tokens"] = max_tokens
    if api_mode() == "local":
        extra["repeat_penalty"] = repeat_penalty
    CFG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    restart_bot()
    return JSONResponse(
        {
            "ok": True,
            "msg": f"已保存：温度 {temperature}、重复惩罚 {repeat_penalty}，AstrBot 重启中",
        }
    )


@app.get("/api/contexts")
def contexts() -> JSONResponse:
    """List stored conversations so stale history can be reviewed and wiped."""
    if not BOT_DB.exists():
        return JSONResponse({"items": []})
    items = []
    con = sqlite3.connect(f"file:{BOT_DB}?mode=ro", uri=True, timeout=5)
    try:
        rows = con.execute(
            "SELECT user_id, conversation_id, updated_at, content "
            "FROM conversations ORDER BY updated_at DESC"
        ).fetchall()
        for umo, cid, updated, content in rows:
            try:
                count = len(json.loads(content)) if content else 0
            except ValueError:
                count = 0
            items.append(
                {
                    "umo": umo,
                    "cid": cid,
                    "messages": count,
                    "kb": round(len(content or "") / 1024, 1),
                    "updated": (updated or "")[:16],
                }
            )
    except sqlite3.Error:
        pass
    finally:
        con.close()
    return JSONResponse({"items": items})


@app.post("/api/contexts/clear")
async def clear_contexts(request: Request) -> JSONResponse:
    """Delete stored conversations and their current-conversation pointer."""
    body = await request.json()
    umo = str(body.get("umo", "")).strip()
    clear_all = bool(body.get("all"))
    if not umo and not clear_all:
        return JSONResponse({"ok": False, "msg": "没有指定要清空的会话"})
    con = sqlite3.connect(BOT_DB, timeout=10)
    try:
        if clear_all:
            con.execute("DELETE FROM conversations")
            con.execute("DELETE FROM preferences WHERE key = 'sel_conv_id'")
        else:
            con.execute("DELETE FROM conversations WHERE user_id = ?", (umo,))
            con.execute(
                "DELETE FROM preferences WHERE scope = 'umo' AND scope_id = ? "
                "AND key = 'sel_conv_id'",
                (umo,),
            )
        con.commit()
        return JSONResponse({"ok": True, "msg": "已清空，下一条消息会开新对话"})
    except sqlite3.Error as exc:
        return JSONResponse({"ok": False, "msg": f"清空失败：{exc}"})
    finally:
        con.close()


@app.get("/api/chats")
def chats() -> JSONResponse:
    """Return recent conversations."""
    return JSONResponse({"items": recent_chats()})


@app.get("/api/autoreply")
def get_autoreply() -> JSONResponse:
    """Return per-group auto-reply switches merged with known groups."""
    data = read_json(AUTOREPLY_FILE, {"groups": {}})
    saved = data.get("groups") or {}
    rows = []
    seen = set()
    for gid in read_access()["groups"]:
        conf = saved.get(gid, {}) if isinstance(saved.get(gid), dict) else {}
        rows.append(
            {
                "id": gid,
                "enabled": bool(conf.get("enabled", True)),
                "count": 0,
                "last": "",
                "whitelisted": True,
            }
        )
        seen.add(gid)
    for item in known_groups():
        if item["id"] in seen:
            for row in rows:
                if row["id"] == item["id"]:
                    row["count"] = item["count"]
                    row["last"] = item["last"]
            continue
        rows.append(
            {
                "id": item["id"],
                "enabled": False,
                "count": item["count"],
                "last": item["last"],
                "whitelisted": False,
            }
        )
    return JSONResponse({"items": rows})


@app.post("/api/autoreply")
async def save_autoreply(request: Request) -> JSONResponse:
    """Save per-group auto-reply switches. Read per request, no restart."""
    body = await request.json()
    groups = {}
    for item in body.get("items", []):
        gid = str(item.get("id", "")).strip()
        if not gid.isdigit():
            continue
        groups[gid] = {"enabled": bool(item.get("enabled"))}
    write_json(AUTOREPLY_FILE, {"groups": groups})
    return JSONResponse({"ok": True, "msg": "已保存，下一条群消息就生效（无需重启）"})



GUARD_FILE = ROOT / "data" / "api_mode.json"


def read_guard() -> dict:
    """Return guard settings with defaults filled in.

    Returns:
        Dict with mode, review_groups, daily_limit, used, save_token, history_keep.
    """
    try:
        state = json.loads(GUARD_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        state = {}
    state.setdefault("review_groups", {})
    state.setdefault("daily_limit", 200000)
    state.setdefault("group_limits", {})
    state.setdefault("used", {"date": "", "tokens": 0, "groups": {}})
    state.setdefault("save_token", True)
    state.setdefault("history_keep", 10)
    state["mode"] = api_mode()
    return state


VISION_STATE = ROOT / "data" / "vision_mode.json"
VL_PORT = 8085


def read_vision_state() -> dict:
    """Return the vision mode settings.

    Returns:
        Dict with mode, port and model.
    """
    try:
        data = json.loads(VISION_STATE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        data = {}
    data.setdefault("mode", "local")
    data.setdefault("port", VL_PORT)
    data.setdefault("model", "Qwen3VL-4B-Instruct")
    return data


@app.get("/api/visionmode")
def get_visionmode() -> JSONResponse:
    """Return the vision backend choice and whether the local VL is running."""
    state = read_vision_state()
    return JSONResponse(
        {
            "mode": state["mode"],
            "port": state["port"],
            "model": state["model"],
            "up": port_open(int(state["port"])),
            "api_mode": api_mode(),
        }
    )


@app.post("/api/visionmode")
async def save_visionmode(request: Request) -> JSONResponse:
    """Switch the vision backend: local, third_party or off."""
    body = await request.json()
    mode = str(body.get("mode", "")).strip()
    if mode not in ("local", "third_party", "off"):
        return JSONResponse({"ok": False, "msg": "模式只能是 local / third_party / off"})
    state = read_vision_state()
    state["mode"] = mode
    VISION_STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    names = {"local": "本地 VL", "third_party": "第三方看图", "off": "不读图"}
    return JSONResponse({"ok": True, "msg": f"已切换：{names[mode]}（立即生效）"})


@app.post("/api/vl/{action}")
async def vl_control(action: str) -> JSONResponse:
    """Start or stop the local VL server."""
    if action not in ("start", "stop"):
        return JSONResponse({"ok": False, "msg": "只支持 start / stop"})
    if action == "start":
        if port_open(VL_PORT):
            return JSONResponse({"ok": True, "msg": "本地 VL 已在运行"})
        subprocess.Popen(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
             "-File", str(ROOT / "scripts" / "start-vl.ps1")],
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        )
        return JSONResponse({"ok": True, "msg": "本地 VL 启动中，约 20 秒后可用"})
    for pid in _pids_on_port(VL_PORT):
        try:
            import psutil

            psutil.Process(pid).terminate()
        except Exception:  # noqa: BLE001
            continue
    return JSONResponse({"ok": True, "msg": "本地 VL 已停止"})


def _pids_on_port(port: int) -> list[int]:
    """Return PIDs listening on a port (empty when psutil is unavailable).

    Args:
        port: TCP port.

    Returns:
        List of process ids.
    """
    try:
        import psutil
    except ImportError:
        return []
    pids: list[int] = []
    for conn in psutil.net_connections(kind="inet"):
        if conn.laddr and conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
            if conn.pid and conn.pid not in pids:
                pids.append(conn.pid)
    return pids


PROFILE_DEFAULT_RULE = {"pattern": "。(?=\\s|$|[（(\\[【「『])", "to": "~"}
LTM_PROMPT = ROOT / "data" / "ltm_prompt.txt"


@app.get("/api/profile")
def get_profile() -> JSONResponse:
    """Return which local-only optimizations are active."""
    cfg = json.loads(REPLY_FILE.read_text(encoding="utf-8"))
    rules = cfg.get("text_rules") or []
    return JSONResponse(
        {
            "mode": api_mode(),
            "meme_on": float(cfg.get("meme_chance", 0)) > 0,
            "rules_on": bool(rules),
            "meme_chance": float(cfg.get("meme_chance", 0)),
            "rule_count": len(rules),
            "reply_chance": float(cfg.get("reply_chance", 0.3)),
        }
    )


@app.post("/api/profile")
async def save_profile(request: Request) -> JSONResponse:
    """Apply a local/third-party preset or toggle individual optimizations."""
    body = await request.json()
    cfg = json.loads(REPLY_FILE.read_text(encoding="utf-8"))
    preset = str(body.get("preset", "")).strip()

    if preset == "local":
        cfg["meme_chance"] = float(body.get("meme_chance", 0.3) or 0.3)
        if not (cfg.get("text_rules") or []):
            cfg["text_rules"] = [dict(PROFILE_DEFAULT_RULE)]
        msg = "已套用本地优化：表情附带 + 文本替换"
    elif preset == "third":
        cfg["meme_chance"] = 0
        cfg["text_rules"] = []
        msg = "已套用第三方精简：关闭表情附带与文本替换"
    else:
        if "meme_on" in body:
            cfg["meme_chance"] = 0.3 if body["meme_on"] else 0
        if "rules_on" in body:
            cfg["text_rules"] = [dict(PROFILE_DEFAULT_RULE)] if body["rules_on"] else []
        msg = "已更新本地优化开关"

    REPLY_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    return JSONResponse({"ok": True, "msg": msg})


@app.get("/api/ltm/prompt")
def get_ltm_prompt() -> JSONResponse:
    """Return the memory extraction prompt."""
    try:
        text = LTM_PROMPT.read_text(encoding="utf-8")
    except OSError:
        text = ""
    return JSONResponse({"text": text, "has_placeholders": "{user}" in text and "{bot}" in text})


@app.post("/api/ltm/prompt")
async def save_ltm_prompt(request: Request) -> JSONResponse:
    """Save the memory extraction prompt (requires {user} and {bot})."""
    body = await request.json()
    text = str(body.get("text", ""))
    if "{user}" not in text or "{bot}" not in text:
        return JSONResponse({"ok": False, "msg": "必须同时包含 {user} 和 {bot} 占位符"})
    LTM_PROMPT.write_text(text, encoding="utf-8")
    return JSONResponse({"ok": True, "msg": "已保存，下一轮提取生效"})


@app.get("/api/guard")
def get_guard() -> JSONResponse:
    """Return review switches, quota, save-token flag and history window."""
    state = read_guard()
    cfg = read_json(CFG, {})
    whitelist = (
        cfg.get("platform_settings", {}).get("id_whitelist", []) or []
    )
    groups = [x for x in whitelist if str(x).isdigit()]
    return JSONResponse(
        {
            "mode": state["mode"],
            "groups": groups,
            "review_groups": state.get("review_groups", {}),
            "daily_limit": state.get("daily_limit", 0),
            "group_limits": state.get("group_limits", {}),
            "used": state.get("used", {}),
            "save_token": bool(state.get("save_token", True)),
            "history_keep": int(state.get("history_keep", 10)),
        }
    )


@app.post("/api/guard")
async def save_guard(request: Request) -> JSONResponse:
    """Save review switches, quota and save-token settings (no restart needed)."""
    body = await request.json()
    state = read_guard()
    state.pop("mode", None)

    if "review_groups" in body and isinstance(body["review_groups"], dict):
        state["review_groups"] = {
            str(k): bool(v) for k, v in body["review_groups"].items()
        }
    if "daily_limit" in body:
        try:
            state["daily_limit"] = max(0, int(body["daily_limit"]))
        except (TypeError, ValueError):
            return JSONResponse({"ok": False, "msg": "额度必须是数字"})
    if "group_limits" in body and isinstance(body["group_limits"], dict):
        # gid -> 额度（0 或缺失 = 跟随全局）；合并写入，不覆盖未提及的群
        gl = dict(state.get("group_limits") or {})
        for k, v in body["group_limits"].items():
            try:
                gl[str(k)] = max(0, int(v))
            except (TypeError, ValueError):
                return JSONResponse({"ok": False, "msg": f"群 {k} 额度必须是数字"})
        state["group_limits"] = gl
    if "save_token" in body:
        state["save_token"] = bool(body["save_token"])
    if "history_keep" in body:
        try:
            state["history_keep"] = max(2, min(40, int(body["history_keep"])))
        except (TypeError, ValueError):
            return JSONResponse({"ok": False, "msg": "历史条数不对"})

    GUARD_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    return JSONResponse({"ok": True, "msg": "已保存（立即生效）"})


# ---- 全账户 token 用量 ----
# 四路各自记账（互不干扰），这里做汇总视图。
# main  → data/api_mode.json  used.tokens + daily_limit
# judge → data/judge_api.json used.tokens + daily_limit
# vision→ data/vision_usage.json（vision 插件写）
# ltm   → data/ltm_usage.json（ltm 插件写）
VISION_USAGE = ROOT / "data" / "vision_usage.json"
LTM_USAGE = ROOT / "data" / "ltm_usage.json"
AUX_DEFAULT = lambda: {"date": "", "tokens": 0, "daily_limit": 100000, "enabled": True}


def _aux_usage(path: Path) -> dict:
    d = read_json(path, AUX_DEFAULT())
    for k, v in AUX_DEFAULT().items():
        d.setdefault(k, v)
    if d.get("date") != datetime.now().strftime("%Y%m%d"):
        d["date"] = datetime.now().strftime("%Y%m%d")
        d["tokens"] = 0
    return d


@app.get("/api/token_usage")
def get_token_usage() -> JSONResponse:
    """Aggregate all four token ledgers into one view (today only)."""
    today = datetime.now().strftime("%Y%m%d")
    main = read_guard()
    main_used = main.get("used") or {}
    judge = read_json(JUDGE_API_FILE, {})
    judge_used = judge.get("used") or {}
    vision = _aux_usage(VISION_USAGE)
    ltm = _aux_usage(LTM_USAGE)

    parts = {
        "main": {
            "tokens": int(main_used.get("tokens") or 0) if main_used.get("date") == today else 0,
            "limit": int(main.get("daily_limit") or 0),
            "enabled": True,
        },
        "judge": {
            "tokens": int(judge_used.get("tokens") or 0) if judge_used.get("date") == today else 0,
            "limit": int(judge.get("daily_limit") or 0),
            "enabled": bool(judge.get("enable", True)),
        },
        "vision": {
            "tokens": int(vision.get("tokens") or 0),
            "limit": int(vision.get("daily_limit") or 0),
            "enabled": bool(vision.get("enabled", True)),
        },
        "ltm": {
            "tokens": int(ltm.get("tokens") or 0),
            "limit": int(ltm.get("daily_limit") or 0),
            "enabled": bool(ltm.get("enabled", True)),
        },
    }
    return JSONResponse({
        "date": today,
        "parts": parts,
        "total": sum(p["tokens"] for p in parts.values()),
        "total_limit": sum(p["limit"] for p in parts.values()),
    })


@app.post("/api/token_usage")
async def save_token_usage(request: Request) -> JSONResponse:
    """Update the daily limits / switches for the vision and ltm ledgers.

    main/judge limits are edited through /api/guard and /api/judge/api —
    this endpoint only owns the two auxiliary ledgers to avoid double writes.
    """
    body = await request.json()
    changed = []
    for name, path in (("vision", VISION_USAGE), ("ltm", LTM_USAGE)):
        if name not in body or not isinstance(body[name], dict):
            continue
        d = _aux_usage(path)
        cfg = body[name]
        if "daily_limit" in cfg:
            try:
                d["daily_limit"] = max(0, min(10_000_000, int(cfg["daily_limit"])))
            except (TypeError, ValueError):
                return JSONResponse({"ok": False, "msg": f"{name} 额度必须是数字"})
        if "enabled" in cfg:
            d["enabled"] = bool(cfg["enabled"])
        write_json(path, d)
        changed.append(name)
    return JSONResponse({"ok": True, "msg": f"已保存：{', '.join(changed) or '无变更'}（立即生效）"})


# ---------------------------------------------------------------- 统一分群额度 API
# 三类额度（聊天/判官/识图）各有「全局默认 + 每群上限(0=跟随全局) + 今日用量」。
# 主对话账本 api_mode.json，判官 judge_api.json，识图 vision_usage.json，
# 当前日期跨天归零由各写入方负责；这里只做读取汇总与配置写入。
QUOTA_CHANNELS = (
    ("chat", "聊天主对话"),
    ("judge", "判官"),
    ("vision", "识图补描述"),
)


def _quota_groups() -> list[str]:
    """群号列表：白名单群优先，再并入历史里见过的群。"""
    groups = [str(x) for x in read_access()["groups"]]
    seen = set(groups)
    for item in known_groups():
        gid = str(item.get("id") or "")
        if gid and gid not in seen:
            seen.add(gid)
            groups.append(gid)
    return groups


@app.get("/api/quota")
def get_quota() -> JSONResponse:
    """Aggregate per-group limits and today's usage for all three channels."""
    today = datetime.now().strftime("%Y%m%d")
    groups = _quota_groups()

    main = read_json(GUARD_FILE, {})
    judge = read_json(JUDGE_API_FILE, {})
    vision = _aux_usage(VISION_USAGE)

    main_used = main.get("used") or {}
    judge_used = judge.get("used") or {}
    main_date_ok = main_used.get("date") == today
    judge_date_ok = judge_used.get("date") == today

    # 各渠道：全局默认额度 / 全局已用 / 每群上限 / 每群已用
    chans = {
        "chat": {
            "global_limit": int(main.get("daily_limit") or 0),
            "global_used": int(main_used.get("tokens") or 0) if main_date_ok else 0,
            "group_limits": {str(k): int(v or 0) for k, v in (main.get("group_limits") or {}).items()},
            "group_used": {str(k): int(v or 0) for k, v in (main_used.get("groups") or {}).items()},
        },
        "judge": {
            "global_limit": int(judge.get("daily_limit") or 0),
            "global_used": int(judge_used.get("tokens") or 0) if judge_date_ok else 0,
            "group_limits": {str(k): int(v or 0) for k, v in (judge.get("group_limits") or {}).items()},
            "group_used": {str(k): int(v or 0) for k, v in (judge_used.get("groups") or {}).items()},
        },
        "vision": {
            "global_limit": int(vision.get("daily_limit") or 0),
            "global_used": int(vision.get("tokens") or 0),
            "group_limits": {str(k): int(v or 0) for k, v in (vision.get("group_limits") or {}).items()},
            "group_used": {str(k): int(v or 0) for k, v in (vision.get("groups") or {}).items()},
        },
    }
    return JSONResponse({
        "date": today,
        "groups": groups,
        "channels": chans,
        "channel_names": {k: v for k, v in QUOTA_CHANNELS},
        # 概览用：所有群/全账户合计（就是各渠道全局今日用量）
        "totals": {k: chans[k]["global_used"] for k, _ in QUOTA_CHANNELS},
        "total": sum(chans[k]["global_used"] for k, _ in QUOTA_CHANNELS),
    })


@app.post("/api/quota")
async def save_quota(request: Request) -> JSONResponse:
    """Merge-save global defaults and per-group limits for the three channels."""
    body = await request.json()
    changed = []

    def _int(v) -> int:
        return max(0, min(10_000_000, int(v)))

    # 聊天 → api_mode.json (GUARD_FILE)
    q = body.get("chat")
    if isinstance(q, dict):
        st = read_json(GUARD_FILE, {})
        if "global_limit" in q:
            st["daily_limit"] = _int(q["global_limit"])
        if isinstance(q.get("group_limits"), dict):
            gl = dict(st.get("group_limits") or {})
            for k, v in q["group_limits"].items():
                gl[str(k)] = _int(v)
            st["group_limits"] = gl
        write_json(GUARD_FILE, st)
        changed.append("chat")

    # 判官 → judge_api.json
    q = body.get("judge")
    if isinstance(q, dict):
        st = read_json(JUDGE_API_FILE, {})
        if "global_limit" in q:
            st["daily_limit"] = _int(q["global_limit"])
        if isinstance(q.get("group_limits"), dict):
            gl = dict(st.get("group_limits") or {})
            for k, v in q["group_limits"].items():
                gl[str(k)] = _int(v)
            st["group_limits"] = gl
        write_json(JUDGE_API_FILE, st)
        changed.append("judge")

    # 识图 → vision_usage.json
    q = body.get("vision")
    if isinstance(q, dict):
        st = _aux_usage(VISION_USAGE)
        if "global_limit" in q:
            st["daily_limit"] = _int(q["global_limit"])
        if isinstance(q.get("group_limits"), dict):
            gl = dict(st.get("group_limits") or {})
            for k, v in q["group_limits"].items():
                gl[str(k)] = _int(v)
            st["group_limits"] = gl
        write_json(VISION_USAGE, st)
        changed.append("vision")

    return JSONResponse({"ok": True, "msg": f"已保存：{', '.join(changed) or '无变更'}（立即生效）"})


# ---------------------------------------------------------------- 好感度面板 API
@app.get("/api/affection")
def get_affection() -> JSONResponse:
    """List active-chat candidates with their current affection (panel view)."""
    cfg = read_json(CFG, {})
    entries = (cfg.get("platform_settings") or {}).get("id_whitelist", []) or []
    friends = [str(e).rsplit(":", 1)[-1] for e in entries if "FriendMessage" in str(e)]
    creator = str((read_json(CFG, {}).get("admins_id") or ["1154487120"])[0])
    if creator and creator not in friends:
        friends.append(creator)
    creator_id = "1154487120"
    data = read_json(CREATOR_DATA_FILE, {})
    aff = data.get("affection") or {}
    edits = read_json(AFFECTION_EDIT_FILE, {})
    rows = []
    for uid in friends:
        is_creator = uid == creator_id
        base = 100.0 if is_creator else 50.0
        rec = aff.get(uid) or {}
        # 创造者恒 100（与插件 _affection() 口径一致），面板不可改
        score = 100.0 if is_creator else float(edits.get(uid, rec.get("score", base)))
        rows.append({
            "uid": uid,
            "score": round(score, 1),
            "msgs": int(rec.get("msgs") or 0),
            "last_seen": rec.get("last_seen") or 0,
            "is_creator": is_creator,
            "overridden": (not is_creator) and uid in edits,
        })
    rows.sort(key=lambda r: -r["score"])
    return JSONResponse({"items": rows, "creator_id": creator_id})


@app.post("/api/affection")
async def save_affection(request: Request) -> JSONResponse:
    """Save panel-authored affection overrides into affection_edit.json."""
    body = await request.json()
    scores = body.get("scores")
    if not isinstance(scores, dict):
        return JSONResponse({"ok": False, "msg": "scores 必须是对象"})
    edits = read_json(AFFECTION_EDIT_FILE, {})
    for uid, v in scores.items():
        if str(uid) == "1154487120":
            continue  # 创造者恒 100，不接受覆盖
        try:
            edits[str(uid)] = round(max(0.0, min(100.0, float(v))), 1)
        except (TypeError, ValueError):
            return JSONResponse({"ok": False, "msg": f"{uid} 好感度必须是数字"})
    write_json(AFFECTION_EDIT_FILE, edits)
    return JSONResponse({"ok": True, "msg": "好感度已保存（主动搭话概率立即生效）"})


@app.get("/api/water")
def get_water() -> JSONResponse:
    """Return per-group watering settings merged with known groups."""
    data = read_json(WATER_FILE, {"groups": {}})
    saved = data.get("groups") or {}
    rows = []
    seen = set()
    for gid in read_access()["groups"]:
        conf = saved.get(gid, {}) if isinstance(saved.get(gid), dict) else {}
        rows.append(
            {
                "id": gid,
                "enabled": bool(conf.get("enabled", True)),
                "idle_min": int(conf.get("idle_min", 90)),
                "count": 0,
                "last": "",
                "whitelisted": True,
            }
        )
        seen.add(gid)
    for item in known_groups():
        if item["id"] in seen:
            for row in rows:
                if row["id"] == item["id"]:
                    row["count"] = item["count"]
                    row["last"] = item["last"]
            continue
        rows.append(
            {
                "id": item["id"],
                "enabled": False,
                "idle_min": 90,
                "count": item["count"],
                "last": item["last"],
                "whitelisted": False,
            }
        )
    return JSONResponse({"items": rows})


@app.post("/api/water")
async def save_water(request: Request) -> JSONResponse:
    """Save per-group watering switches. Read per-request, so no restart."""
    body = await request.json()
    groups = {}
    for item in body.get("items", []):
        gid = str(item.get("id", "")).strip()
        if not gid.isdigit():
            continue
        try:
            idle_min = max(5, int(item.get("idle_min", 90)))
        except (TypeError, ValueError):
            idle_min = 90
        groups[gid] = {"enabled": bool(item.get("enabled")), "idle_min": idle_min}
    write_json(WATER_FILE, {"groups": groups})
    return JSONResponse({"ok": True, "msg": "已保存，下一次判定周期生效（约 1 分钟）"})


GROUP_FLAGS_FILE = (
    PLUGIN_DIR / "astrbot_plugin_access" / "group_flags.json"
)
# 两类主动分开：auto_chat=主动冒泡(无唤醒词选择性聊天,主特色,默认开)，
# warmup=热群(冷场发预设暖场话,默认关)。旧键 reply_at/proactive 做兼容映射。
GROUP_FLAG_DEFAULTS = {"auto_chat": True, "warmup": False, "welcome": False}
FLAG_NAMES = {
    "auto_chat": "主动冒泡（选择性聊天）",
    "warmup": "热群（冷场暖场话）",
    "welcome": "进群提醒",
}
FLAG_KEY_ALIAS = {"reply_at": "auto_chat", "proactive": "warmup"}


def _normalize_flag_entry(conf: dict) -> dict:
    entry = dict(GROUP_FLAG_DEFAULTS)
    if not isinstance(conf, dict):
        return entry
    for key in GROUP_FLAG_DEFAULTS:
        if key in conf:
            entry[key] = bool(conf[key])
    for old, new in FLAG_KEY_ALIAS.items():
        if new not in conf and old in conf:
            entry[new] = bool(conf[old])
    return entry


def _welcome_text() -> str:
    """Pull WELCOME_TEXT from the access plugin via ast (no code execution)."""
    path = PLUGIN_DIR / "astrbot_plugin_access" / "main.py"
    try:
        import ast
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "WELCOME_TEXT"
                for t in node.targets
            ):
                return ast.literal_eval(node.value)
    except Exception:  # noqa: BLE001 - 预览拿不到就空着
        pass
    return ""


@app.get("/api/group_flags")
def get_group_flags() -> JSONResponse:
    """Per-group auto_chat/warmup/welcome switches (defaults match access)."""
    saved = (read_json(GROUP_FLAGS_FILE, {"groups": {}}).get("groups")) or {}
    rows = []
    seen = set()
    for gid in read_access()["groups"]:
        row = {"id": gid, "whitelisted": True}
        row.update(_normalize_flag_entry(saved.get(gid)))
        rows.append(row)
        seen.add(gid)
    for item in known_groups():
        if item["id"] in seen:
            continue
        row = {"id": item["id"], "whitelisted": False}
        row.update(_normalize_flag_entry(saved.get(item["id"])))
        rows.append(row)
    return JSONResponse({"items": rows, "flag_names": FLAG_NAMES, "welcome_text": _welcome_text()})


@app.post("/api/group_flags")
async def save_group_flags(request: Request) -> JSONResponse:
    """Merge-write per-group switches. Plugin loaders cache by mtime, no restart."""
    body = await request.json()
    raw = read_json(GROUP_FLAGS_FILE, {"groups": {}})
    groups = raw.get("groups") or {}
    changed = 0
    for item in body.get("items", []):
        gid = str(item.get("id", "")).strip()
        if not gid.isdigit():
            continue
        entry = _normalize_flag_entry(groups.get(gid))
        for key in GROUP_FLAG_DEFAULTS:
            if key in item:
                entry[key] = bool(item[key])
        groups[gid] = entry
        changed += 1
    write_json(GROUP_FLAGS_FILE, {"groups": groups})
    return JSONResponse(
        {"ok": True, "msg": f"已保存 {changed} 个群，开关即时生效（无需重启）"}
    )


def available_models() -> list[str]:
    """Read preset names from the llama.cpp router config."""
    try:
        raw = MODELS_INI.read_bytes()
    except OSError:
        return []
    text = None
    for enc in ("utf-8", "gb18030"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        return []
    names = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("[") and line.endswith("]"):
            name = line[1:-1].strip()
            if not name or name == "*":
                continue
            # 这些预设不适合当聊天模型，别让人误选
            if any(bad in name for bad in ("PaddleOCR", "Translate")):
                continue
            names.append(name)
    return names


def current_model() -> str:
    """Return the model currently configured for chat."""
    cfg = read_json(CFG, {})
    try:
        return str(cfg["provider"][0].get("model", ""))
    except (KeyError, IndexError):
        return ""


API_MODELS = ["deepseek-flash", "deepseek-v4-pro"]


@app.get("/api/models")
def models() -> JSONResponse:
    """List switchable models and the active one for the current mode."""
    if api_mode() == "third_party":
        cfg = read_json(CFG, {})
        return JSONResponse(
            {
                "items": API_MODELS,
                "current": str(active_provider(cfg).get("model", "")),
                "mode": "third_party",
            }
        )
    return JSONResponse(
        {"items": available_models(), "current": current_model(), "mode": "local"}
    )


@app.post("/api/models")
async def switch_model(request: Request) -> JSONResponse:
    """Switch the chat model preset and restart AstrBot."""
    body = await request.json()
    name = str(body.get("model", "")).strip()
    third = api_mode() == "third_party"
    allowed = API_MODELS if third else available_models()
    if name not in allowed:
        return JSONResponse({"ok": False, "msg": f"没有这个预设：{name}"})
    cfg = read_json(CFG, {})
    active_provider(cfg)["model"] = name
    CFG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    restart_bot()
    return JSONResponse(
        {"ok": True, "msg": f"已切到 {name}，AstrBot 重启中（模型首次加载约 10 秒）"}
    )


@app.get("/api/vision")
def vision() -> JSONResponse:
    """Return image-caption cache stats and meme library totals."""
    entries = 0
    hits = 0
    recent: list[dict] = []
    if CAPTION_DB.exists():
        con = sqlite3.connect(f"file:{CAPTION_DB}?mode=ro", uri=True, timeout=5)
        try:
            row = con.execute(
                "SELECT COUNT(*), COALESCE(SUM(hits), 0) FROM captions"
            ).fetchone()
            entries, hits = int(row[0] or 0), int(row[1] or 0)
            for h, text, created in con.execute(
                "SELECT hash, text, created FROM captions "
                "ORDER BY created DESC LIMIT 6"
            ).fetchall():
                recent.append(
                    {
                        "hash": str(h)[:8],
                        "text": str(text)[:90],
                        "at": datetime.fromtimestamp(created).strftime("%m-%d %H:%M"),
                    }
                )
        except sqlite3.Error:
            pass
        finally:
            con.close()

    packs = 0
    images = 0
    if MEME_DIR.exists():
        packs_dir = MEME_DIR / "packs"
        if packs_dir.exists():
            packs = len([p for p in packs_dir.iterdir() if p.is_dir()])
            images = len(
                [
                    f
                    for f in packs_dir.rglob("*")
                    if f.suffix.lower() in {".jpg", ".jpeg", ".png", ".gif", ".webp"}
                ]
            )

    return JSONResponse(
        {
            "cache_entries": entries,
            "cache_hits": hits,
            "recent": recent,
            "meme_packs": packs,
            "meme_images": images,
        }
    )


@app.get("/api/persona")
def get_persona() -> JSONResponse:
    """Return the current persona text."""
    data = read_json(PERSONA_FILE, {"text": ""})
    return JSONResponse({"text": data.get("text", "")})


@app.post("/api/persona")
async def save_persona(request: Request) -> JSONResponse:
    """Save the persona and restart AstrBot so it takes effect."""
    body = await request.json()
    text = str(body.get("text", "")).strip()
    if len(text) < 20:
        return JSONResponse({"ok": False, "msg": "太短了，至少写 20 个字"})
    write_json(PERSONA_FILE, {"text": text})
    restart_bot()
    return JSONResponse(
        {"ok": True, "msg": f"已保存 {len(text)} 字，AstrBot 正在重启（约 15 秒）"}
    )


@app.get("/api/judge")
def get_judge() -> JSONResponse:
    """Return the judge prompt and keyword rules."""
    data = read_json(
        JUDGE_FILE, {"prompt": DEFAULT_JUDGE_PROMPT, "ignore": [], "force_reply": []}
    )
    data.setdefault("prompt", DEFAULT_JUDGE_PROMPT)
    data.setdefault("recent_max", 12)
    data.setdefault("ignore", [])
    data.setdefault("force_reply", [])
    return JSONResponse(data)


@app.post("/api/judge")
async def save_judge(request: Request) -> JSONResponse:
    """Save judge settings. Read per-request, so no restart is needed."""
    body = await request.json()
    prompt = str(body.get("prompt", "")).strip()
    if "{message}" not in prompt:
        return JSONResponse({"ok": False, "msg": "提示词里必须保留占位符 {message}"})
    # 合并写入：force_patterns / summon 等字段不能被面板保存冲掉
    data = read_json(JUDGE_FILE, {})
    data.update(
        {
            "prompt": prompt,
            "recent_max": min(30, max(1, int(body.get("recent_max") or 12))),
            "ignore": [str(x).strip() for x in body.get("ignore", []) if str(x).strip()],
            "force_reply": [
                str(x).strip() for x in body.get("force_reply", []) if str(x).strip()
            ],
        }
    )
    write_json(JUDGE_FILE, data)
    return JSONResponse({"ok": True, "msg": "已保存，下一条群消息就生效（无需重启）"})


def _judge_api_credentials(cfg: dict) -> tuple[str, str, str]:
    """Resolve third-party judge credentials, falling back to the DeepSeek provider."""
    base = str(cfg.get("api_base") or "https://api.deepseek.com/v1").rstrip("/")
    key = str(cfg.get("api_key") or "").strip()
    model = str(cfg.get("model") or "").strip()
    if base and key and model:
        return base, key, model
    provider_cfg = read_json(CFG, {})
    sources = {
        str(s.get("id")): s
        for s in provider_cfg.get("provider_sources", [])
        if isinstance(s, dict)
    }
    providers = {
        str(p.get("id")): p
        for p in provider_cfg.get("provider", [])
        if isinstance(p, dict)
    }
    provider = providers.get("deepseek") or {}
    source = sources.get(str(provider.get("provider_source_id") or "")) or sources.get(
        "deepseek_source"
    ) or {}
    if not key:
        keys = source.get("key") if isinstance(source.get("key"), list) else []
        key = str(source.get("api_key") or (keys[0] if keys else "")).strip()
    if not model:
        model = str(provider.get("model") or "deepseek-flash").strip()
    return base, key, model


@app.get("/api/judge/api")
def get_judge_api() -> JSONResponse:
    """Return the third-party judge profile with the key masked."""
    data = read_json(JUDGE_API_FILE, {})
    key = str(data.get("api_key") or "")
    data["api_key"] = ""
    data["api_key_set"] = bool(key)
    data.setdefault("used", {"date": "", "tokens": 0})
    data.setdefault("enable", True)
    data.setdefault("budget_gate", True)
    data.setdefault("use_reply_chance", False)
    data.setdefault("daily_limit", 50000)
    data.setdefault("judge_delay", 2.0)
    data.setdefault("reply_gap", 6)
    data.setdefault("inflight_ttl", 45)
    data.setdefault("inflight_lock", True)
    data.setdefault("dup_window", 45)
    data.setdefault("dup_ratio", 0.75)
    data.setdefault("burst_gap", 15)
    data.setdefault("burst_settle", 3.5)
    data.setdefault("burst_reuse", 45)
    data.setdefault("burst_enable", True)
    data.setdefault("summon_gap", 4)
    data.setdefault("break_follow", 30)
    data.setdefault("bot_names", [])
    data.setdefault("break_words", [])
    data.setdefault("followup_enable", True)
    data.setdefault("followup_gap", 120)
    data.setdefault("unknown_reply", "silent")
    return JSONResponse(data)


@app.post("/api/judge/api")
async def save_judge_api(request: Request) -> JSONResponse:
    """Merge-save the third-party judge profile (empty key keeps the old one)."""
    body = await request.json()
    data = read_json(JUDGE_API_FILE, {})
    for key in (
        "enable",
        "api_base",
        "model",
        "prompt",
        "recent_max",
        "recent_chars",
        "include_last_bot",
        "max_tokens",
        "temperature",
        "budget_gate",
        "use_reply_chance",
        "reply_chance",
        "fallback_chance",
        "cache_seconds",
        "judge_delay",
        "reply_gap",
        "inflight_ttl",
        "inflight_lock",
        "dup_window",
        "dup_ratio",
        "burst_gap",
        "burst_settle",
        "burst_reuse",
        "burst_enable",
        "summon_gap",
        "break_follow",
        "bot_names",
        "break_words",
        "daily_limit",
        "ignore",
        "force_reply",
        "force_patterns",
        "followup_patterns",
        "followup_enable",
        "followup_gap",
        "unknown_reply",
        "summon",
    ):
        if key in body:
            data[key] = body[key]
    if body.get("api_key"):
        data["api_key"] = str(body["api_key"]).strip()
    if body.get("clear_api_key"):
        data["api_key"] = ""
    prompt = str(data.get("prompt") or "")
    if "{message}" not in prompt:
        return JSONResponse({"ok": False, "msg": "提示词里必须保留占位符 {message}"})
    write_json(JUDGE_API_FILE, data)
    return JSONResponse({"ok": True, "msg": "已保存，下一条群消息生效"})


@app.post("/api/judge/test")
async def test_judge(request: Request) -> JSONResponse:
    """Run the judge prompt against a sample message and return its verdict."""
    body = await request.json()
    message = str(body.get("message", "")).strip() or "今天好累啊"
    recent = str(body.get("recent", "")).strip() or "(暂无更早消息)"
    backend = str(body.get("backend") or "local").lower()

    if backend == "api":
        api_cfg = read_json(JUDGE_API_FILE, {})
        for kw in api_cfg.get("ignore", []):
            if kw and kw in message:
                return JSONResponse(
                    {"verdict": "0", "source": f"命中免打扰规则：{kw}", "ms": 0}
                )
        for kw in api_cfg.get("force_reply", []):
            if kw and kw in message:
                return JSONResponse(
                    {"verdict": "1", "source": f"命中必答规则：{kw}", "ms": 0}
                )
        for pattern in api_cfg.get("force_patterns", []):
            try:
                if re.search(str(pattern), message):
                    return JSONResponse(
                        {"verdict": "1", "source": f"命中必答正则：{pattern}", "ms": 0}
                    )
            except re.error:
                continue
        for pattern in api_cfg.get("followup_patterns", []):
            try:
                if re.search(str(pattern), message):
                    return JSONResponse(
                        {"verdict": "1", "source": f"命中追问直通：{pattern}", "ms": 0}
                    )
            except re.error:
                continue
        if len(message) <= 3:
            return JSONResponse({"verdict": "0", "source": "过短不接", "ms": 0})

        prompt = str(api_cfg.get("prompt") or "")
        prompt = (
            prompt.replace("{recent}", recent)
            .replace("{last_bot}", str(body.get("last_bot") or "(还没说过话)"))
            .replace("{message}", message)
        )
        base, key, model = _judge_api_credentials(api_cfg)
        if not key:
            return JSONResponse({"ok": False, "msg": "第三方判官还没有可用密钥"})
        started = time.time()
        try:
            with httpx.Client(timeout=15) as client:
                resp = client.post(
                    f"{base}/chat/completions",
                    headers={"Authorization": f"Bearer {key}"},
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": int(api_cfg.get("max_tokens", 2) or 2),
                        "temperature": float(api_cfg.get("temperature", 0) or 0),
                        "thinking": {"type": "disabled"},
                    },
                )
                resp.raise_for_status()
                payload = resp.json()
            verdict = payload["choices"][0]["message"]["content"].strip()
        except Exception as exc:  # noqa: BLE001 - surface the failure in the UI
            return JSONResponse({"ok": False, "msg": f"第三方判官调用失败：{exc}"})
        usage = payload.get("usage") or {}
        return JSONResponse(
            {
                "verdict": verdict[:4],
                "source": f"API 判定（{model}）",
                "ms": int((time.time() - started) * 1000),
                "tokens": int(usage.get("total_tokens") or 0),
            }
        )

    data = read_json(JUDGE_FILE, {"prompt": DEFAULT_JUDGE_PROMPT})

    for kw in data.get("ignore", []):
        if kw and kw in message:
            return JSONResponse({"verdict": "0", "source": f"命中免打扰规则：{kw}", "ms": 0})
    for kw in data.get("force_reply", []):
        if kw and kw in message:
            return JSONResponse({"verdict": "1", "source": f"命中必答规则：{kw}", "ms": 0})
    for pattern in data.get("force_patterns", []):
        try:
            if re.search(str(pattern), message):
                return JSONResponse(
                    {"verdict": "1", "source": f"命中必答正则：{pattern}", "ms": 0}
                )
        except re.error:
            continue
    if len(message) <= 3:
        return JSONResponse({"verdict": "0", "source": "过短不接", "ms": 0})

    prompt = str(data.get("prompt") or DEFAULT_JUDGE_PROMPT)
    prompt = prompt.replace("{recent}", recent).replace("{message}", message)

    started = time.time()
    try:
        with httpx.Client(timeout=12) as client:
            resp = client.post(
                JUDGE_URL,
                headers={"Authorization": "Bearer sk-judge-local"},
                json={
                    "model": "Qwen3-1.7B",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 4,
                    "temperature": 0,
                    "grammar": 'root ::= "0" | "1"',
                    "chat_template_kwargs": {"enable_thinking": False},
                },
            )
            resp.raise_for_status()
            verdict = resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as exc:  # noqa: BLE001 - surface the failure in the UI
        return JSONResponse({"ok": False, "msg": f"判官没响应（8082）：{exc}"})
    return JSONResponse(
        {"verdict": verdict[:4], "source": "模型判定", "ms": int((time.time() - started) * 1000)}
    )


_APIMODE_MODULE = None


def apimode_module():
    """Load the apimode plugin as a plain module.

    The plugin already owns every side effect of a mode switch (provider flags,
    vision mode, unloading the local models, restart). Importing it keeps one
    implementation instead of a drifting copy in the dashboard.

    Returns:
        The imported module object.

    Raises:
        Exception: When the module cannot be imported.
    """
    global _APIMODE_MODULE
    if _APIMODE_MODULE is not None:
        return _APIMODE_MODULE
    astrbot_root = str(ROOT / "apps" / "AstrBot")
    if astrbot_root not in sys.path:
        sys.path.insert(0, astrbot_root)
    path = PLUGIN_DIR / "astrbot_plugin_apimode" / "main.py"
    spec = importlib.util.spec_from_file_location("_dash_apimode", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载 {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _APIMODE_MODULE = module
    return module


@app.post("/api/mode")
async def switch_mode(request: Request) -> JSONResponse:
    """Switch the whole bot between the local model and the third-party API."""
    body = await request.json()
    mode = str(body.get("mode", "")).strip()
    if mode not in ("local", "third_party"):
        return JSONResponse({"ok": False, "msg": "mode 只能是 local / third_party"})
    if api_mode() == mode:
        return JSONResponse({"ok": True, "msg": "已经是这个模式了"})
    try:
        mod = apimode_module()
    except Exception as exc:  # noqa: BLE001 - surface the failure in the UI
        return JSONResponse({"ok": False, "msg": f"切换模块加载失败：{exc}"})
    try:
        mod.set_provider_mode(mode)
        mod.tune_reply_for_mode(mode)
        if mode == "third_party":
            mod.set_thinking("off")
            mod.set_vision_mode("third_party")
            stopped = mod.unload_local_models()
            detail = f"已卸载本地服务 {len(stopped)} 个"
        else:
            mod.tune_local_provider()
            mod.set_vision_mode("local")
            mod.start_local_models()
            detail = "本地模型启动中（约 1 分钟）"
        state = mod.load_state()
        state["mode"] = mode
        mod.save_state(state)
        mod.schedule_restart(8)
    except Exception as exc:  # noqa: BLE001
        return JSONResponse({"ok": False, "msg": f"切换失败：{exc}"})
    return JSONResponse(
        {
            "ok": True,
            "msg": (
                f"已切到{'第三方 API' if mode == 'third_party' else '本地模型'}，"
                f"{detail}；8 秒后 AstrBot 重启（QQ 不断线）"
            ),
        }
    )


@app.get("/api/plugins")
def plugins() -> JSONResponse:
    """List installed AstrBot plugins with their metadata."""
    items = []
    if PLUGIN_DIR.exists():
        for path in sorted(PLUGIN_DIR.iterdir()):
            if not path.is_dir() or path.name.startswith("."):
                continue
            meta = {}
            meta_file = path / "metadata.yaml"
            if meta_file.exists():
                for line in meta_file.read_text(encoding="utf-8").splitlines():
                    if ":" in line:
                        key, value = line.split(":", 1)
                        meta[key.strip()] = value.strip()
            items.append(
                {
                    "slug": path.name,
                    "name": meta.get("name", path.name),
                    "desc": meta.get("desc", ""),
                    "version": meta.get("version", ""),
                    "files": len(list(path.rglob("*.py"))),
                }
            )
    return JSONResponse({"items": items})


@app.post("/api/start")
def start_all() -> JSONResponse:
    """Launch the stack in the background."""
    subprocess.Popen(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ROOT / "start-all.ps1"),
        ],
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    return JSONResponse({"ok": True, "msg": "启动中，约 30 秒后刷新"})


@app.post("/api/stop")
def stop_all() -> JSONResponse:
    """Stop the stack in the background."""
    subprocess.Popen(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ROOT / "stop-all.ps1"),
        ],
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    return JSONResponse({"ok": True, "msg": "停止中"})


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    """Serve the single-page dashboard."""
    return (Path(__file__).parent / "index.html").read_text(encoding="utf-8")
