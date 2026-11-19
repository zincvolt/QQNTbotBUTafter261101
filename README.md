# QQNT Bot

因为养鱼热封杀在大伙都跑路得差不多之后才用剩饭搭出来的一套能用的 QQ 第三方聊天机器人方案。

本地 AI 接入 QQ 群聊/私聊的机器人。人格「阿灰」——一个嘴损、爱聊猎奇和游戏的奶牛猫兽人，尝试混入群友

## 这是什么

- **用真实 QQ 登录**（非官方 bot、非协议库），QQNT + NapCat 跑在本机
- **本地大模型**（9B）或第三方 DeepSeek 双模式，可热切换
- 有判官模型决定"该不该接这句话"、长期记忆、读图、发表情包、联网搜索、兽聚倒计时等指令
- 设计取向：**宁可少说、装死，也不刷屏、不编事实**

## 目录结构

```
docs/                  文档（架构/维护/踩坑/指令/接管指南）
  HANDOFF.md          ← 接手先看这份：入口导航 + Git 手册 + 关键事实
  PROJECT.md          完整架构、功能、已知限制、6 处源码补丁
  LESSONS.md          踩坑心得（为什么错、怎么不犯）
scripts/               运维脚本（启停、判官、重启、验证等）
  verify.ps1          ← 改完代码跑一遍的验证脚本
dashboard/             本机控制台（FastAPI）
caption_proxy/         图片描述缓存代理
data/                  配置模板（*.json，敏感值已脱敏为 CHANGE_ME）
  cmd_config.json      主配置（密码/api_key 需自行填写）
  persona.json / judge.json / reply.json / ...
apps/AstrBot/astrbot/  AstrBot 核心源码（含本项目 6 处补丁，见 PROJECT.md §14）
start-all.ps1          一键启动（完整环境，需配合本地依赖）
stop-all.ps1           一键停止
```

## 重要：这个仓库不是完整运行环境（缺什么一目了然）

本仓库只含**代码与配置模板**。下面逐项列出**没有上传的内容、原因、以及如何补齐**——不需要猜。

### A. 刻意不上传：法律 / 隐私原因（无法从本仓库补齐）

| 缺失项 | 原始位置 | 为什么没传 | 如何补齐 |
|---|---|---|---|
| NapCat 二进制与配置 | `apps/NapCat/` | 已删库跑路的 fork | 自行获取 NapCat；WebUI token 等凭证需重新生成 |
| QQNT、改 | `_backup/`、`apps/` | 修改并注入LiteLoader，我不想吃律师函 | 自行准备 QQNT 9.9.25 客户端；注入与绕过校验的做法见 `docs/PROJECT.md` |
| LiteLoader（改QQNT） | `apps/LiteLoader/` | QQNT反代 | 自行安装 |
| 记忆 / 缓存数据库 | `data/memory.db`、`data/caption_cache.db`、AstrBot `data_v4.db` | 含真实聊天记忆与会话历史，**隐私数据** | 首次运行会自动新建空库 |
| 真实凭证 | `apps/NapCat/config/webui.json`（token/totp）、`data/cmd_config.json` 的 api_key 与面板密码哈希 | 不想给别人用自己的token | 配置文件中已脱敏为 `CHANGE_ME`，填入你自己的值；`webui.json` 需重新生成 |

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
2. 先读 [docs/HANDOFF.md](docs/HANDOFF.md)——5 分钟建立全局认知
3. 按主题查 [docs/](docs/) 下其他文档
4. 改完代码跑 `scripts/verify.ps1` 验证（尤其 AstrBot 升级后查补丁是否还在）

## 部署提示

> 完整步骤见 [部署指引 docs/DEPLOY.md](docs/DEPLOY.md)，下面只是速记。

- （本地9B）主模型、判官、向量、OCR/VL 等模型服务在另一目录 `D:\LLM`，本仓库只调用不改它
- `data/cmd_config.json` 里的 `CHANGE_ME` 需替换为真实值
- AstrBot 升级会覆盖本项目的 6 处源码补丁，升级后务必跑 `verify.ps1`恢复，不建议更新

## 许可证

本仓库采用 **AGPL-3.0-or-later**（见 [LICENSE](LICENSE)），与所依赖的 AstrBot 上游一致。
