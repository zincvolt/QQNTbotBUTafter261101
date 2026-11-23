# astrbot_plugin_apimode — 与其他插件的接口
> 源码：`apps/AstrBot/data/plugins/astrbot_plugin_apimode/`
> 版本：1.1.3（metadata.yaml）  分类：自写

## 1. 职责一句话
在 provider 层面判断本地/第三方模式，管住第三方 token 额度与按群审查，并在模式切换时改写 AstrBot provider 配置、联动本地模型进程与识图模式。

## 2. 注册的钩子

| 钩子 | 优先级 | 触发时机 | 实际行为 |
|---|---|---|---|
| `@filter.on_llm_request()` → `budget_gate`（main.py:416-417） | 无显式 priority（非 AdapterMessageEvent，不受 access 分档影响） | LLM 请求组装时 | 仅 third_party 生效：把群号写进 ContextVar `_current_group`（main.py:423）；`save_token` 开时把 `req.contexts` 截到 `history_keep`（main.py:424-428）；全局额度或本群额度耗尽 → `event.send` + `stop_event()`（main.py:433-448）。本地模式直接 return，不写任何状态。不改 system_prompt/prompt/工具列表。 |
| `@filter.on_decorating_result()` → `review_output`（main.py:453-454） | 无 | 回复装饰阶段 | third_party + 本群 `review_groups` 开时，遍历 `result.chain[*].text`，命中 `review_words.txt` 任一词就把所有文本组件改成「这个话题我不接」（main.py:465-482）。不 stop_event，不改 prompt，不释放锁。 |
| `@filter.on_astrbot_loaded()` → `watch_provider_switch`（main.py:501-502） | 无 | AstrBot 加载完成 | 起两个后台任务：`_provider_watch()` 每 20s 比对 provider_id，本地→API 写 `vision_mode.json=third_party` 并终止 8080/8083/8085，API→本地写 `local` 并拉起脚本（main.py:570-593）；`_install_provider_counter()` 最多等 60s 拿 deepseek provider，patch 其 `text_chat`/`text_chat_stream` 统计每次调用 usage（main.py:509-559）。 |
| `@filter.event_message_type(ALL)` → `handle`（main.py:595-596） | 无显式；access 按 `_CMD_LISTENER_MODS` 分到 `CMD_BAND = maxsize-10`（access/main.py:50-54,349-350） | 每条消息；内部只看斜杠（main.py:598-609） | 管理指令 `/用量`、`/判官`、`/切换`、`/思维链`、`/本群额度`、`/额度`、`/省token`、`/审查`；每条处理完 `event.send` + `stop_event()`（main.py:613-806）。非管理员动配置指令会发拒答 + stop_event（main.py:623-627）。 |

## 3. 输入（别人给它什么）

- **事件字段**：`message_str`、`message_obj.raw_message`、`get_group_id()`、`get_sender_id()`（经 access `unified_perm` 判权，main.py:412-414）。
- **`event.get_extra` 键**：无（本文件无 get_extra/set_extra）。
- **读的配置/数据**：`data/api_mode.json`（main.py:37,79-88,124-127）、`cmd_config.json`（main.py:38,113,284,345,384,491）、`data/reply.json`（main.py:39,325-340）、`data/review_words.txt`（main.py:40,178-186，缺文件时写默认）、`data/vision_mode.json`（main.py:216,229-236）、`data/judge_api.json`（main.py:630-638，utf-8-sig）；provider 返回的 `usage`（`TokenUsage`，main.py:130-152）。
- **外部 HTTP**：无（计数走 provider 实例，不直连 API）。子进程：PowerShell 启停脚本（main.py:190-194,268-271,362-372）、psutil 查端口（main.py:197-213）。
- **其他插件直接调用**：顶层函数 `load_state/save_state/current_mode/add_tokens/set_provider_mode/set_vision_mode/tune_reply_for_mode/set_thinking/unload_local_models/start_local_models/schedule_restart` 等（main.py:79-402）。权限优先用 access 的 `unified_perm.is_admin`（main.py:50-57），access 不在时降级硬编码 `{1154487120}`（main.py:54）。这些顶层函数是否被其他插件 import：**待确认**（全仓 grep 未见外部引用）。

## 4. 输出（它给别人什么）

- **`event.set_extra` 键与值**：无。
- **改写 req**：只截断 `req.contexts`（省 token，main.py:424-428）；不改写 `req.system_prompt`、`req.prompt`、工具列表。
- **改写回复**：`result.chain[*].text` 整段替换（main.py:480-482）。
- **`stop_event`**：额度耗尽（main.py:436,447）、全部管理指令处理完（main.py:620,627,656,678,690,699,705,733,747,771,780,788,795,806）。
- **发消息**：`event.plain_result` 的用量/额度/设置回执。
- **写文件**：`api_mode.json`（main.py:91-94）、`cmd_config.json`（main.py:284-308,345-359,384-400）、`reply.json`（main.py:317-340）、`vision_mode.json`（main.py:219-237）、`judge_api.json`（main.py:630-703）、`review_words.txt` 默认词表（main.py:178-181）。
- **进程/外部副作用**：终止或拉起 8080/8083/8085（main.py:240-272）；8 秒后重启 AstrBot（main.py:362-372）；monkey-patch deepseek provider 的 `text_chat`/`text_chat_stream` 并打 `_apimode_counted` 标（main.py:556-558）。
- **面板/HTTP 接口**：无内置接口；dashboard 直接读写同一批 json（PLUGIN-COMMANDS.md:211-223）。下游消费者：`api_mode.json` → 框架判官（PROJECT.md:440）；`reply.json` → basicz（basicz/main.py:239-266,1992-2003）；`vision_mode.json` → basicz（basicz/main.py:849-864）；`cmd_config.json.provider_id` → basicz（basicz/main.py:430-461）。

## 5. 与其他插件的协作关系

| 对方 | 关系 | 契约/约定 |
|---|---|---|
| access | 权限归并 + 指令分档 | import access 的 `unified_perm.is_admin`；`handle` 被分档为 CMD_BAND；`/切换`、`/额度`、`/审查`、`/判官` 等在 access 权限表里默认 admin（access/main.py:109-111）。 |
| basicz | 文件耦合，无 import | apimode 写 reply.json / cmd_config.json / vision_mode.json，basicz 读；两边都独立以 `provider_id` 含 `deepseek` 判第三方模式（basicz/main.py:430-461）。 |
| visionmode | 写入其状态文件 | `set_vision_mode()` 写 `data/vision_mode.json` 的 mode/port/model（main.py:219-237）；visionmode 侧读取点**待确认**（本任务未读其源码）。 |
| 框架判官 group_chat_context | 额度联动 | PROJECT.md:440 记载判官读 `api_mode.json` 今日用量，主对话额度耗尽时短路；该逻辑在本仓 core 补丁里，不在本插件源码中。 |
| meme_manager | 间接受影响 | `tune_reply_for_mode()` 把 reply.json 的 `meme_chance` 设 0 或 0.3（main.py:328-339）；meme_manager 是否读该键**待确认**。 |

## 6. 配置与数据文件

| 路径 | 用途 | 谁写 | 谁读 |
|---|---|---|---|
| `data/api_mode.json` | 模式记账 / 全局与分群额度 / 用量 / 审查群 | apimode（`/切换`、`/额度`、`/本群额度`、`/审查` + provider 计数） | apimode、dashboard、框架判官 |
| `cmd_config.json` | provider 启用位与 `agent_runner.provider_id`（模式真相） | WebUI 或 `/切换`、`/思维链` | apimode、basicz、AstrBot 本体 |
| `data/reply.json` | dual_judge / thinking / meme_chance / text_rules | apimode 切换时、dashboard | basicz、框架判官 |
| `data/review_words.txt` | 审查词表（默认词见 main.py:72-76） | 人工；apimode 缺文件时写默认 | `apimode.review_words()` |
| `data/vision_mode.json` | 识图 mode / port / model | apimode、visionmode、dashboard | basicz、visionmode |
| `data/judge_api.json` | 第三方判官配置与用量 | apimode `/判官`、dashboard | 框架判官、apimode `/判官 状态` |

## 7. 顺序、坑与边界

- 模式真相是 `agent_runner.config.model.provider_id` 是否含 `deepseek`，`api_mode.json.mode` 仅兜底（main.py:102-127）；WebUI 改 provider 后记账文件会过期，靠这个避免额度闸/审查静默失效。
- BOM：`cmd_config.json` / `judge_api.json` 用 `utf-8-sig`（main.py:113,491,633），`api_mode.json` 用 `utf-8`（main.py:83,125）。
- 计数挂在 provider 的 `text_chat`/`text_chat_stream`，而非 `on_llm_response`——后者漏计工具循环中间调用（main.py:450-451,509-517）；`_apimode_counted` 防重载重复包装（main.py:533-534）；只统计 `is_chunk=False` 的帧（main.py:564-568）。
- 静默失败：拿不到 deepseek provider 只打 warning、计数不安装（main.py:530-532）；计数异常只 warning 不影响聊天（main.py:543-544,551-553）；provider watch 异常只 warning（main.py:592-593）。
- `/切换` 写完配置 8 秒后重启（main.py:362-372,721,732）；重启窗口里改配置会被覆盖（THIRD-PARTY-API.md:436）。
- 省 token 截断 `req.contexts` 只在 `save_token` 开时生效（main.py:424-428）；`history_keep` 由 dashboard 写（THIRD-PARTY-API.md:300-301）。
- 卸载本地模型后 DeepSeek 报错无本地 fallback（THIRD-PARTY-API.md:341）。
- 本插件不通过 event extra 传递模式；跨插件只能读上述配置文件或调用顶层函数。

## 8. 代码依据
`main.py:36-47`（路径与 ContextVar）、`main.py:49-57`（权限降级）、`main.py:79-127`（状态与模式判定）、`main.py:130-186`（计数与词表）、`main.py:189-272`（进程控制）、`main.py:275-402`（配置改写函数）、`main.py:412-448`（budget_gate）、`main.py:453-482`（review_output）、`main.py:501-568`（watch 与计数安装）、`main.py:570-806`（provider 守护与指令处理）。
