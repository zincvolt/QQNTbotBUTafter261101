# 部署指引

> 目标：把这个 GitHub 代码仓变成一套**能跑的** QQ 机器人。
> 最后更新：2026-11-19
>
> 先读 README 的「缺失内容清单」——本仓库只有代码和配置模板，**不是开箱即用的完整环境**。
> 部署的本质是：把这里的代码，叠加到一套你自己准备的外部依赖之上。

---

## 0. 先判断你的场景

| 场景 | 你该做什么 |
|---|---|
| **A. 原机器上代码坏了 / 想同步最新代码** | 直接看 §5，几分钟搞定 |
| **B. 全新机器，从零搭一套** | 从头看 §1–§4，工作量较大（数小时） |
| **C. 只想看懂，不打算真跑** | 读 README + [HANDOFF.md](HANDOFF.md) 即可，到此为止 |

**重要现实**：本仓库刻意不含 QQ 客户端、NapCat 二进制、模型文件、venv（见 README 缺失清单）。
其中**改造版 QQ.exe、dbghelp.dll、删库 fork 的 NapCat 无法从公开渠道合法获取**。
所以场景 B 的"完整复现"实际上只有原作者或拿到其完整快照的人做得到。本指引会如实标注每一步的可获得性。

---

## 1. 前置依赖（外部准备，不在本仓库）

### 1.1 软件环境

| 依赖 | 版本 / 说明 | 可获得性 |
|---|---|---|
| Windows | PowerShell 5.1（脚本按其语法写） | ✅ |
| Python | 3.10+，给 AstrBot 和各服务用 | ✅ 官网 |
| QQNT | **9.9.25（build 42905/42941）** | ⚠️ 需旧版安装包 |
| 改过的QQ.exe + dbghelp.dll | 注入Liteloader，**匹配 9.9.25** | ❌ |
| LiteLoader | QQNT 加载器 | github |
| NapCat | 跑路了！ | ❌ |
| AstrBot | **4.29.4** 发行版（含 venv / main.py / requirements） | ✅ 官方，但需旧版 |
| 模型服务 | 本地 9B / 判官 1.7B / OCR / 向量 = 独立目录 `D:\LLM` | ⚠️ 见 §1.2 |

### 1.2 两种运行模式（决定你要准备什么）

| | 本地模式 | 第三方模式（DeepSeek） |
|---|---|---|
| 主模型 | 本地 9B（8080），吃 ~9.7GB 内存 | DeepSeek API（需 key + 付费） |
| 判官 | 本地 1.7B（8082） | 仍本地跑（≤2B） |
| OCR / 本地 VL | 8083 / 8085 | 停用 |
| 适合 | 无 API 预算、有足够内存 | 内存有限、追求回复质量 |

**资金/算力有限的话**：第三方模式的准入成本更低（只需一个 DeepSeek API key），不必准备 9B 大模型和 16GB+ 内存。

---

## 2. 安装步骤（场景 B）

### 步骤 1：装 QQNT 并锁版本

1. 安装 QQNT **9.9.25**（旧版安装包需自行寻找）。
2. 装完后立刻用 `scripts\block_update.ps1` 屏蔽更新域名（hosts），否则一升级注入就失效。
3. 验证：`C:\Program Files\Tencent\QQNT\versions\config.json` 里 `curVersion` 应为 `9.9.25-42905`。
4. 替换改造版 `QQ.exe` + `dbghelp.dll`（见liteloader官方telegram频道）。
5. 装 NapCat + LiteLoader 入口：`scripts\install_napcat_entry.ps1`。
   - 装完确认 NapCat WebUI 端口 6099 起来，token 在 `apps\NapCat\config\webui.json`（已跑路（本项目采用REA逆向（bushi）））。

> `start-all.ps1` 开头有**版本守卫**：版本不对只警告不硬拦，但注入必然失效，等于白跑。

### 步骤 2：装 AstrBot 4.29.4

1. 装 AstrBot **4.29.4** 到 `apps\AstrBot`（独立 venv）。
2. **关键**：本仓库的 `apps\AstrBot\astrbot\` 是**改过的核心源码**（含 6 处补丁），
   必须用本仓库的版本**覆盖**掉发行版里的同名目录，否则补丁全丢、功能悄悄失效。
3. 把本仓库的自研插件复制到 `apps\AstrBot\data\plugins\`：
   ```
   astrbot_plugin_peer/  astrbot_plugin_ltm/  astrbot_plugin_vision_context/
   astrbot_plugin_websearch/  astrbot_plugin_meme_manager/  ...
   ```
   （GitHub 仓里插件目录结构若与发行版不同，以发行版 `data/plugins/` 为准放置。）
4. 面板默认账号：`astrbot` / `qqbot2026`（改配置后以你的为准）。

### 步骤 3：准备模型服务

- **本地模式**：按 `D:\LLM` 原作者的环境部署 llama.cpp 路由（8080）、判官（8082）、OCR（8083）、向量（8097）。这些脚本与模型不在本仓库。
- **第三方模式**：只需在 `data/cmd_config.json` 填 DeepSeek API key，判官仍走本地 8082。

### 步骤 4：填配置（把 CHANGE_ME 换成真值）

| 文件 | 要填什么 |
|---|---|
| `data/cmd_config.json` | dashboard 密码、`provider[].api_key`（DeepSeek key）、provider 开关 |
| `apps\NapCat\config\webui.json` | NapCat WebUI token（不入库，首次运行生成） |
| `data/persona.json` / `judge.json` / `reply.json` | 人格、判官、回复策略（一般沿用模板即可） |

⚠️ 填完 key 后确认这些文件**没被 git 跟踪**：`git status` 不该出现它们。

### 步骤 5：启动

```powershell
# 一键启动（原机器上）
.\start-all.ps1
```

自动顺序：版本守卫 → 路由 → 判官 → OCR → AstrBot → QQ/NapCat → 控制台，需要扫码时弹二维码页。
停：`.\stop-all.ps1`。只重启 AstrBot（QQ 不断线）：`scripts\restart-astrbot.ps1`。

**铁律**：改 AstrBot 配置/插件/人格**绝不重启 QQ**，会要重新扫码。

---

## 3. 验证部署是否成功

部署完逐项核对：

```powershell
# 看端口监听
netstat -ano | findstr /R ":8080 :8082 :6185 :6199 :6190 :6099"
```

| 检查项 | 期望 |
|---|---|
| 面板 | 浏览器开 `http://127.0.0.1:6185`，能登录 |
| 控制台 | `http://127.0.0.1:6190` 能打开 |
| OneBot WS | 6199 已连接（AstrBot 日志显示） |
| QQ 在线 | 小号在线，群消息有反应 |
| 6 处补丁 | 跑 `scripts\verify.ps1` 全绿 |

**改完任何代码后**，也跑 `scripts\verify.ps1`——这项目踩过三次"改了没生效"的坑。

---

## 4. 常见问题

| 症状 | 原因 / 处理 |
|---|---|
| 启动后 AI 不回话 | QQNT 版本被升级了 → 重装 9.9.25，重跑注入 |
| 功能"悄悄少了几样" | AstrBot 升级冲掉 6 处补丁 → 重新覆盖 `apps\AstrBot\astrbot\`，跑 verify |
| 判官很笨 | 1.7B 二分类本就 ~85%，外面叠了规则层；属已知限制 |
| 本地模式内存爆 | 9B 吃 ~9.7GB，切第三方模式：`/切换 api 第三方` |
| 表情标记变乱码 | `&&...&&` 白名单校验问题，见 HANDOFF.md §6 待办 |
| 重启 QQ 后要扫码 | 正常，QQ 登录态不持久；尽量不要重启 QQ |

---

## 5. 场景 A：已有完整环境，只想同步代码

原机器上已经有完整环境（`D:\QQNTBOT` + `D:\LLM`），只是想把 GitHub 上的最新改动同步过来：

```powershell
cd D:\QQNTBOT
git pull
# 如果 GitHub 仓是独立的 D:\QQNTBOT-github，把需要的文件复制过去：
# 例如覆盖 astrbot 源码、插件、scripts 等
```

⚠️ 注意两个仓是**分开的**：
- `D:\QQNTBOT` = 完整保全仓（含依赖/二进制，本地，不上 GitHub）
- `D:\QQNTBOT-github` = 代码仓（本仓库，推 GitHub）

同步时要手动把代码仓的改动搬到完整环境，**别指望 git pull 自动搞定全部**。

---

## 6. 相关文档

- [README.md](../README.md) — 缺失内容清单、许可证说明
- [HANDOFF.md](HANDOFF.md) — 人工接管、Git 手册、关键事实
- [PROJECT.md](PROJECT.md) — 完整架构、6 处补丁（§14）
- [THIRD-PARTY-API.md](THIRD-PARTY-API.md) — 第三方模式与双向切换
- [LESSONS.md](LESSONS.md) — 踩坑心得，部署/改代码前值得扫一遍
