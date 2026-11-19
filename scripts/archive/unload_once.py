import psutil
ports = (8080, 8083, 8085)
freed = []
for port in ports:
    for conn in psutil.net_connections(kind="inet"):
        if conn.laddr and conn.laddr.port == port and conn.status == psutil.CONN_LISTEN and conn.pid:
            try:
                proc = psutil.Process(conn.pid)
                rss = proc.memory_info().rss / 1024**3
                name = proc.name()
                proc.terminate()
                freed.append(f"{port}({name}, {rss:.1f}GB)")
            except Exception as e:
                freed.append(f"{port}: {e}")
print("已卸载:", freed or "无")
