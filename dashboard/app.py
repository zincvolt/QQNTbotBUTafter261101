"""QQ bot dashboard: status, system load, logs, memories, chats, access, tuning.

Reads existing SQLite databases read-only and tails existing log files.
State changes only happen through the start/stop/restart scripts, or by
writing the JSON config files that the plugins read.
"""

from __future__ import annotations

import json
import re
import socket
import sqlite3
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
import psutil
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

ROOT = Path(r"D:\QQNTBOT")
MEM_DB = ROOT / "data" / "memory.db"
BOT_DB = ROOT / "apps" / "AstrBot" / "data" / "data_v4.db"
CFG = ROOT / "apps" / "AstrBot" / "data" / "cmd_config.json"
NAPCAT_LOG_DIR = ROOT / "apps" / "NapCat" / "logs"
BOT_LOG_DIR = ROOT / "apps" / "AstrBot" / "data" / "logs"
PERSONA_FILE = ROOT / "data" / "persona.json"
JUDGE_FILE = ROOT / "data" / "judge.json"
WATER_FILE = ROOT / "data" / "water.json"
AUTOREPLY_FILE = ROOT / "data" / "autoreply.json"
REPLY_FILE = ROOT / "data" / "reply.json"
PLUGIN_DIR = ROOT / "apps" / "AstrBot" / "data" / "plugins"
JUDGE_URL = "http://127.0.0.1:8082/v1/chat/completions"

CAPTION_DB = ROOT / "data" / "caption_cache.db"
MEME_DIR = ROOT / "apps" / "AstrBot" / "data" / "plugin_data" / "meme_manager"
MODELS_INI = Path(r"D:\LLM\scripts\models.ini")

PORTS = {
    "model": (8080, "本地模型"),
    "astrbot": (6185, "AstrBot"),
    "onebot": (6199, "OneBot WS"),
    "napcat": (6099, "NapCat"),
    "judge": (8082, "判官模型"),
    "vl": (8085, "本地读图"),
    "ocr": (8083, "OCR"),
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
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    entries = cfg["platform_settings"]["id_whitelist"]
    groups = [str(e) for e in entries if str(e).isdigit()]
    friends = [str(e).rsplit(":", 1)[-1] for e in entries if "FriendMessage" in str(e)]
    return {"groups": groups, "friends": friends, "admin": cfg.get("admins_id", [])}


def write_access(groups: list[str], friends: list[str]) -> list[str]:
    """Persist a new allowlist into the AstrBot config."""
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
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
        return json.loads(path.read_text(encoding="utf-8"))
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


@app.get("/api/status")
def status() -> JSONResponse:
    """Return component health plus small counters."""
    comps = [
        {"key": key, "label": label, "port": port, "up": port_open(port)}
        for key, (port, label) in PORTS.items()
    ]
    return JSONResponse(
        {
            "components": comps,
            "memories": memory_total(),
            "activity": recent_activity(),
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
        data = tail(Path(r"D:\LLM\logs\llama-router.log"), lines)
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
    cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))
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

    cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))
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
        cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))
        current["dual_judge_model"] = cfg["provider"][0]["model"]
    current["meme_chance"] = chance
    current["reply_chance"] = reply_chance
    if "history_minutes" in body:
        current["history_minutes"] = float(body["history_minutes"])
    if "reply_budget" in body:
        current["reply_budget"] = int(body["reply_budget"])
    if "reply_budget_minutes" in body:
        current["reply_budget_minutes"] = float(body["reply_budget_minutes"])
    # 正则规则：空列表视为"这次没传"，只有显式 clear_rules 才清空
    if rules or body.get("clear_rules"):
        current["text_rules"] = rules
    current.setdefault("history_minutes", 30)
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
    cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))
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

    cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))
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
    state.setdefault("used", {"date": "", "tokens": 0})
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
    cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))
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
    if "save_token" in body:
        state["save_token"] = bool(body["save_token"])
    if "history_keep" in body:
        try:
            state["history_keep"] = max(2, min(40, int(body["history_keep"])))
        except (TypeError, ValueError):
            return JSONResponse({"ok": False, "msg": "历史条数不对"})

    GUARD_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    return JSONResponse({"ok": True, "msg": "已保存（立即生效）"})


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
    cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))
    try:
        return str(cfg["provider"][0].get("model", ""))
    except (KeyError, IndexError):
        return ""


API_MODELS = ["deepseek-flash", "deepseek-v4-pro"]


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
    cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))
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
    write_json(
        JUDGE_FILE,
        {
            "prompt": prompt,
            "ignore": [str(x).strip() for x in body.get("ignore", []) if str(x).strip()],
            "force_reply": [
                str(x).strip() for x in body.get("force_reply", []) if str(x).strip()
            ],
        },
    )
    return JSONResponse({"ok": True, "msg": "已保存，下一条群消息就生效（无需重启）"})


@app.post("/api/judge/test")
async def test_judge(request: Request) -> JSONResponse:
    """Run the judge prompt against a sample message and return its verdict."""
    body = await request.json()
    message = str(body.get("message", "")).strip() or "今天好累啊"
    recent = str(body.get("recent", "")).strip() or "(暂无更早消息)"
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
