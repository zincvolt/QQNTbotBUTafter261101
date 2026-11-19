from pathlib import Path
p = Path(r"D:\QQNTBOT\docs\THIRD-PARTY-API.md")
s = p.read_text(encoding="utf-8")

add = """---

## 6.6 读图只在必要时

表情包不能每次都送进视觉模型（一张 1000~2000 tokens），所以加了一道判断：

```python
VISION_HINTS = ("截图", "看图", "这张图", "图上", "图里", "图片里",
                "识别", "翻译", "这是什么", "什么字", "写的啥", …)

def _should_read_images(text, images):
    if 命中上面的词:            return True
    if 句子里有问号:             return True
    if 图片 >= 3 张:            return True   # 多图多半是求助
    if 单张体积 > 60KB(base64): return True   # 长截图/照片
    return False                              # 其余当表情包，不读
```

实测：

| 消息 | 图 | 读不读 |
|---|---|---|
| `[表情包]` | 1 张小的 | ❌ 跳过 |
| `这图什么意思？` | 1 张 | ✅ 读 |
| `看这个截图` | 1 张 | ✅ 读 |
| 无文字 | 1 张大图 | ✅ 读 |
| 无文字 | 3 张 | ✅ 读 |

所以：**发表情包不会触发视觉**，只有明显在问图的时候才花这个钱。
日志里会打 `[peer] vision skipped: N image(s), likely sticker`。

---

## 6.7 思维链（第三方适配）

DeepSeek 的思考模式和本地 9B 用的参数不一样：

| | 本地 9B | DeepSeek |
|---|---|---|
| 开/关 | `chat_template_kwargs.enable_thinking` | `thinking: {type: enabled/disabled}` |
| 长度 | `max_tokens` | `reasoning_effort: low/high/max` |
| temperature | 生效 | 思考模式下**被忽略** |

所以 `/思维链` 命令改成按第三方语法写：

```
/思维链 off        关掉（默认，省钱）
/思维链 on         开，强度 high
/思维链 low        开，强度 low（最省）
/思维链 max        开，强度 max（最贵）
```

会写进 `deepseek` provider 的 `custom_extra_body`：

```json
{"thinking": {"type": "enabled"}, "reasoning_effort": "low"}
```

开启时会自动移除 `temperature`（思考模式下它无效，留着只是噪音）。

**成本提示**：思维链内容也按输出 token 计费，强度 `max` 可能让单条回复贵 3~5 倍。
日常群聊建议 `off`，遇到需要推理的话题再 `/思维链 low`。

"""
s = s.replace("---\n\n## 7. 每日额度", add + "---\n\n## 7. 每日额度", 1)
p.write_text(s, encoding="utf-8")
print("文档行数:", len(s.splitlines()))
