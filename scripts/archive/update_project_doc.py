from pathlib import Path
p = Path(r"D:\QQNTBOT\docs\PROJECT.md")
s = p.read_text(encoding="utf-8")

# 关键文件表补新字段
s = s.replace(
    "| `data\\reply.json` | 表情概率 + 文本替换正则 |",
    "| `data\\reply.json` | 回复预算 / 召唤词开关 / 上下文时间窗 / 回复与表情概率 / 文本替换正则 |",
)
# 链路图补召唤词与预算
s = s.replace(
    """ ├─ 是不是 @ / 唤醒？
 │    ├─ 是 → 排队（不丢弃，按会话锁顺序处理）
 │    └─ 否 → 该群自动接话开了吗？
 │         ├─ 关 → 不接
 │         └─ 开 → 规则层（免打扰 / 必答关键词 / 必答正则）
 │              └─ 还没定 → 判官 Qwen3-1.7B 判 0/1""",
    """ ├─ 是不是 @ / 唤醒？
 │    ├─ 是 → 排队（不丢弃），计入回复预算
 │    └─ 否 → 命中召唤词（阿灰/小灰…）？
 │         ├─ 是 → 直接接，计入预算
 │         └─ 否 → 该群自动接话开了吗？
 │              ├─ 关 → 不接
 │              └─ 开 → 规则层（免打扰 / 必答关键词 / 必答正则）
 │                   └─ 还没定 → 判官 Qwen3-1.7B 判 0/1（温度 0.5）
 │                        └─ 预算未满 + 概率命中 → 接""",
)
# 补丁清单加第 6 条
s = s.replace(
    "| `builtin_stars\\astrbot\\main.py` | `GeneratorExit` 不算错误（stop 事件时不再刷红字） |",
    "| `builtin_stars\\astrbot\\main.py` | `GeneratorExit` 不算错误（stop 事件时不再刷红字） |\n"
    "| `core\\updater.py` | 禁止自动升级（`LOCAL_UPDATES_DISABLED`），保护上面 5 处补丁 |",
)
# 已知限制更新
s = s.replace(
    "6. **读图只认字**：OCR 能抄文字，纯画面梗（一张猫）它看不懂",
    "6. **读图只认字**：OCR 能抄文字，纯画面梗（一张猫）它看不懂\n"
    "7. **会编造具体名词**：9B 遇到不认识的活动/关卡会硬编（已用提示词和证据校验缓解，未根治）\n"
    "8. **自称会漂移**：模型偶尔自造称呼（如\"本灰\"），靠 repeat_penalty 压，不能根除",
)
p.write_text(s, encoding="utf-8")
print("PROJECT.md updated, lines:", len(s.splitlines()))
