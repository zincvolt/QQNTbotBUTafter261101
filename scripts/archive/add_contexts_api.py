from pathlib import Path
p = Path(r"D:\QQNTBOT\dashboard\app.py")
s = p.read_text(encoding="utf-8")

block = '''@app.get("/api/contexts")
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
                "DELETE FROM preferences WHERE scope = 'umo' AND name = ? "
                "AND key = 'sel_conv_id'",
                (umo,),
            )
        con.commit()
        return JSONResponse({"ok": True, "msg": "已清空，下一条消息会开新对话"})
    except sqlite3.Error as exc:
        return JSONResponse({"ok": False, "msg": f"清空失败：{exc}"})
    finally:
        con.close()


@app.get("/api/chats")'''

s = s.replace('@app.get("/api/chats")', block, 1)
p.write_text(s, encoding="utf-8")
print("added contexts endpoints")
