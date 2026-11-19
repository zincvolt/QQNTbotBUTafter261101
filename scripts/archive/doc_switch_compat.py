"""Write the switch-compatibility chapter into the third-party API doc."""

from pathlib import Path

DOC = Path(r"D:\QQNTBOT\docs\THIRD-PARTY-API.md")
s = DOC.read_text(encoding="utf-8")

chapter = """
---

## 13. 双向切换的兼容性（实测）

这一节是 2026-11-18 晚上真机来回切了一次之后写的，不是推演。

### 13.1 切到第三方会发生什么

| 动作 | 结果 |
|---|---|
| `agent_runner.config.model.provider_id` | `local-llama` → `deepseek` |
| `fallback_provider_ids` | `["local-llama"]`（本地兜底，但此时本地已卸载） |
| provider 启用位 | `local-llama`、`vl-ocr` 关；`deepseek` 开 |
| `reply.json` | `meme_chance=0`、`text_rules=[]`、`dual_judge=false`、`thinking=false` |
| DeepSeek 参数 | `thinking.type=disabled`、`temperature=0.8`、`max_tokens` 保留 |
| 识图模式 | `third_party`（图直接发 DeepSeek） |
| 本地进程 | **终止** 8080 聊天 / 8083 OCR / 8085 识图 VL |
| 保留 | 8082 判官（1.7B）、8097 嵌入（知识库） |

内存实测：**7.8 GB 空闲 → 16.5 GB 空闲**。

### 13.2 切回本地会发生什么

| 动作 | 结果 |
|---|---|
| `provider_id` | `deepseek` → `local-llama` |
| 启用位 | `local-llama`、`vl-ocr` 开；`deepseek` 关 |
| `reply.json` | `meme_chance=0.3`、`text_rules` 补回句号规则、`dual_judge=true` |
| 本地 provider 参数 | 复位成 `max_tokens≤300`、`temperature=0.5`、`enable_thinking=false` |
| 识图模式 | `local`（图先由 VL 转文字，不进第三方） |
| 本地进程 | **自动拉起** 8080 / 8083 / 8085 |
| LTM 记忆抽取 | 从「跳过」恢复为「每 30 分钟扫一次」 |

内存实测：**16.5 GB 空闲 → 2.1 GB 空闲**（9B 的 131K 上下文很吃内存）。

### 13.3 切回来会不会炸：实测结果

```
本地 9B        「只回两个字：在线」→ 在线         ✅
本地 VL 识图   江苏 4 场兽展…（21.4 秒）          ✅
OCR 8083       已监听                              ✅
判官 8082      已监听                              ✅
AstrBot        适配器已连接，无 provider 报错       ✅
控制台面板     采样/思维链/主模型 全部切回本地视图  ✅
```

**结论：不会炸。** 早先会出问题的两处已经修掉：

1. 本地 provider 带着 `enable_thinking=true` + `max_tokens=500` 回来
   → 回复又慢又长，现在强制复位
2. 表情概率和文本规则停在第三方精简的 0 和空
   → 本地模型少了两个保底，现在自动补回

### 13.4 切换时不要手动做的事

- 别在 WebUI 里同时启用 local-llama 和 deepseek —— 选哪个由 `agent_runner` 决定，
  同时启用只会让人搞不清当前在跑谁
- 别在切换的 8 秒重启窗口里改配置，会被覆盖
- 切回本地后如果卡顿，先看内存：`Get-CimInstance Win32_OperatingSystem | % FreePhysicalMemory`

### 13.5 内存不够时的两个开关

| 做法 | 效果 |
|---|---|
| 把 `models.ini` 里主模型 `c = 131072` 改小（如 32768） | 省几 GB，长上下文能力下降 |
| 控制台「识图」面板点「停止本地 VL」 | 省 1~2 GB，识图改走第三方或关闭 |

### 13.6 守护逻辑

`astrbot_plugin_apimode` 每 20 秒读一次 `agent_runner` 的 provider：

- 本地 → DeepSeek：停 8080/8083/8085，识图切第三方
- DeepSeek → 本地：拉脚本，识图切本地，参数复位

所以**直接在 WebUI 里改主模型也会触发**，不必非得走 `/切换` 命令。
"""

if "## 13. 双向切换的兼容性" not in s:
    s = s.rstrip() + "\n" + chapter
    DOC.write_text(s, encoding="utf-8")
    print("已写入 §13，文档", len(s.splitlines()), "行")
else:
    print("已存在")
