from pathlib import Path
p = Path(r"D:\QQNTBOT\dashboard\app.py")
s = p.read_text(encoding="utf-8")

block = '''@app.get("/api/ltm/recent")
def ltm_recent(limit: int = 40) -> JSONResponse:
    """Return recent group messages that could be turned into memories."""
    limit = max(1, min(200, limit))
    if not BOT_DB.exists():
        return JSONResponse({"items": []})
    con = sqlite3.connect(f"file:{BOT_DB}?mode=ro", uri=True, timeout=5)
    try:
        rows = con.execute(
            "SELECT id, created_at, user_id, sender_name, content "
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
        if not text or len(text) < 2:
            continue
        uid = str(umo).split(":")[-1].split("_")[-1]
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


@app.get("/api/memories")'''
s = s.replace('@app.get("/api/memories")', block, 1)
p.write_text(s, encoding="utf-8")
print("ltm api added")
