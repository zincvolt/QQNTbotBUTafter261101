# 一个屎山QQ聊天机器人
> 这个仓库不是完整运行环境

目标：让大肥鱼像群友一样混进群聊
本项目是在遗留生态上继续长出的一整套拟人聊天系统。

### 亮点：
- **判官机制**：群里每句话先过一个 1.7B 小模型作为判官，从而决定要不要接话。配套：话段聚合、在途硬锁、"未知全貌不随意发言"。看不懂会打 `?` 追上下文（选择性追问）
- **本地优先 + 双模式热切换**：9B 主模型 + 1.7B 判官 + 本地 VL 读图 + OCR + 向量库全本地；可一键切第三方 LLM（本项目使用DeepSeek）
- **token节约**：全局 + 分群额度闸；额度耗尽时判官自动跳过。图片以及表情包仅在首次出现时识别，之后由插件注入语义
- **记忆**：LLM自动总结长期记忆并归类，按 TTL 自动过期并归档清理，语义召回（按需注入）

## 和其他 QQ 机器人有什么不一样：
| 类型 | 代表 | 用途 | 差在哪 |
|---|---|---|---|
| **协议端** | NapCat、Lagrange.Core、LLOneBot、go-cqhttp | 把 QQ 消息收发打通，是"管道" | 不含聊天智能 |
| **通用框架** | AstrBot、NoneBot2、Koishi | 事件系统 + 插件生态 | 接入LLM后是"有问必答"、没有"沉默"这个概念 |

本项目 = **通用框架（AstrBot）+ 一套"会沉默"的插件**。解决了**"这句话到底该不该回、什么时候回、应不应该沉默"**的问题。

## 一些插件简介：
| 插件 | 用途 |
|---|---|
| [astrbot-plugin-basicz](https://github.com/zincvolt/astrbot-plugin-basicz) | 群聊基础行为 |
| [astrbot-plugin-private-settle](https://github.com/zincvolt/astrbot-plugin-private-settle) | 私聊话段合并 |
| [astrbot-plugin-access](https://github.com/zincvolt/astrbot-plugin-access) | 防冲突与权限管理 |
| [astrbot-plugin-ltm](https://github.com/zincvolt/astrbot-plugin-ltm) | 长期记忆 |
| [astrbot-plugin-apimode](https://github.com/zincvolt/astrbot-plugin-apimode) | 本地 / 第三方模型切换 |
| [astrbot-plugin-visionmode](https://github.com/zincvolt/astrbot-plugin-visionmode) | 读图方式切换 |
| [astrbot-plugin-vision_context](https://github.com/zincvolt/astrbot-plugin-vision_context) | 识图优化 |
| [astrbot-plugin-websearch](https://github.com/zincvolt/astrbot-plugin-websearch) | 联网搜索 |
| [astrbot-plugin-furcon](https://github.com/zincvolt/astrbot-plugin-furcon) | 兽聚功能、每日运势、群统计 |
| [astrbot-plugin-repeat](https://github.com/zincvolt/astrbot-plugin-repeat) | 复读机 |
| [astrbot-plugin-dice](https://github.com/zincvolt/astrbot-plugin-dice) | 桌游骰娘 |

> 本仓库只保留框架与适配。装插件时把对应仓库放进 AstrBot 的 `data/plugins/` 目录即可；权限闸门 [astrbot-plugin-access](https://github.com/zincvolt/astrbot-plugin-access) 建议先装，其余插件靠它做统一鉴权以及防止指令冲突。

## 依赖的上游项目
| 项目 | 仓库 | 在本项目中的角色 |
|---|---|---|
| AstrBot | [AstrBotDevs/AstrBot](https://github.com/AstrBotDevs/AstrBot) | 机器人框架本体 |
| NapCatQQ | [NapNeko/NapCatQQ](https://github.com/NapNeko/NapCatQQ) | QQ 协议端，跑在 QQNT 进程内（官方已标注 ending） |
| LiteLoaderQQNT | [LiteLoaderQQNT/LiteLoaderQQNT](https://github.com/LiteLoaderQQNT/LiteLoaderQQNT) | QQNT 插件加载器，用于注入 NapCat |
| OneBot v11 | [botuniverse/onebot-11](https://github.com/botuniverse/onebot-11) | NapCat 与 AstrBot 之间的通信协议规范 |
| SearXNG | [searxng/searxng](https://github.com/searxng/searxng) | 自建搜索后端，供 websearch 插件使用 |


## 部署提示
> 完整步骤见 [部署指引 docs/DEPLOY.md](docs/DEPLOY.md)
- 部分能力依赖的模型需要自己部署并接入（如向量化、stt、tts等）
- `data/cmd_config.json` 里的 `CHANGE_ME` 需替换
- AstrBot 升级会覆盖本项目的 6 处源码补丁，升级后务必跑 `verify.ps1`恢复，不建议更新


## 你需要补全的：
### A. 无法从本仓库补齐的部分：法律 / 隐私原因
| 缺失项 | 原始位置 | 描述 | 如何补齐 |
|---|---|---|---|
| NapCat 二进制与配置 | `apps/NapCat/` | 已删库跑路，自建fork | 自行获取 NapCat 以及 WebUI token 等凭证 |
| LiteLoader（改QQNT） | `apps/LiteLoader/` | QQNT注入 | 自行安装 |

### B. 环境依赖
| 缺失项 | 原始位置 | 体积 | 如何补齐 |
|---|---|---|---|
| Python 虚拟环境 | `apps/AstrBot/.venv/` | ~419MB | 根据 `requirements.txt` / `pyproject.toml` 重新 `pip install` |
| Node 依赖 | `apps/NapCat/node_modules/` | ~113MB | `pnpm install` |
| 前端构建产物 | `apps/AstrBot/data/dist/` | — | 从 AstrBot 发行版获取或重新构建 |
| 本地模型服务 | （不在本项目内） | — | 模型服务（9B / 判官 1.7B / OCR / 本地VL / 向量 / 语音识别 Whisper 8096）需单独部署，SearXNG 跑在 Docker（9000），端口见 `docs/PROJECT.md`。`start-all.ps1` 会拉起前两类 |

### C. 建议版本：
- QQNT 客户端：**9.9.25**
- AstrBot（建议版本）：**4.29.4**，含本项目 6 处源码补丁（见 `docs/PROJECT.md` §14，`scripts/verify.ps1` 可核对补丁是否存活）


## 你可能需要的：
1. **想把它跑起来** → 看 [部署指引 docs/DEPLOY.md](docs/DEPLOY.md)（从零搭建 / 同步代码 / 验证清单）
2. 先读 [docs/HANDOFF.md](docs/HANDOFF.md) —— 可以大概了解一下这些屎山插件
3. 按主题查 [docs/](docs/) 下其他文档
4. 改完代码跑 `scripts/verify.ps1` 验证（尤其 AstrBot 升级后查补丁是否还在）
5. **判官有两套互不干扰的配置**：本地模式用 `data/judge.json` + 8082；第三方模式用 `data/judge_api.json` + API，按主模型 provider 自动切换，细节见 [docs/THIRD-PARTY-API.md](docs/THIRD-PARTY-API.md) §14
6. **话段聚合与省 token**：很多人把一句话拆成两三句发，判官会等这一口气说完（`burst_settle`）再判一次；这一段判过/回过后不再送判官（`burst_reuse`），但叫它名字或骂到它头上会按规则破例。回复正在生成/分段发送时开启**在途硬锁**（`inflight_lock`），收到（`after_message_sent` “我说完了”标记）才会放开。字段都在 `data/judge_api.json`，机制见 [docs/THIRD-PARTY-API.md](docs/THIRD-PARTY-API.md) §14.6、兼容性清单见 §14.7
7. **私聊连发**由独立插件把几条**合并成一条用户消息**再回一次；私聊表情的发送默认交给模型判断，见 [docs/PRIVATE-CHAT.md](docs/PRIVATE-CHAT.md)
8. **查某个插件注册了哪些钩子、往外交什么数据、和谁耦合** → [docs/plugins/](docs/plugins/)


## 目录结构
```
docs/                  文档
  HANDOFF.md          ← 维护看这份：入口导航 + Git 手册 + 关键事实
  PROJECT.md          完整架构、功能、已知限制、6 处源码补丁
  LESSONS.md          AI的踩坑心得（方便继续vibecoding）
scripts/               运维脚本
  verify.ps1          ← 改完代码用的验证脚本
dashboard/             统一入口控制台（FastAPI）
caption_proxy/         图片描述缓存代理
data/                  配置模板（*.json）
  cmd_config.json      主配置
  persona.json / judge.json / judge_api.json / reply.json / ...
apps/AstrBot/astrbot/  AstrBot 核心源码（含本项目 6 处补丁，见 PROJECT.md §14）
start-all.ps1          一键启动（需配合本地依赖）
stop-all.ps1           一键停止
```


本仓库采用 **AGPL-3.0-or-later**
