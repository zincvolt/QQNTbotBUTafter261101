# QQNT Bot

因为养鱼热大面积封杀，在大伙都跑路得差不多之后才用剩饭搭出来的一套能用的 QQ 第三方聊天机器人方案。

本地 AI 可接入 QQ 群聊/私聊的机器人。会只能主动接话，目标是混入群。友

## 这是什么

- **用真实 QQ 登录**（非官方 bot、非协议库），QQNT + NapCat 跑在本机
- **本地大模型**（9B）或第三方 DeepSeek 双模式，可热切换

## 写了一些插件

| 插件 | 用途 |
|---|---|
| [astrbot-plugin-peer](https://github.com/zincvolt/astrbot-plugin-peer) | 只能主动回复核心功能、消息后处理 |
| [astrbot-plugin-access](https://github.com/zincvolt/astrbot-plugin-access) | 权限闸门：统一斜线指令鉴权、指令权限表在线编辑、主动回复冲突仲裁（附新插件指令管理/部署双指南） |
| [astrbot-plugin-ltm](https://github.com/zincvolt/astrbot-plugin-ltm) | 长期记忆：抽取稳定事实、语义召回后注入提示词 |
| [astrbot-plugin-apimode](https://github.com/zincvolt/astrbot-plugin-apimode) | 本地 / 第三方模型热切换、token 额度、按群审查 |
| [astrbot-plugin-visionmode](https://github.com/zincvolt/astrbot-plugin-visionmode) | 读图方式切换：本地 VL / 第三方 / 关 |
| [astrbot-plugin-vision_context](https://github.com/zincvolt/astrbot-plugin-vision_context) | 群图上下文：后台给图片生成释义并缓存，并按需注入上下文 |
| [astrbot-plugin-websearch](https://github.com/zincvolt/astrbot-plugin-websearch) | 联网搜索：接本地 SearXNG，自动 + 工具两种入口 |
| [astrbot-plugin-furcon](https://github.com/zincvolt/astrbot-plugin-furcon) | 兽聚倒计时、每日运势、群统计，图片卡片输出 |
| [astrbot-plugin-repeat](https://github.com/zincvolt/astrbot-plugin-repeat) | 群聊复读机 |
| [astrbot-plugin-dice](https://github.com/zincvolt/astrbot-plugin-dice) | 桌游骰娘 |
| [astrbot-plugin-meme_manager](https://github.com/zincvolt/astrbot-plugin-meme_manager) | 表情包管理（fork 自 [anka-afk](https://github.com/anka-afk/astrbot_plugin_meme_manager)）：WebUI 图库管理、AI 智能发送、自动收集 |

> 插件都放在各自的独立仓库里（每个插件 main.py 的 metadata 描述里也带主仓库链接），本仓库只保留框架与自研适配器。装插件时把对应仓库放进 AstrBot 的 `data/plugins/` 目录即可；权限闸门 [astrbot-plugin-access](https://github.com/zincvolt/astrbot-plugin-access) 建议最先装，其余插件靠它做统一鉴权。

## 依赖的上游项目

这套方案依赖以下开源项目（链接为官方仓库）：

| 项目 | 仓库 | 在本项目中的角色 |
|---|---|---|
| AstrBot | [AstrBotDevs/AstrBot](https://github.com/AstrBotDevs/AstrBot) | 机器人框架本体 |
| NapCatQQ | [NapNeko/NapCatQQ](https://github.com/NapNeko/NapCatQQ) | QQ 协议端，跑在 QQNT 进程内（ending） |
| LiteLoaderQQNT | [LiteLoaderQQNT/LiteLoaderQQNT](https://github.com/LiteLoaderQQNT/LiteLoaderQQNT) | QQNT 插件加载器，用于注入 NapCat |
| OneBot v11 | [botuniverse/onebot-11](https://github.com/botuniverse/onebot-11) | NapCat 与 AstrBot 之间的通信协议规范 |
| SearXNG | [searxng/searxng](https://github.com/searxng/searxng) | 自建搜索后端，供 websearch 插件使用 |

## 目录结构

```
docs/                  文档（架构/维护/踩坑/指令/接管指南）
  HANDOFF.md          ← 接手先看这份：入口导航 + Git 手册 + 关键事实
  PROJECT.md          完整架构、功能、已知限制、6 处源码补丁
  LESSONS.md          Agent的踩坑心得（为什么错、怎么不犯）
scripts/               运维脚本（启停、判官、重启、验证等）
  verify.ps1          ← 改完代码跑一遍的验证脚本
dashboard/             本机控制台（FastAPI）（主要适用这个项目的n合1面板）
caption_proxy/         图片描述缓存代理
data/                  配置模板（*.json，记得替换 CHANGE_ME）
  cmd_config.json      主配置（/api_key 在这里）
  persona.json / judge.json / judge_api.json / reply.json / ...
apps/AstrBot/astrbot/  AstrBot 核心源码（含本项目 6 处补丁，见 PROJECT.md §14）
start-all.ps1          一键启动（完整环境，需配合本地依赖）
stop-all.ps1           一键停止
```

## 重要：这个仓库不是完整运行环境

本仓库只含**代码与配置模板**。下面逐项列出**没有上传的内容、原因、以及如何补齐**——不需要猜。

### A. 刻意不上传：法律 / 隐私原因（无法从本仓库补齐）

| 缺失项 | 原始位置 | 为什么没传 | 如何补齐 |
|---|---|---|---|
| NapCat 二进制与配置 | `apps/NapCat/` | 已删库跑路，自建fork | 自行获取 NapCat；WebUI token 等凭证需重新生成 |
| QQNT：改 | `_backup/`、`apps/` | 修改并注入LiteLoader，我不想吃律师函 | 自行准备 QQNT 9.9.25 客户端；注入与绕过校验的做法见 `docs/PROJECT.md` |
| LiteLoader（改QQNT） | `apps/LiteLoader/` | QQNT反代 | 自行安装 |
| 记忆 / 缓存数据库 | `data/memory.db`、`data/caption_cache.db`、AstrBot `data_v4.db` | 含真实聊天记忆与会话历史，**隐私数据** | 首次运行会自动新建空库 |
| 凭证 | `apps/NapCat/config/webui.json`（token/totp）、`data/cmd_config.json` 的 api_key 与面板密码哈希 | 不想给别人用自己的token | 配置文件中的 `CHANGE_ME`；`webui.json` 需重新生成 |

### B. 刻意不上传：可重建的体积项（有替代方案）

| 缺失项 | 原始位置 | 体积 | 如何补齐 |
|---|---|---|---|
| Python 虚拟环境 | `apps/AstrBot/.venv/` | ~419MB | 用 `requirements.txt` / `pyproject.toml` 重新 `pip install` |
| Node 依赖 | `apps/NapCat/node_modules/` | ~113MB | `pnpm install` |
| 前端构建产物 | `apps/AstrBot/data/dist/` | — | 从 AstrBot 发行版获取或重新构建 |
| 模型服务 | 独立目录 `D:\LLM`（不在本项目内） | — | 本项目只**调用**不修改它；模型服务（9B / 判官 1.7B / OCR / 本地VL / 向量）需单独部署，端口见 `docs/PROJECT.md` |

**完整可运行的快照**仅保存在原作者的本机，本仓库只提供思路喵，不是开箱即用。

### C. 版本对应关系（避免版本错配）

- QQNT 客户端：**9.9.25**（升级会导致注入失效；建议hosts屏蔽更新域名）
- AstrBot（建议版本）：**4.29.4**，基于上游 AGPL-3.0，含本项目 6 处源码补丁（见 `docs/PROJECT.md` §14，`scripts/verify.ps1` 可核对补丁是否存活）

## 接手指引

1. **想把它跑起来** → 看 [部署指引 docs/DEPLOY.md](docs/DEPLOY.md)（从零搭建 / 同步代码 / 验证清单）
2. 先读 [docs/HANDOFF.md](docs/HANDOFF.md)——建立全局认知
3. 按主题查 [docs/](docs/) 下其他文档
4. 改完代码跑 `scripts/verify.ps1` 验证（尤其 AstrBot 升级后查补丁是否还在）
5. **主动回复核心功能**：很多人把一句话拆成两三句发，判官会等这一口气说完（`burst_settle`）再判一次；这一段判过/回过后不再送判官（`burst_reuse`），但叫它名字或骂到它头上会按规则破例。回复正在生成/分段发送时开启**在途硬锁**（`inflight_lock`），连 @ 它和唤醒前缀也一并挡掉，发完（`after_message_sent`）立刻放开。字段都在 `data/judge_api.json`，控制台「判官 → 话段聚合/在途硬锁」可调，机制见 [docs/THIRD-PARTY-API.md](docs/THIRD-PARTY-API.md) §14.6、兼容性清单见 §14.7

## 部署提示

> 完整步骤见 [部署指引 docs/DEPLOY.md](docs/DEPLOY.md)，下面只是速记。

- （本地9B）主模型、判官、向量、OCR/VL 等模型服务在另一目录 `D:\LLM`，本仓库只调用不改它
- `data/cmd_config.json` 里的 `CHANGE_ME` 需替换为真实值
- AstrBot 升级会覆盖本项目的 6 处源码补丁，升级后务必跑 `verify.ps1`恢复，不建议更新

## 许可证

本仓库采用 **AGPL-3.0-or-later**（见 [LICENSE](LICENSE)）
