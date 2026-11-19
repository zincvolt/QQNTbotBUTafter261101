from pathlib import Path
p = Path(r"D:\QQNTBOT\dashboard\app.py")
s = p.read_text(encoding="utf-8")
# 常量名写错了：REPLY -> REPLY_FILE
s = s.replace('cfg = json.loads(REPLY.read_text(encoding="utf-8"))',
              'cfg = json.loads(REPLY_FILE.read_text(encoding="utf-8"))')
s = s.replace('REPLY.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")\n    return JSONResponse({"ok": True, "msg": msg})',
              'REPLY_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")\n    return JSONResponse({"ok": True, "msg": msg})')
p.write_text(s, encoding="utf-8")
print("REPLY -> REPLY_FILE 修正:", s.count("REPLY_FILE.read_text"))
