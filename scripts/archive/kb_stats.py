import json, httpx
BASE="http://127.0.0.1:6185"
KB="43291192-3ce7-4cda-88c0-9f1332dca75d"
with httpx.Client(timeout=60) as c:
    t=c.post(f"{BASE}/api/auth/login", json={"username":"astrbot","password":"qqbot2026"}).json()["data"]["token"]
    h={"Authorization":f"Bearer {t}"}
    st=c.get(f"{BASE}/api/v1/knowledge-bases/{KB}/stats", headers=h).json()
    print("stats:", json.dumps(st.get("data"), ensure_ascii=False)[:300])
    docs=c.get(f"{BASE}/api/v1/knowledge-bases/{KB}/documents?page=1&page_size=5", headers=h).json()
    print("docs:", json.dumps(docs.get("data"), ensure_ascii=False)[:400])
