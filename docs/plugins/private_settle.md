# astrbot_plugin_private_settle — 与其他插件的接口
> 源码：`apps/AstrBot/data/plugins/astrbot_plugin_private_settle/`
> 版本：1.0.2（metadata.yaml）  分类：自写

## 1. 职责一句话
私聊里补上判官那套「等用户把一口气说完」：把连发的几条合成一条用户消息再回一次（图片接进同一消息链），不送判官、不加任何判定，配置默认 `settle=5`、`merge_window=20`、`min_gap=10`。

## 2. 注册的钩子

| 钩子 | 优先级 | 触发时机 | 实际行为 |
|---|---|---|---|
| `@filter.on_waiting_llm_request(priority=maxsize)` `hold_private`（`main.py:184`） | `maxsize`（抢在 basicZ gate 之前） | 私聊消息确定要请求 LLM 后 | 等安静 `settle` 秒且距上次回复 ≥`min_gap`（最多 `merge_window`）；把攒的文本/图片并进 owner 事件；后到者 `stop_event`；本钩子自身不改 `req` |
| `@filter.on_llm_request(priority=maxsize-500)` `mark_inflight`（`main.py:374`） | `maxsize-500`（仍早于 meme_manager `99999` 与 basicZ 默认 0） | LLM 开始生成 | 私聊写 `_inflight[umo] = now + 180.0`，只用于后续排队，不参与任何判定 |
| `@filter.on_llm_response()` `clear_inflight`（`main.py:380`） | 默认 0 | 拿到回复 | 私聊 `pop(_inflight, umo)`，与 basicZ 释放 busy 同一时机 |
| `@filter.after_message_sent()` `clear_after_send`（`main.py:386`） | 默认 0 | 消息真正发出后 | `pop(_inflight, umo)`，并记 `_last_sent[umo] = now` 供 `min_gap` 计算 |

> 无斜线指令：`DECLARED_COMMANDS = {}`（`main.py:43`）。副作用：`stop_event` = 有（后到消息/让位者）；改 prompt = 不直接改；写历史 = 无（被合并事件在 LLM 前停掉，`update_conversation` 不执行，`PRIVATE-CHAT.md:58-59`）；发消息 = 无（本插件不调 `event.send`）。

## 3. 输入（别人给它什么）

**事件字段**：`event.is_private_chat()`（异常时当群聊跳过，`main.py:191-194`）；`event.message_str`（`main.py:196`）；`event.unified_msg_origin` = umo，作为 `_seq/_pending/_inflight/_last_sent` 的键（`main.py:197,377,383,391`）；`event.get_sender_id()` 转字符串查白名单（`main.py:216`）；`event.message_obj.message` 里的 `Image` 组件（`_images_of`，`main.py:152-167`）；`text[:1] in ("/", "／")` 直接放行（`main.py:212`）。

**`event.get_extra` 键**：无。源码未出现 `event.get_extra(...)` 调用，不消费 basicZ/判官/vision 打的任何 extra 标记（**待确认**：框架透传的标记未在本插件读取）。

**读的配置文件**：
- `data/private_settle.json`：`load_config()`（`main.py:68`），`utf-8-sig` + mtime 缓存；键 `enabled/merge/settle/merge_window/min_gap/poll/inflight_wait/whitelist_only/log`，clamp 为 `settle∈[0,15]`、`merge_window∈[1,60]`、`min_gap∈[0,60]`、`poll∈[0.05,1]`、`inflight_wait∈[0,120]`（`main.py:52-62,103-108`）。默认值与 `PRIVATE-CHAT.md:154-166`、`dashboard/app.py:2057-2067` 一致。
- `apps/AstrBot/data/cmd_config.json`：`_private_allowed()`（`main.py:113`）读 `platform_settings.enable_id_white_list` 与 `platform_settings.id_whitelist`，只认含 `FriendMessage` 的条目、取 `rsplit(":",1)[-1]` 作 QQ。与 `/私聊` 白名单同一份数据（`PLUGIN-COMMANDS.md §1.2`）。

**数据库表 / 外部服务**：无。不连 SQLite、不发 HTTP；只靠 `asyncio.sleep` + `time.time()`。

**其他插件直接调用**：无公开 API；`load_config`、`_private_allowed`、`_images_of` 是模块级函数，`_apply_merge`/`_taken_over`/`_drop` 是 `Main` 私有方法，仓库内无外部调用记录。

## 4. 输出（它给别人什么）

**`event.set_extra` 键与值**：无。

**改写 `req.system_prompt` / `req.prompt`**：本插件源码不直接碰 `req`。`_apply_merge` 写 `event.message_str = "\n".join(texts)`，并同步 `event.message_obj.message_str`（如实现有该属性）；图片 `chain.extend(images)` 接到 owner 消息链（`main.py:322-346`）。**下游消费者** = basicZ gate、`astr_main_agent`、ltm、vision/meme：`req.prompt = event.message_str` 由框架侧赋值（`PRIVATE-CHAT.md:56-57`），本插件源码未见该赋值，**待确认**具体赋值点。

**注入上下文内容**：合并后的多行用户文本 + 原 `Image` 组件；原有顺序是 owner 原文在前，后到文本依次 `\n` 拼接（`main.py:332-341`）。纯图片（`text` 为空）时只把图并进正在攒的组并 `stop_event`（`main.py:198-211`）。

**`stop_event`**：并入组的新消息（`main.py:236`）、纯图片并入组（`main.py:210`）、让位的旧 owner `_drop()`（`main.py:366-370`）。owner 正常发出时不 stop。

**发消息 / 写数据库 / 写文件**：均无。面板配置只被读取，不回写。

**面板接口**：`GET /api/dm/settle` 读、`POST /api/dm/settle` 合并写 `data/private_settle.json`（`dashboard/app.py:2081-2116`）；`poll` 固定 0.2 不开放面板；下游消费者 = 面板「判官 → 私聊话段合并」。私聊表情策略 `data/meme_dm.json` 是**另一个插件**的地盘（`dashboard/app.py:2119-2129`）。

## 5. 与其他插件的协作关系

| 对方 | 关系 | 契约/约定 |
|---|---|---|
| `astrbot_plugin_basicz` 闸门 | 钩子顺序 | `hold_private` 在 `on_waiting_llm_request(maxsize)`，`basicz.gate` 在 `on_waiting_llm_request()` 默认 0（`basicz/main.py:1493`），所以等待/合并发生在注入防护、要表情、在途 busy、冷却、并发上限之前；本插件不碰 basicZ 的 `_busy` |
| basicZ **在途锁** | 时机对齐、互不共享 | basicZ `_busy[umo]` 由 `on_llm_response`/`after_message_sent` 释放（`basicz/main.py:1487,1562-1570`）；本插件 `_inflight` 也在同两处清，但只做排队、不做丢弃。basicZ 的 busy 用于丢弃非 @ 消息，两套锁独立 |
| AstrBot **session 锁** | 排队原因 | 私聊里 basicZ 走 @/唤醒直通、不置 busy（`basicz/main.py:1530-1536`），但 AstrBot session 锁会把同会话 LLM 请求串行化；B、C 若都在 A 生成期间过钩子，会各回一条，所以 owner 在 settle 前先等 `_inflight`（`main.py:263-276`，`PRIVATE-CHAT.md:82-85`） |
| **follow-up**（判官追文 `?`） | 私聊无此链路 | 判官 `need_active_reply` 对非群消息直接 `return False`（`group_chat_context.py:826`），`followup_enable/followup_gap` 只在群判官分支使用（`group_chat_context.py:514-515,1146-1157`）；本插件不写 extra 键给 follow-up，两者无直接契约 |
| `astrbot_plugin_ltm` | 文本下游 | 合并后的 `event.message_str` 成为私聊 `learn_from_turn` 的抽取输入（`ltm/main.py:1048`）；两插件 `on_llm_response` 同为默认 0，先后**待确认** |
| `astrbot_plugin_meme_manager` | 图片/表情 | 合并图片留在 `message_obj.message`，basicZ 读图与 meme 识图照常；私聊表情走 `meme_dm.json` 的本地补丁（`PRIVATE-CHAT.md §4`），**升级 meme_manager 会覆盖补丁**（`PROJECT.md §14`） |
| `astrbot_plugin_access` | 白名单同源、无 import | 只读 `cmd_config.json` 的同一份 `id_whitelist`，不调用 `unified_perm`；`whitelist_only=false` 时对所有人生效，与 `/私聊` 闸门口径可能不一致 |
| 指令插件（access/furcon/dice/ltm） | 不抢指令 | 斜杠/全角 `／` 开头直接 return（`main.py:212-214`），指令在 handler 阶段已被消费（`PRIVATE-CHAT.md:90-98`） |

## 6. 配置与数据文件

| 路径 | 用途 | 谁写 | 谁读 |
|---|---|---|---|
| `data/private_settle.json` | 合并/等待/在途参数 | dashboard `POST /api/dm/settle`（`app.py:2115`）、人工 | 本插件 `load_config()`、`_drop()`（日志开关） |
| `apps/AstrBot/data/cmd_config.json` → `platform_settings.id_whitelist` / `enable_id_white_list` | 私聊白名单（同源） | AstrBot WebUI / access `/私聊` | 本插件 `_private_allowed()`；ltm `_resolve_llm()` 也读同文件 |
| `data/meme_dm.json` | 私聊表情策略（**非本插件**） | dashboard `app.py:2119+` | meme_manager 本地补丁 |
| 无数据库 / 无状态文件 | `_seq/_pending/_inflight/_last_sent` 全在内存 | 本插件进程 | 本插件进程（重启即清零） |

## 7. 顺序、坑与边界
- 优先级链：`maxsize`（等待合并）→ `maxsize-500`（在途打标）→ meme_manager `99999` → basicZ 默认 0。`on_waiting_llm_request` 不属于 `AdapterMessageEvent`，**不受 access 分档重排影响**（`access/main.py:316-359` 只处理 AdapterMessageEvent）。
- **默认值口径**：以源码 `DEFAULTS`（`main.py:52-62`）和 `PRIVATE-CHAT.md:154-166` 为准：`settle=5.0`、`merge_window=20.0`、`min_gap=10.0`、`inflight_wait=45.0`、`whitelist_only=true`。`PROJECT.md §9.6` 与 §4 里的「settle 默认 3.5s」是群判官 `burst_settle`（`dashboard/app.py:1987`），**不是私聊 settle**（`PRIVATE-CHAT.md:61-75` 记录了实测 0.58s 落单才加 `min_gap`）。
- 私聊必回：`merge_window` 到点必发（`main.py:298-306`）；`inflight_wait` 超时也继续（`main.py:270-272`）；`settle=0` 关安静等待、`min_gap=0` 关回复间隔（`PRIVATE-CHAT.md:77-78`）。
- `merge=false` 回退旧行为：旧 owner 标 `yield=True` 并被 pop，自己不再 stop，新消息接管（`main.py:238-246`），体现为「只回最新」。
- 指令边界：等待窗口里发指令会**立即执行并回复**，owner 的聊天回复仍在 settle 后回来，短时间两条属预期（`PRIVATE-CHAT.md:106-109`）；首条就是指令则 0 等待放行。
- 静默失败：配置读不了 → 默认值 + WARN；白名单读不了 → 全员放行（`main.py:144-146`）；`is_private_chat()` 抛异常 → 当群聊跳过；`utf-8-sig` 读 BOM 安全。
- 合并只改 **owner** 事件，不动 `raw_message`、不动其他事件，首字符仍是 owner 原文，不会冒充斜杠指令（`PRIVATE-CHAT.md:96-98`）。
- 升级：本插件自写目录不会被 AstrBot 升级覆盖；但依赖的 meme_manager 私聊补丁会被其升级覆盖，需重打（`PROJECT.md §14`）。

## 8. 代码依据
`main.py:1-28`（设计说明/优先级）、`42-62`（声明与默认值）、`64-110`（配置加载/clamp）、`113-149`（白名单）、`152-167`（图片提取）、`170-182`（内存状态）、`184-320`（主钩子：放行/并入/在途/窗口）、`322-346`（合并写回）、`348-370`（让位）、`374-394`（在途三钩子）；交叉核对 `PRIVATE-CHAT.md:1-5,33-45,61-85,90-112,152-171,183-211`、`PROJECT.md:300-324,434-445`、`basicz/main.py:1487-1570`、`group_chat_context.py:514-515,826,1146-1157`、`dashboard/app.py:59,2057-2116`、`access/main.py:42-47,316-359`、`ltm/main.py:1048`。
