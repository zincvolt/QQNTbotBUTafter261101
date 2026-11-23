# astrbot_plugin_creator — 与其他插件的接口
> 源码：`apps/AstrBot/data/plugins/astrbot_plugin_creator/`
> 版本：1.0.0（metadata.yaml）  分类：自写

## 1. 职责一句话
创造者专属通道：给创造者私聊注入身份提示并向 LLM 暴露 `tell_creator` 私信工具，后台另跑日志报错监控、端口健康探测、好感度维护与主动搭话/每日摘要，所有对外消息都是发给创造者的 QQ 私聊，不参与普通群聊。

## 2. 注册的钩子

| 钩子 | 优先级 | 触发时机 | 实际行为 |
|---|---|---|---|
| `@filter.on_llm_request()` → `inject_identity`（main.py:306-320） | 无显式 priority | LLM 请求组装；仅私聊且发送者 = creator_id | 只改 `req.system_prompt`，追加一段身份提示并告知可用 `tell_creator`（main.py:314-318）；群里或非创造者立即 return；不 stop_event、不改工具列表。 |
| `@filter.llm_tool(name="tell_creator")` → `tell_creator`（main.py:323-353） | 不适用 | LLM 主动调用工具时 | 注册名为 `tell_creator` 的工具，参数 `content: string`；读冷却/日限后经 aiocqhttp `send_private_msg` 私信创造者；返回状态字符串给 LLM（339/341/344/349/350/353），异常也返回字符串不抛出。 |
| `@filter.event_message_type(EventMessageType.ALL, priority=-100)` → `_on_message`（main.py:404-440） | 源码 `-100`；运行时被 access 的 `_enforce_bands` 改写为 `LISTENER_BAND = maxsize-100`（access/main.py:316-361） | 每条适配器消息 | 先拦好友申请（356-401）；群消息只计 `group_msgs`；私聊计 `private_msgs`、涨好感度（默认 +0.5/条，上限 100）、更新 `last_seen`/`msgs`、维护 30 条上下文窗口（411-437）。不 stop_event 普通消息、不发消息。 |
| `@filter.on_decorating_result()` → `_on_reply`（main.py:442-462） | 无显式 priority | 回复装饰阶段 | 仅私聊且该 uid 已在 `windows` 中时，把 bot 回复以 `role="bot"` 追加进窗口（截 200 字、最多 30 条，451-460）；不改 `result.chain`、不 stop_event。 |
| `@filter.command("好感度")` → `affection_cmd`（main.py:465-492） | 无显式 priority；运行时被 access 归到 `CMD_BAND = maxsize-10`（access/main.py:45-46,341-355） | `/好感度`、`/好感度 列表` | `列表` 分支要求 access `is_admin`（469），按分数排序输出 uid 与创造者标记；个人分支输出分数与档位；`yield plain_result`，不 stop_event。 |
| `@filter.on_astrbot_loaded()` → `_start`（main.py:857-870） | — | AstrBot 加载完成 | `_started` 防重入后起 4 个后台任务：日志循环（563-600）、健康探测（615-647）、主动搭话（692-714）、每日调度（829-854）。 |

## 3. 输入（别人给它什么）

- **事件字段**：`get_group_id()`（306-311,413）、`get_sender_id()`（312,412,448,482）、`get_sender_name()`（未用，主动搭话用 `windows` 文本）、`message_str`（411,467）、`message_obj.raw_message` dict（364-372，好友申请取 `post_type`/`request_type`/`flag`/`user_id`/`comment`）、`event.get_result()` → `result.chain` / `get_plain_text()`（451-454）、`event.role`（降级 admin 判定时使用，main.py:94）。
- **`event.get_extra` 键**：无（全文件无 `get_extra`）。
- **读的配置文件/数据库**：`creator_data.json`（31,124-132；含 `affection`/`windows`/`sent_log`/`stats`/`error_seen`/`warn_seen`/`health_state`/`pending_alerts`）；`D:\QQNTBOT\data\affection_edit.json`（34,46-61，utf-8-sig，mtime 缓存，面板手调值优先）；`data/persona.json`（35,669-674，只取 `text` 用于搭话/情绪评估的 system）；`apps/AstrBot/data/cmd_config.json`（36,135-165,603-613；取 `agent_runner.config.model.provider_id` → provider / api_base / key / model 及探测端口）；`context.get_config()['platform_settings']['id_whitelist']`（234-244，只认含 `FriendMessage` 的条目，60s 缓存）；`apps/AstrBot/data/logs/astrbot.log`（37,563-600，从当前末尾读新行）；`astrbot_plugin_access/unified_perm.py`（86-94 import `is_admin`）。
- **外部 HTTP**：`POST {api_base}/chat/completions`（650-667，直连当前 provider，temperature 0.8；解析失败回退 `FALLBACK_LLM = 127.0.0.1:8080`，39）；TCP connect 探活 127.0.0.1 端口（621-627，本地 8080/8082/8083/8085/8097/9000，第三方 8082/8097/9000）。
- **其他插件直接调用**：全仓 grep 未见任何插件 import 本插件的符号（`tell_creator`/`creator_data`/`affection_edit` 仅本文件出现）；下游只有 LLM（工具）、创造者（私聊）与 dashboard（读数据文件）。

## 4. 输出（它给别人什么）

- **`event.set_extra` 键与值**：无。
- **LLM 工具**：名称 `tell_creator`（323）；参数 `content: string`（324-331 docstring）；返回 4 类字符串——冷却中（339）、日限已满（341）、空内容（344）、发送成功（349）/通道不可用（350）/异常（353）。下游消费者：主模型，把返回当工具观察继续生成。
- **改写 prompt**：仅私聊创造者时给 `req.system_prompt` 追加身份提示（314-318）；不改 `req.prompt` / `req.image_urls` / 工具列表。
- **`stop_event`**：仅好友申请分支（398）；注意白名单内、外都会 stop_event。普通消息与指令分支均不 stop_event。
- **发消息**：aiocqhttp `bot.call_action("send_private_msg", user_id=int(uid), message=text)`（266-277）——承载吐槽、报错/关键 WARN 报警、端口挂/恢复、主动搭话、排队报警（295-303）、每日摘要（793-827）；每小时上限 6 条，超出的 `bump("suppressed")` 进日报（283-287）。下游消费者：创造者 QQ。
- **写文件**：`creator_data.json`（`_save()` 200-204，全量覆盖；触发点见 tell_creator 348、好友申请 390、日志循环 592-594、健康循环 641、主动搭话 736、每日任务与调度 755/791/827/848）；**不写** `affection_edit.json`（只读）。
- **面板/HTTP 接口**：无自建 HTTP 端点；控制台「好感度」页由外部 dashboard 写 `affection_edit.json`，本插件按 mtime 读（42-61）。`DECLARED_COMMANDS`（97-100）与 `DECLARED_BEHAVIOR`（102-108）供 access 的 `/权限 列表` 做 ast 扫描展示。

## 5. 与其他插件的协作关系

| 对方 | 关系 | 契约/约定 |
|---|---|---|
| access | 单向 import + 名单/权限共享 | `from unified_perm import is_admin`（86-88）；单拎时降级本地 `{"1154487120"}`（90-94）；候选名单 = access `/私聊` 白名单里含 `FriendMessage` 的条目 ∪ 创造者（227-253）；access `_enforce_bands` 把本插件消息监听覆盖到 `maxsize-100`（access/main.py:341-355）。 |
| dashboard（非插件） | 文件单向写入 | 面板写 `data/affection_edit.json`，本插件按 mtime 读并优先于自然涨落（258-261）；刻意不落回主数据，避免并发写把面板改动冲掉（32-34）。 |
| basicZ / 判官 / 复读机 | 钩子顺序 | 消息监听名义 `priority=-100` 但运行时被 access 改写为 LISTENER_BAND，因此统计/好感度更新在指令档之后；普通消息不 stop_event，不抢指令。 |
| 主模型（LLM） | 工具与 prompt 双向 | 暴露 `tell_creator` 工具；私聊创造者时改 system_prompt 告知可用工具（314-318）；工具返回状态串被 LLM 当观察继续生成。 |

## 6. 配置与数据文件

| 路径 | 用途 | 谁写 | 谁读 |
|---|---|---|---|
| `astrbot_plugin_creator/creator_data.json` | affection / windows / sent_log / stats / error_seen / warn_seen / health_state / pending_alerts | creator `_save()` | creator `_load_data()` |
| `D:\QQNTBOT\data\affection_edit.json` | 面板手调 uid → score | dashboard「好感度」页 | creator `_load_affection_edits()`（mtime 缓存，utf-8-sig） |
| `D:\QQNTBOT\data\persona.json` | 搭话/情绪评估的 system 文本（不复述内容） | dashboard、basicZ | creator `_persona()`（只取 `text`） |
| `apps/AstrBot/data/cmd_config.json` | provider_id、api_base/key/model、id_whitelist、admins_id | WebUI、access | creator `_resolve_llm` / `_probe_ports` / `_sync_whitelist` |
| `apps/AstrBot/data/logs/astrbot.log` | ERRO / 关键 WARN 行源 | AstrBot 与各插件 | creator `_log_loop()` |
| `astrbot_plugin_access/unified_perm.py` | `is_admin` 统一判定 | access | creator 顶层 import |
| `astrbot_plugin_creator/_conf_schema.json` | 冷却/上限/时段/概率默认值 | 随插件发布 | WebUI 载入为 `self.cfg` |

## 7. 顺序、坑与边界
- `priority=-100` 是名义值：access `_enforce_bands` 会把所有 AdapterMessageEvent handler 改写成 `LISTENER_BAND = maxsize-100`（access/main.py:341-355）；效果仍是"最后统计"，但原因不是源码里那个 -100。
- 工具名冲突：全仓仅 creator 注册 `tell_creator`（grep 验证）；若将来别的插件注册同名工具，AstrBot 的取舍行为**待确认**。
- 好友申请被 AstrBot 伪装成空私聊消息送进来（356-361），故 `_on_message` 第一件事就拦；命中即 stop_event，其他想监听空私聊的插件会拿不到——**待确认**是否有这种消费者。
- 限流/冷却：吐槽 60min + 每日 5 条（334-341，按 86400s 滚动）；报警每小时 6 条（283-287）；同签名报错首次即报、4h 后仍在再报（537-543）；关键 WARN 4h 节流（555-556）；主动搭话 6h 最小间隔 / 每日 3 条 / 2h 内聊过跳过 / 仅活跃时段（677-690）；安静时段报警排队，队列上限 50（290-293）。
- 配置合并写入语义：`_save()` 是**全量覆盖** `creator_data.json`（200-204），面板手调值因此单独放 `affection_edit.json`（32-34）；`_load_data()` 用默认值合并 raw（124-132），可容忍缺键。
- BOM：`affection_edit.json` / `cmd_config.json` 用 `utf-8-sig`（56,145）；`creator_data.json` 用 `utf-8`（126,203）。
- 主动搭话/日报是插件主动私聊，不走 event 链；日报发出后把 `error_seen`/`warn_seen` 的 count 清零（822-826）。
- `_llm_chat` 直连 provider（650-667），与 AstrBot 主模型不同路；provider 切换靠 `cmd_config.json` mtime 自动更新（135-165）；`terminate()` 只 cancel 任务并 `_save()`（872-876）。

## 8. 代码依据
`main.py:30-43`（路径/常量/缓存）、`main.py:46-61`（面板手调读取）、`main.py:85-108`（access import 与声明）、`main.py:111-165`（默认数据与 LLM 解析）、`main.py:227-263`（白名单/好感度）、`main.py:266-303`（发送通道与报警限流）、`main.py:306-320`（身份注入）、`main.py:323-353`（tell_creator）、`main.py:356-401`（好友申请）、`main.py:404-440`（消息监听）、`main.py:442-462`（回复窗口）、`main.py:465-492`（指令）、`main.py:495-600`（日志监控）、`main.py:603-647`（健康探测）、`main.py:650-674`（LLM/人设）、`main.py:677-739`（主动搭话）、`main.py:742-854`（每日任务/调度）、`main.py:857-876`（启停）；`_conf_schema.json:1-83`；`metadata.yaml:4`；`access/main.py:316-361`（priority 覆盖）。
