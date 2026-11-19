"""Recreate the knowledge base cleanly and import the LLM KB without duplicates."""

from __future__ import annotations

import contextlib
import json
import time
from pathlib import Path

import httpx

BASE = "http://127.0.0.1:6185"
NAME = "本地知识库"
SRC = Path(r"D:\LLM\kb")
CHUNK = 600
OVERLAP = 80
BATCH_FILES = 25


def client_with_token() -> httpx.Client:
    """Return a client carrying a valid dashboard JWT."""
    c = httpx.Client(timeout=120)
    tok = c.post(f"{BASE}/api/auth/login",
                 json={"username": "astrbot", "password": "qqbot2026"}).json()["data"]["token"]
    c.headers.update({"Authorization": f"Bearer {tok}"})
    return c


def delete_old(c: httpx.Client) -> None:
    """Delete every existing knowledge base with the target name."""
    items = c.get(f"{BASE}/api/v1/knowledge-bases",
                  params={"page": 1, "page_size": 50}).json()["data"]["items"]
    for kb in items:
        print("删除旧库:", kb["kb_name"], kb["kb_id"], "文档数", kb.get("doc_count"))
        r = c.delete(f"{BASE}/api/v1/knowledge-bases/{kb['kb_id']}")
        print("  ->", r.status_code, r.text[:100])


def create_kb(c: httpx.Client) -> str:
    """Create the knowledge base and return its id."""
    r = c.post(f"{BASE}/api/v1/knowledge-bases", json={
        "name": NAME,
        "description": "从 D:\\LLM\\kb 复制",
        "embedding_provider_id": "local-embed",
        "chunk_size": CHUNK,
        "chunk_overlap": OVERLAP,
    })
    r.raise_for_status()
    kb_id = r.json()["data"]["kb_id"]
    print("新建知识库:", kb_id)
    return kb_id


def split_text(text: str) -> list[str]:
    """Split text into overlapping chunks on paragraph boundaries."""
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    buf = ""
    for p in paras:
        if len(buf) + len(p) + 2 <= CHUNK:
            buf = f"{buf}\n\n{p}" if buf else p
            continue
        if buf:
            chunks.append(buf)
        while len(p) > CHUNK:
            chunks.append(p[:CHUNK])
            p = p[CHUNK - OVERLAP:]
        buf = p
    if buf:
        chunks.append(buf)
    return chunks


def main() -> None:
    """Delete old KBs, rebuild, and import all markdown files once."""
    started = time.time()
    with contextlib.closing(client_with_token()) as c:
        delete_old(c)
        kb_id = create_kb(c)

        files = sorted(SRC.rglob("*.md"))
        print(f"待导入 {len(files)} 个文件")

        ok_files = 0
        chunk_total = 0
        failures: list[str] = []

        for start in range(0, len(files), BATCH_FILES):
            batch = files[start:start + BATCH_FILES]
            docs = []
            for path in batch:
                try:
                    text = path.read_text(encoding="utf-8", errors="ignore")
                except OSError as exc:
                    failures.append(f"{path}: {exc}")
                    continue
                chunks = split_text(text)
                if chunks:
                    docs.append({
                        "file_name": str(path.relative_to(SRC)),
                        "file_type": "md",
                        "chunks": chunks,
                    })
            if not docs:
                continue

            try:
                r = c.post(
                    f"{BASE}/api/v1/knowledge-bases/{kb_id}/documents/import",
                    json={"documents": docs, "batch_size": 32,
                          "tasks_limit": 4, "max_retries": 2},
                )
                if r.status_code != 200:
                    failures.append(f"batch {start}: {r.status_code} {r.text[:150]}")
                    continue
                task_id = r.json()["data"].get("task_id")
            except Exception as exc:  # noqa: BLE001
                failures.append(f"batch {start}: {exc!r}")
                continue

            status = "unknown"
            for _ in range(150):
                time.sleep(1.5)
                try:
                    info = c.get(
                        f"{BASE}/api/v1/knowledge-bases/tasks/{task_id}"
                    ).json().get("data", {})
                    status = info.get("status", "unknown")
                except Exception:  # noqa: BLE001
                    break
                if status in ("completed", "failed"):
                    break

            ok_files += len(docs)
            chunk_total += sum(len(d["chunks"]) for d in docs)
            print(f"[{ok_files}/{len(files)}] 块 {chunk_total} 状态 {status} "
                  f"{int(time.time()-started)}s", flush=True)

        print("完成。文件", ok_files, "块", chunk_total, "失败", len(failures))
        if failures:
            for f in failures[:10]:
                print("  失败:", f)
        st = c.get(f"{BASE}/api/v1/knowledge-bases/{kb_id}/stats").json()["data"]
        print("服务端统计:", json.dumps(st, ensure_ascii=False))


if __name__ == "__main__":
    main()
