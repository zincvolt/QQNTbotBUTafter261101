# astrbot_plugin_ltm — 与其他插件的接口
> 源码：`apps/AstrBot/data/plugins/astrbot_plugin_ltm/`
> 版本：1.2.3（metadata.yaml）  分类：自写

## 1. 职责一句话
把对话和群历史里稳定成立的事实抽成 `facts` 行，按当前消息召回后追加到 `req.system_prompt`，并提供 `/记忆`、`/忘记` 与后台去重/过期清理。

## 2. 注册的钩子

| 钩子 | 优先级 | 触发时机 | 实际行为 |
|---|---|---|---|
| `@filter.on_llm_request()` `inject_memory`（`main.py:990`） | 未声明，默认 0；与 basicZ/vision_context/websearch 同档，同档顺序**待确认** | 每次 LLM 请求组装时 | 只**追加** `req.system_prompt`，不改 `req.prompt`；不 `stop_event`；无 `event.set_extra` |
| `@filter.on_llm_response()` `learn_from_turn`（`main.py:1031`） | 未声明，默认 0 | LLM 回复后 | 群聊（有 `get_group_id()`）直接 return；仅私聊且正文 ≥4 字，`extract_cooldown`（默认 900s）过了才 `asyncio.create_task(_extract(uid, said, "chat"))` |
| `@filter.on_astrbot_loaded()` `start_scanner`（`main.py:1103`） | 未声明，默认 0 | AstrBot 加载完成 | 启动两个后台 task：`_scan_loop`（群历史攒批抽取）与 `_dedup_loop`（启动 2h 后首跑，每 24h 过期+清理+去重） |
| `@filter.command("记忆")` `show_memory`（`main.py:1425`） | 默认；权限由 access CMD_BAND 闸门先判 | 斜杠指令 | 列本人最近 20 条；`去重`/`清理` 子命令需 `_is_admin(event)`，会直接跑 `_dedup_once` / `_expire_once` + `_purge_expired`，并 `yield event.plain_result(...)` |
| `@filter.command("忘记")` `forget`（`main.py:1476`） | 默认 | 斜杠指令 | 按 uid 删 `facts`（可带 `text LIKE %keyword%`），`yield event.plain_result("忘掉了 N 条。")` |

> 副作用口径：改 prompt = 是（仅 system_prompt）；写历史 = 是（写的是自己的 `facts`，不改 AstrBot 对话历史）；`stop_event` = 否；发消息 = 仅两条指令。

## 3. 输入（别人给它什么）

**事件字段**：`event.get_sender_id()` → 回落 `event.get_session_id()` 当 uid（`main.py:999,1042,1455,1479`）；`event.message_str` 作召回 query 与抽取原文（`main.py:1002,1048`）；`event.get_group_id()` 判群聊（`main.py:1046`）；指令参数 `arg` / `keyword`（`main.py:1426,1477`）。

**`event.get_extra` 键**：无。源码未出现 `event.get_extra(...)` 调用，不消费其他插件写入的 extra 键（**待确认**：框架是否把判官标记透传给本插件——未发现代码路径）。

**读的配置文件 / 数据库表**：
- `data/ltm.json`：`load_settings()`（`main.py:356`），`utf-8-sig` + mtime 缓存，缺字段用 `DEFAULT_SETTINGS`（`main.py:167`）。
- `data/ltm_prompt.txt`：`load_prompt()`（`main.py:381`），`utf-8`，乱码自动还原、缺 `{lines}` 回落内置。
- `data/ltm_usage.json`：`_load_usage()`（`main.py:77`），`utf-8-sig`，`date/tokens/daily_limit/enabled`。
- `data/memory.db` 的 `facts` 表：`uid,text,emb,created,used,hits,slot,value,source,superseded_by,conf`（`main.py:499-520`）。
- `apps/AstrBot/data/data_v4.db` 的 `platform_message_history`：只读（`mode=ro`），取 `id > _last_hist_id`，只留 `GroupMessage` 且 `data.type != "bot"`（`main.py:1064-1101`）。
- `apps/AstrBot/data/cmd_config.json`：`provider_id → provider → provider_sources` 解析 `api_base/key/model`（`main.py:272-320`）；含 `deepseek` 即判第三方（`main.py:1338`）。
- `data/api_mode.json`：`mode == "third_party"` 作模式兜底（`main.py:1352`）。
- 环境变量：`QQNTBOT_ROOT`、`QQNTBOT_DATA`、`LTM_BOT_DB`、`LTM_CMD_CONFIG`、`LTM_PROMPT`、`LTM_EMB_BASE`、`LTM_EMB_MODEL`（`main.py:45,143,151,187,265`）。

**外部服务**：本地向量 `/embeddings`（默认 `127.0.0.1:8097`，`main.py:533`）；LLM `POST {base}/chat/completions`（cmd_config 的 provider 或 `FALLBACK_LLM` `127.0.0.1:8080`，`main.py:185,548`）；第三方直连吃 `ltm_usage.json` 日额度闸（`main.py:99,558`）。

**其他插件直接调用**：无公开 API，外部只能经钩子或改数据文件间接使用；`access` 是唯一的跨插件 import：`sys.path.insert(0, .../astrbot_plugin_access)` 后 `from unified_perm import is_admin`（`main.py:124-132`）。

## 4. 输出（它给别人什么）

**`event.set_extra` 键与值**：无。

**改写 `req.system_prompt` / `req.prompt`**：追加 `"\n\n[你长期记得的关于对方的事，自然地用，不要逐条复述]\n" + block`（`main.py:1019`）；最多 4 条、单行 60 字截断、整块 600 字预算（`main.py:190-194,1007-1016`）。`req.prompt` 不改。`activity`/`habit` 注入时自动带「今天/昨天/N天前…」时间标签（`main.py:212-213,617-621`）。

**注入上下文内容**：即上面那段系统提示词块，供主模型自然使用；**下游消费者** = 主模型（8080 provider / 第三方），以及读取 system_prompt 的 basicZ `log_system_prompt`（`basicz/main.py:1777`，只读日志，不改内容）。

**`stop_event`**：无。

**发消息**：`/记忆` 列表与去重/清理结果、`/忘记` 删除条数，均为 `event.plain_result`（`main.py:1430-1493`）。

**写数据库 / 文件**：`facts` 行 `INSERT`、旧值 `UPDATE superseded_by = 新id`（单值槽位顶替 / 合并），过期或 FIFO 超限写 `superseded_by = -1`，超 `MAX_FACTS_PER_USER=300` 与过期清理会 `DELETE`（`main.py:940-981,1162-1166,1192-1209,1313-1318`）；删除前整行 JSONL 追加到 `data/ltm_purged.jsonl`（`main.py:426-445,1197`）；`ltm_usage.json` 累加 `tokens`（`main.py:109-120`）。

**面板接口（下游消费者 = dashboard 6190）**：`GET/POST /api/ltm/settings` 读写 `ltm.json`（`dashboard/app.py:502-532`）；`GET/POST /api/ltm/prompt` 读写 `ltm_prompt.txt`（`dashboard/app.py:1261-1279`）；`GET /api/ltm/recent`、`POST /api/ltm/add`、`POST /api/memories/delete` 读/写/删 `facts`（`dashboard/app.py:619,665,729`）。

## 5. 与其他插件的协作关系

| 对方 | 关系 | 契约/约定 |
|---|---|---|
| `astrbot_plugin_access` | 跨插件 import 权限判定（`main.py:124-132`） | ImportError 时降级本地名单 `{1154487120}` + `event.role == "admin"`；`access/main.py:99` 把 `记忆`/`忘记` 默认判为 `user`，管理级子命令靠插件内 `_is_admin` 二道闸 |
| `astrbot_plugin_basicz` | 共享 `event`/`req`，互不写对方状态 | basicZ 的 `on_llm_request` 只记录 system_prompt 日志（`basicz/main.py:1777`），ltm 只追加不覆盖；同优先级默认 0 的钩子执行先后**待确认** |
| 判官 / `group_chat_context` | 无直接调用、不读判官 extra | 判官 `need_active_reply` 在私聊第一行就 `return False`（`group_chat_context.py:826`），私聊抽取只能靠 ltm 的 `on_llm_response`；群聊抽取读的是判官/上下文共享的 `platform_message_history`，不依赖判官是否放行（被 `stop_event` 的消息是否仍入库**待确认**） |
| `astrbot_plugin_private_settle` | 文本链下游 | 私聊合并后 `event.message_str` 变 `"A\nB\nC"`，ltm `learn_from_turn` 拿到的就是合并文本（`main.py:1048`）；两者 `on_llm_response` 均为默认优先级，先后**待确认** |
| `astrbot_plugin_meme_manager` / `vision_context` / `websearch` | 同挂 `on_llm_request` 注入不同内容 | 各自只动自己那部分 prompt，不共享 extra 键；meme_manager `priority=99999` 早于 ltm 默认 0（`meme_manager/main.py:444`） |
| 向量 8097 / provider | 外部 HTTP | 不可用则静默降级：embed `None` → 退回最近记忆（`main.py:656-663`）；chat 失败跳过本轮（`main.py:847-851`）；第三方额度满也跳过（`main.py:558-559`） |

## 6. 配置与数据文件

| 路径 | 用途 | 谁写 | 谁读 |
|---|---|---|---|
| `data/memory.db` → `facts` | 记忆主表 | ltm；dashboard `/api/ltm/add`、`/api/memories/delete` | ltm 召回/抽取/指令；dashboard 概览与记忆页 |
| `data/ltm.json` | 节奏/开关/TTL | dashboard `POST /api/ltm/settings`、人工 | ltm `load_settings()`（mtime 缓存） |
| `data/ltm_prompt.txt` | 抽取提示词 | dashboard `POST /api/ltm/prompt`、人工 | ltm `load_prompt()` |
| `data/ltm_usage.json` | 第三方直连 token 账本 | ltm `_add_usage()`；dashboard 调 `daily_limit/enabled` | ltm `_load_usage()/_quota_ok()`；dashboard 显示 |
| `data/ltm_purged.jsonl` | 物理删除前整行归档 | ltm `_archive_purged()` | 人工按 id 恢复（面板恢复入口**待确认**：未发现） |
| `apps/AstrBot/data/data_v4.db` → `platform_message_history` | 群历史游标 | AstrBot 框架 | ltm `_new_group_rows()`（只读） |
| `apps/AstrBot/data/cmd_config.json` | provider 端点/模式判定 | AstrBot WebUI / apimode | ltm `_resolve_llm()`、`_is_third_party()` |
| `data/api_mode.json` | 模式兜底 | `/切换`（apimode） | ltm `_is_third_party()` |

## 7. 顺序、坑与边界
- 优先级：ltm 三个钩子都是默认 0；meme_manager `99999`、private_settle 打标 `maxsize-500` 都在它前面，但 ltm 只**追加** system_prompt，不依赖顺序。
- **提示词占位符（已对齐）**：插件 `load_prompt()` 要 `{lines}`（必需）/`{known}`（可选，缺失降级为不注入已知事实）（`main.py:396,843`）。面板 `GET/POST /api/ltm/prompt` 已于 2026-11-23 改为同一口径：校验 `{lines}` 必需、缺 `{known}` 给提示不拦截（`dashboard/app.py`）；面板 UI 文案同步去掉了错误的「{candidates} 也认」。旧版本曾误校验 `{user}`/`{bot}`，若发现自定义提示词没生效，先确认是从旧版面板存的。
- BOM/乱码：配置一律 `utf-8-sig`；抽取提示词读 `utf-8` 且 `_looks_mojibake`/`_demojibake` 自动还原（`main.py:323-353,399-406`）；写回仍是 `utf-8`。
- 静默失败：文件坏 → 默认值 + WARN；embedding 不可用 → 最近记忆兜底；LLM 异常/空回复 → 跳过本轮；归档写失败只 WARN 不阻断清理。
- 过期语义：`superseded_by = -1` = 过期软删，`>0` = 合并指向新行；`_purge_expired` 先归档再物理删，并清掉指向已删行的悬空合并行（`main.py:1171-1213`）。
- 群聊回复不触发抽取（统一交给扫描器，`main.py:1045-1047`）；私聊同一人 `extract_cooldown=900s` 冷却，最近 24 条进 `_said` 窗口（`main.py:1023-1029`）。
- 扫描器每人只留 60 条 pending，预算 `scan_budget=3` 外的人留到下一轮；`MIN_BATCH=8` / `MAX_WAIT=1800` 才调用模型（`main.py:1375-1413`）。
- 启动时游标取 `MAX(id)`（`main.py:468-480`），停机期间的历史在下次启动后会被读到；第三方模式可由 `third_party_scan: false` 关掉群扫描（会产生 API 费用）。
- 升级：本插件是本地自写目录，AstrBot 升级不覆盖；但 `unified_perm` import 路径若随 access 重构变化，会静默降级为本地管理员名单。

## 8. 代码依据
`main.py:39-53`（根目录detect）、`66-120`（额度账本）、`124-132`（access import/降级）、`143-201`（路径与常量）、`206-213`（槽位）、`265`（PROMPT_FILE）、`323-411`（乱码修复/配置/提示词加载）、`426-445`（归档）、`448-529`（init_db/facts 列）、`533-586`（embed/chat）、`628-693`（召回）、`768-818`（解析）、`876-986`（入库去重）、`990-1021`（注入钩子）、`1023-1060`（私聊学习钩子）、`1064-1132`（扫描/去重循环）、`1134-1323`（过期/清理/去重）、`1325-1421`（扫描器）、`1425-1493`（指令）；交叉核对 `access/main.py:99`、`access/unified_perm.py:64`、`basicz/main.py:1777`、`group_chat_context.py:826`、`dashboard/app.py:45,58,502-532,619,665,729,1261-1279`。
