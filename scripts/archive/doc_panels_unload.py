from pathlib import Path
p = Path(r"D:\QQNTBOT\docs\THIRD-PARTY-API.md")
s = p.read_text(encoding="utf-8")
add = """
---

## 10. 控制台新增面板（审查 / 额度 / 识图）

### 审查 · 额度 · 省 token

- **本群审查开关**：按白名单群逐个勾选，写 `api_mode.json.review_groups`
- **每日额度**：`daily_limit`，0 = 不限；`used.tokens` 每天按日期重置
- **省 token 模式**：勾上后只发最近 N 条历史
- **历史消息数量滑块**：2~40 条，写 `history_keep`，由 `astrbot_plugin_apimode`
  在请求前截断 `req.contexts`

写入即时生效，**不需要重启**。

### 识图

| 按钮 | 效果 |
|---|---|
| 本地 VL 读图 | 图先转文字再发给模型，不耗视觉 token |
| 交给第三方看图 | 图片直接发 DeepSeek |
| 关闭读图 | 忽略图片 |

另有「启动/停止本地 VL」按钮，状态显示本地 VL 在线/离线、端口、模型名。

### 不支持的功能自动置灰

- 第三方模式下 `repeat_penalty` 滑条禁用，显示「API 不支持」
- 第三方模式下双判官勾选框禁用（要本地 9B）
- 第三方模式下思维链预算滑条禁用，改为显示 `reasoning_effort` 档位

## 11. 切换时自动卸载本地模型

主模型切到 DeepSeek 后，会**自动卸载**这三个本地服务：

| 端口 | 服务 | 处理 |
|---|---|---|
| 8080 | 本地 9B 聊天 | 终止进程 |
| 8083 | OCR | 终止进程 |
| 8085 | 本地识图 VL | 终止进程 |

保留：8082 判官（1.7B，筛回复频率继续用）、8097 嵌入（知识库要用）。

实测卸载后内存空闲从 7.8GB 回到 14.2GB。

切回本地时会自动把它们拉起来（`start-router.ps1` / `start-ocr.ps1` / `start-vl.ps1`），
切换同时会把识图模式改成 `local`；切到 API 时识图改成 `third_party`。

守护逻辑：`astrbot_plugin_apimode` 每 20 秒读一次 `agent_runner` 的 provider，
发现从本地变 API（或反向）就执行卸载/拉起，所以**在 WebUI 里直接改主模型也会生效**。

⚠️ 卸载后本地 fallback 不可用：DeepSeek 报错时没有备用模型。要恢复就 `/切换 api 本地`。
"""
s = s.rstrip() + "\n" + add
p.write_text(s, encoding="utf-8")
print("文档:", len(s.splitlines()), "行")
