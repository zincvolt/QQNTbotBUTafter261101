# QQNT Bot

本地 AI 接入 QQ 群聊/私聊的机器人。人格「阿灰」——一个嘴损、爱聊猎奇和游戏的狼人兽人，像群友一样聊天，而不是像客服。

## 这是什么

- **用真实 QQ 小号登录**（非官方 bot、非协议库），QQNT + NapCat 跑在本机
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

## 重要：这个仓库不是完整运行环境

本仓库只含**代码与配置模板**，为了安全和体积，刻意不包含：

- QQNT / NapCat 二进制（含改造版 QQ.exe，侵权风险）
- Python 虚拟环境、Node 依赖、运行时（约 1.4GB，可重装）
- 数据库（记忆、会话历史——隐私数据）
- 真实凭证（WebUI token、API key、面板密码）

**完整可运行的快照**保存在本机 `D:\QQNTBOT`（含全部依赖与二进制），不在 GitHub。

## 接手指引

1. 先读 [docs/HANDOFF.md](docs/HANDOFF.md)——5 分钟建立全局认知
2. 按主题查 [docs/](docs/) 下其他文档
3. 改完代码跑 `scripts/verify.ps1` 验证（尤其 AstrBot 升级后查补丁是否还在）

## 部署提示

- 主模型、判官、向量、OCR/VL 等模型服务在另一目录 `D:\LLM`，本仓库只调用不改它
- `data/cmd_config.json` 里的 `CHANGE_ME` 需替换为真实值
- AstrBot 升级会覆盖本项目的 6 处源码补丁，升级后务必跑 `verify.ps1`
