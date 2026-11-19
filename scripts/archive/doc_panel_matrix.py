from pathlib import Path
p = Path(r"D:\QQNTBOT\docs\THIRD-PARTY-API.md")
s = p.read_text(encoding="utf-8")
add = """
---

## 9. 控制台面板对照（第三方模式）

**模式的唯一真相**是 `agent_runner.config.model.provider_id`（WebUI 里选的那个），
不是 `data/api_mode.json`。后者只是 `/切换` 的记账，两边不一致时以配置为准
（控制台、peer、ltm 都已改成读配置）。

| 面板 | 第三方模式 | 说明 |
|---|---|---|
| 状态灯 | ✅ | 多了 VL/OCR 两个灯，返回里带 `mode` |
| 系统状态 | ✅ | CPU/内存/显存无关，照常 |
| 手动加记忆 / 最近记住的事 | ✅ | 直接写 memory.db |
| 最近对话 / 对话上下文 | ✅ | 读 AstrBot 自己的库 |
| 触发权限 / 自动接话 / 水群 | ✅ | 读 cmd_config |
| 人格 | ✅（只读展示） | **不提供服务端改写**，提示词你自己维护 |
| 判官 | ✅ | 1.7B 本地，第三方模式下仍可用（≤2B） |
| 判官与思维链 | ⚠️ 已适配 | 开关映射到 `thinking.type`，预算折算成 `reasoning_effort` |
| 回复行为 | ✅ | reply.json |
| 模型采样参数 | ⚠️ 部分生效 | 温度在 DeepSeek 思考模式下被忽略；`repeat_penalty` 不支持 |
| 主模型 | ⚠️ 已适配 | 第三方模式下列表变成 `deepseek-flash` / `deepseek-v4-pro` |
| 图片理解 | ✅ | 显示 caption 缓存；本地 VL 状态看状态灯 `vl` |
| 已装模块 | ✅ | 插件列表 |
| 日志 | ✅ | AstrBot 日志尾部 |

“⚠️ 已适配”指这次改过：面板不再只读写 `provider[0]`，而是读写**当前真正在用的 provider**。

"""
s = s.rstrip() + "\n" + add
p.write_text(s, encoding="utf-8")
print("THIRD-PARTY-API.md:", len(s.splitlines()), "行")
