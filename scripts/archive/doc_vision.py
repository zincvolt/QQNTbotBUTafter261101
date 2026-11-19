from pathlib import Path
p = Path(r"D:\QQNTBOT\docs\THIRD-PARTY-API.md")
s = p.read_text(encoding="utf-8")
section = """---

## 6.5 图片理解（DeepSeek 看图）

`deepseek-flash` **支持图像输入**（`deepseek-v4-pro` 不支持），已经配好：

```json
"model": "deepseek-flash",
"modalities": ["image", "text"]
```

行为区别：

| 模式 | 图片怎么处理 |
|---|---|
| 本地 | 本地 9B 不支持图片，peer 插件会把图片剥掉，只靠 OCR 插件转成文字 |
| 第三方 | **不再剥图**，图片原样发给 DeepSeek 直接看 |

所以第三方模式下 `vl-ocr`（本地 OCR）是停用的——没必要先转文字，还多一层损耗。

peer 插件里的判断：

```python
if req.image_urls and not _third_party_mode():
    req.image_urls = []      # 只有本地模式才剥
```

**成本提醒**：图片按 token 计费，一张普通图大约 1000~2000 tokens。
群里有人连续刷图时，建议把 `/额度` 设低一点。

"""
s = s.replace("---\n\n## 7. 每日额度", section + "---\n\n## 7. 每日额度", 1)
p.write_text(s, encoding="utf-8")
print("文档已更新:", len(s.splitlines()), "行")
