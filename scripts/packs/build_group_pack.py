"""Build a pack from the stickers collected out of the group chat.

The set mixes several artists, so the pack is named after the source (群友投喂)
rather than one artist. Categories were assigned by inspecting the contact
sheets; the plugin only uses category descriptions to pick a sticker.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

SRC = Path(r"D:\QQNTBOT\build\collected")
PLUGIN_DATA = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugin_data\meme_manager")
PACK_ID = "group-feed"
PACK_NAME = "群友投喂"

ASSIGN: dict[str, list[int]] = {
    "开心": [1, 3, 4, 5, 10, 12, 13, 17, 22, 28, 34, 42, 57, 58, 62, 72, 75, 78],
    "无语": [8, 27, 30, 35, 36, 39, 40, 41, 46, 47, 61],
    "生气": [29, 31, 56, 59, 60],
    "惊讶": [16, 18, 33, 37, 43, 52, 55, 65, 77],
    "累了": [6, 14, 23, 24, 45, 67, 68, 70, 74],
    "吃喝": [2, 9, 19, 20, 21, 25, 73],
    "难过": [26, 38, 49, 51, 54, 63],
    "日常": [0, 7, 11, 15, 32, 44, 48, 50, 53, 64, 66, 69, 76, 79, 80],
}

DESCRIPTIONS = {
    "开心": "开心、兴奋、比耶比心、星星眼，适合接好消息和打闹",
    "无语": "翻白眼、斜眼、脸垮下来，适合吐槽和表达无语",
    "生气": "炸毛、凶人、拍桌，适合假装发火",
    "惊讶": "瞪眼、问号、愣住，适合被惊到",
    "累了": "趴着、睡觉、流汗，适合说累了想躺",
    "吃喝": "吃东西、喝奶茶、拿快餐，适合饭点闲聊",
    "难过": "哭、委屈、sorry，适合认怂和安慰",
    "日常": "各种日常动作和杂图，适合随机接一句",
}


def main() -> None:
    """Copy the collected stickers into a registered pack."""
    files = sorted(SRC.glob("*.gif"), key=lambda p: p.stat().st_mtime)
    pack_dir = PLUGIN_DATA / "packs" / PACK_ID
    if pack_dir.exists():
        shutil.rmtree(pack_dir)

    copied = 0
    used: set[int] = set()
    for category, indexes in ASSIGN.items():
        target = pack_dir / "memes" / category
        target.mkdir(parents=True, exist_ok=True)
        for idx in indexes:
            if idx >= len(files) or idx in used:
                continue
            used.add(idx)
            shutil.copy2(files[idx], target / files[idx].name)
            copied += 1

    manifest = {
        "schema_version": 1,
        "id": PACK_ID,
        "name": PACK_NAME,
        "version": "1.0.0",
        "description": "从群里收到的兽人表情，多位画师混编，按情绪分了 8 类",
        "tags": ["furry", "anthro", "group", "mixed-artists"],
        "categories": {k: {"description": v} for k, v in DESCRIPTIONS.items()},
    }
    (pack_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (pack_dir / "memes_data.json").write_text("{}\n", encoding="utf-8")

    registry_path = PLUGIN_DATA / "registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    packs = [p for p in registry.get("installed_packs", []) if p.get("id") != PACK_ID]
    packs.append(
        {
            "id": PACK_ID,
            "name": PACK_NAME,
            "version": "1.0.0",
            "enabled": True,
            "installed_at": "2026-11-17T10:20:00+00:00",
        }
    )
    registry["installed_packs"] = packs
    registry_path.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"copied {copied} stickers into {len(ASSIGN)} categories")


if __name__ == "__main__":
    main()
