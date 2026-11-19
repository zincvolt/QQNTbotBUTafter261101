"""Build a curated furry meme pack from the emoji.gg download.

Categories were assigned by looking at the contact sheet: unrelated images
(Mario, cheese, Shrek, real dogs) and two offensive text memes are dropped.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

SRC = Path(r"D:\QQNTBOT\_downloads\furry-emoji")
PLUGIN_DATA = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugin_data\meme_manager")
PACK_ID = "furry-emoji"
PACK_NAME = "兽人表情"

# index on the contact sheet -> category
ASSIGN: dict[str, list[int]] = {
    "卖萌": [6, 11, 13, 18, 19, 28, 34, 41, 58, 61, 64, 67, 70, 76, 51],
    "无语": [0, 20, 22, 5, 33],
    "心动": [21, 24, 47, 73],
    "困了": [2, 3, 23, 25, 43],
    "打招呼": [7, 8, 37, 42, 52, 57],
    "贴贴": [15, 16, 45, 69, 71],
    "开心": [26, 27, 35, 72],
    "杂图": [4, 14, 30, 31, 36, 40, 46, 54, 55, 59, 65, 66, 68, 74, 39],
}

DESCRIPTIONS = {
    "卖萌": "软萌可爱的兽人表情：撒娇、示好、被夸了有点飘",
    "无语": "翻白眼、无奈、看傻子一样的表情，适合吐槽",
    "心动": "爱心眼、脸红、害羞，适合表达喜欢或被人撩到",
    "困了": "打哈欠、趴着睡、说晚安，适合表示累了",
    "打招呼": "招手、比耶、出门打招呼，适合进场和回应",
    "贴贴": "两只兽贴在一起、抱抱蹭蹭，适合亲密互动",
    "开心": "大笑、欢呼、兴奋，适合庆祝和接梗",
    "杂图": "各种兽人杂图，适合随机插一句",
}


def main() -> None:
    """Copy selected emojis into category folders and register the pack."""
    files = sorted(SRC.glob("*"))
    pack_dir = PLUGIN_DATA / "packs" / PACK_ID
    if pack_dir.exists():
        shutil.rmtree(pack_dir)

    copied = 0
    for category, indexes in ASSIGN.items():
        target = pack_dir / "memes" / category
        target.mkdir(parents=True, exist_ok=True)
        for idx in indexes:
            if idx >= len(files):
                continue
            src_file = files[idx]
            shutil.copy2(src_file, target / src_file.name)
            copied += 1

    manifest = {
        "schema_version": 1,
        "id": PACK_ID,
        "name": PACK_NAME,
        "version": "1.0.0",
        "description": "从 emoji.gg furry 分类挑选整理的兽人表情包，按情绪分了 9 类",
        "tags": ["furry", "anthro", "emoji"],
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
            "installed_at": "2026-11-17T10:05:00+00:00",
        }
    )
    registry["installed_packs"] = packs
    registry_path.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    rules_path = PLUGIN_DATA / "selection_rules.json"
    rules = json.loads(rules_path.read_text(encoding="utf-8"))
    rules["rules"] = [r for r in rules.get("rules", []) if r.get("id") != "furry-default"]
    rules["rules"].insert(0, {"id": "furry-default", "scope": "default", "pack_id": PACK_ID})
    rules_path.write_text(
        json.dumps(rules, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"copied {copied} stickers into {len(ASSIGN)} categories")


if __name__ == "__main__":
    main()
