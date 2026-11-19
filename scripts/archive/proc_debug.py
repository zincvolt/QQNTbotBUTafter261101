import psutil
for p in psutil.process_iter(["pid","name","memory_info","cmdline"]):
    try:
        n = p.info["name"] or ""
        if n.startswith("python") or n == "QQ.exe" or n.startswith("llama"):
            cmd = " ".join(p.info["cmdline"] or [])[:90]
            print(f'{p.info["pid"]:>6} {n:<14} {round(p.info["memory_info"].rss/1048576)}MB  {cmd}')
    except Exception:
        pass
