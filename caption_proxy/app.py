"""Caption cache proxy in front of the OCR server.

Sits between AstrBot and llama.cpp (8083):

    AstrBot -> 8084 (this proxy) -> 8083 (PaddleOCR-VL)

Every image is hashed first. A hit returns the stored description instantly
and never touches the model, so repeated memes cost nothing. A miss is
forwarded upstream and the answer is stored for next time.
"""

from __future__ import annotations

import base64
import hashlib
import json
import sqlite3
import time
from pathlib import Path

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

ROOT = Path(r"D:\QQNTBOT")
CACHE_DB = ROOT / "data" / "caption_cache.db"
UPSTREAM = "http://127.0.0.1:8083"
UPSTREAM_KEY = "sk-ocr-local"
MAX_CACHE_ENTRIES = 5000

app = FastAPI(title="Caption Cache Proxy")


def conn() -> sqlite3.Connection:
    """Open the cache database, creating the table on first use."""
    con = sqlite3.connect(CACHE_DB, timeout=10)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute(
        """CREATE TABLE IF NOT EXISTS captions (
               hash TEXT PRIMARY KEY,
               text TEXT NOT NULL,
               created REAL NOT NULL,
               hits INTEGER DEFAULT 0,
               last_hit REAL
           )"""
    )
    return con


def image_hash(image_url: str) -> str | None:
    """Return a stable hash for a data URL or plain URL."""
    if not image_url:
        return None
    if image_url.startswith("data:"):
        try:
            payload = image_url.split(",", 1)[1]
            raw = base64.b64decode(payload)
        except (IndexError, ValueError):
            return None
        return hashlib.sha256(raw).hexdigest()
    return hashlib.sha256(image_url.encode("utf-8")).hexdigest()


def extract_image(body: dict) -> tuple[str | None, str]:
    """Pull the first image URL and the text prompt out of a chat request."""
    prompt = ""
    image = None
    for msg in body.get("messages", []):
        content = msg.get("content")
        if isinstance(content, str):
            prompt = content or prompt
            continue
        if not isinstance(content, list):
            continue
        for part in content:
            ptype = part.get("type")
            if ptype == "text":
                prompt = part.get("text") or prompt
            elif ptype == "image_url":
                url = part.get("image_url")
                image = url.get("url") if isinstance(url, dict) else url
    return image, prompt


def cached(h: str) -> str | None:
    """Look up a cached caption and bump its counter."""
    con = conn()
    try:
        row = con.execute("SELECT text FROM captions WHERE hash = ?", (h,)).fetchone()
        if not row:
            return None
        con.execute(
            "UPDATE captions SET hits = hits + 1, last_hit = ? WHERE hash = ?",
            (time.time(), h),
        )
        con.commit()
        return row[0]
    finally:
        con.close()


def store(h: str, text: str) -> None:
    """Save a caption and trim the cache to a bounded size."""
    con = conn()
    try:
        con.execute(
            "INSERT OR REPLACE INTO captions (hash, text, created, hits, last_hit) "
            "VALUES (?, ?, ?, 0, ?)",
            (h, text, time.time(), time.time()),
        )
        con.execute(
            "DELETE FROM captions WHERE hash NOT IN ("
            "  SELECT hash FROM captions ORDER BY COALESCE(last_hit, created) DESC LIMIT ?)",
            (MAX_CACHE_ENTRIES,),
        )
        con.commit()
    finally:
        con.close()


def reply(text: str, model: str, cached_flag: bool) -> JSONResponse:
    """Build an OpenAI-compatible completion response."""
    return JSONResponse(
        {
            "id": f"cache-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": text},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "cached": cached_flag,
        }
    )


@app.get("/v1/models")
async def models() -> JSONResponse:
    """Pass the upstream model list through."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{UPSTREAM}/v1/models",
            headers={"Authorization": f"Bearer {UPSTREAM_KEY}"},
        )
        return JSONResponse(resp.json(), status_code=resp.status_code)


@app.post("/v1/chat/completions")
async def completions(request: Request) -> JSONResponse:
    """Serve captions from cache, forwarding misses to the OCR model."""
    body = await request.json()
    image, _prompt = extract_image(body)
    model = body.get("model", "PaddleOCR-VL-1.6")

    h = image_hash(image) if image else None
    if h:
        hit = cached(h)
        if hit is not None:
            return reply(hit, model, True)

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{UPSTREAM}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {UPSTREAM_KEY}",
                    "Content-Type": "application/json",
                },
                json=body,
            )
            data = resp.json()
    except Exception as exc:  # noqa: BLE001 - let the caller fall back
        return JSONResponse({"error": str(exc)}, status_code=502)

    text = ""
    try:
        text = data["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError):
        pass
    if h and text:
        store(h, text)
    return JSONResponse(data)


@app.get("/api/cache/stats")
def stats() -> JSONResponse:
    """Report cache size and total hits for the dashboard."""
    con = conn()
    try:
        row = con.execute(
            "SELECT COUNT(*), COALESCE(SUM(hits), 0) FROM captions"
        ).fetchone()
    finally:
        con.close()
    return JSONResponse({"entries": row[0], "hits": row[1], "limit": MAX_CACHE_ENTRIES})
