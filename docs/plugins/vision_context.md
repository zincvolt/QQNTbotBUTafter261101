# astrbot_plugin_vision_context — 与其他插件的接口

> 源码：`apps/AstrBot/data/plugins/astrbot_plugin_vision_context/`
> 版本：1.0.0（metadata.yaml）  分类：自写

## 1. 职责一句话

给白名单群 / `/私聊` 白名单私聊里出现的每张图在后台生成一次文字描述（按图片字节的 sha256 去重），回复时把最近的描述注入 `req.system_prompt`，让「这图啥意思 / 刚才那张图」这类跨轮追问不靠原图也能答，并为第三方模式省下 1000~2000 token 的原图输入；**无斜线指令**（main.py:29-31）。

## 2. 注册的钩子

| 钩子 | 优先级 | 触发时机 | 实际行为 |
|---|---|---|---|
| `@filter.event_message_type(filter.EventMessageType.ALL)` → `watch_images`（main.py:704-705） | 未显式声明（装饰器无 `priority` 参数，走框架默认） | 所有消息 | 只处理白名单群或 `/私聊` 白名单私聊；收集消息体 + Reply 链里的 `Image`（最多 3 张），`asyncio.create_task` 后台跑 `_store_caption`；不 `stop_event`、不发消息、不改 prompt |
| `@filter.on_llm_request()` → `inject_context`（main.py:850-851） | 未显式声明（装饰器无 `priority` 参数，默认 0；与 ltm/basicz/websearch 同档，同档顺序**待确认**，ltm.md:12） | 每次 LLM 请求组装时 | 按 session 取环形缓冲，筛掉低质 / 已注入项后**只追加** `req.system_prompt`；不 `stop_event`、不发消息、不动 `req.image_urls` |

两个钩子都不写 `event.set_extra`、都不注册 LLM 工具（全文件无 `set_extra` / `llm_tool`）。

## 3. 输入（别人给它什么）

- **事件字段**：`get_group_id()` / `get_sender_id()`（选 session：群号、`u<QQ>`，715-724,853-862）；`get_messages()` 里的 `Image` 与 `Reply.chain`（727-731）；`req.image_urls` / `req.prompt`（判官唤醒时判是否谈图，872-875）。
- **`event.get_extra` 键**：`vision_judge_wake`（只读，866）。由框架补丁 `builtin_stars/astrbot/group_chat_context.py` 的 `_mark_judge_wake` 在判官放行（含概率兜底）时置 `True`（PROJECT.md:440、VISION.md「按判官的需求注入」）；召唤词直通 / 必答规则 / 艾特不置位。**basicz 自身不写 extra**（basicz.md:22）。
- **读的配置文件 / 缓存库**：
  - `data/vision_mode.json`：`mode` → `_vision_mode()`，**按 mtime 缓存**（51-52,330-356），缺文件 / 写坏 → `local`。
  - `data/vision_usage.json`：`_load_usage()` 按 mtime 缓存（39-40,59-82），取 `enabled` / `daily_limit` / `group_limits` / `groups` / `tokens`，跨日清零；额度闸 `_quota_ok()`（85-104）。
  - `apps/AstrBot/data/cmd_config.json`：`platform_settings.id_whitelist` / `enable_id_white_list`（359-367,370-388）、`provider` + `provider_sources`（394-442，选 `modalities` 含 image 的 provider，`flash` 优先，跳过 127.0.0.1/localhost）；`utf-8-sig`。
  - `data/vision_cache.db` 的 `captions` 表：`sha` / `caption` / `bytes` / `hits` / `created` / `last_used`，WAL（144,216-317）。
  - 表情库 `packs/*/manifest.json` + `memes/<分类>/`：`load_meme_index()` 扫 sha256 **前 16 位** → (包, 分类, 描述)（445-479）。
- **外部 HTTP（本地端口）**：8085 `sk-vl-local` `Qwen3VL-4B-Instruct`、8083 `sk-ocr-local` `PaddleOCR-VL-1.6`（126-141,592-621）；云端 flash 端点 `base + /chat/completions`（394-442,683-687）；远程图下载 `_read_bytes()`（802-813）。
- **其他插件直接调用**：顶层 `from astrbot_plugin_basicz.main import VISION_HINTS as IMAGE_REF_HINTS`（182-189），basicZ 未加载时用本地兜底词表。`cache_get/put/gc`、`caption_shaky`、`load_meme_index` 是模块级函数，是否被外部 import **待确认**（全仓未见引用）。

## 4. 输出（它给别人什么）

- **`event.set_extra` 键与值**：无（不写任何 extra 键）。
- **LLM 工具**：无（不注册工具）。
- **改写 `req.system_prompt`**：`inject_context` 追加 `[群里|私聊里最近发过的图（按时间从早到晚）...]` 块，含最多 3 条、合计 ≤300 字（150-153,883-903）；下游 = 主模型。
- **改写 `req.prompt` / `req.image_urls`**：无（由 basicZ 负责）。
- **`stop_event`**：无（两个钩子都不停事件）。
- **发消息**：无。
- **写缓存 / 文件**：`captions` 表 `INSERT ... ON CONFLICT` 覆盖 caption/bytes（268-291）、命中 `hits+1`/`last_used`（238-265）、每小时最多一次 `DELETE`（294-317,794-798）；`data/vision_usage.json` 累加 `tokens` 与分群 `groups`（107-124）；新图按 sha256 前 16 位写入 `meme_manager/packs/unsorted/memes/未分类/<digest>.<ext>`（160-173,815-848）。
- **面板接口**：无内置接口；`vision_usage.json` / `vision_cache.db` / `vision_mode.json` 被 dashboard「视觉 / 额度」页读取（PLUGIN-COMMANDS.md:211-223、PROJECT.md:342）。

## 5. 与其他插件的协作关系

| 对方 | 关系 | 契约/约定 |
|---|---|---|
| basicz（读图闸） | 共享 DB + 词表导入 | 本插件给白名单图后台写 `captions`；basicZ 第三方模式查表命中就**整图不发**、只发文字，本地模式用存的描述（VISION.md §9；basicz.md:46,983-1029）。判官唤醒判定 `IMAGE_REF_HINTS` 直接 import basicZ 的 `VISION_HINTS`（182-189），basicZ 改词表这边跟着变。反过来 basicZ 的 `_should_read_images` 纯字符串闸决定**本轮是否真发图**（VISION.md §4；basicz.md:66），与本插件的后台缓存是两条独立路径 |
| 框架判官 group_chat_context.py | extra 键契约 | 判官放行打 `vision_judge_wake=True`，本插件见标后只在「本轮带图 / 命中 `IMAGE_REF_HINTS`」时注入历史描述；直通/艾特唤醒不打标，注入照旧（866-878；PROJECT.md:440） |
| apimode | 文件耦合，无 import | apimode 切 provider 时写 `vision_mode.json=third_party/local`（apimode.md:14,219-237），本插件 `_vision_mode()` 按 mtime 立即跟随；「主模型模式」与「识图档位」是两个维度，不互相 import |
| visionmode | 文件耦合，无 import | visionmode 的 `/读图` 写同一份 `vision_mode.json`，本插件是读侧（704-712,578-590）；`off` 档双方一致：不下载、不识图、不调 flash |
| meme_manager | 共享目录 + 表 | 读其 `manifest.json` 取分类描述（445-479）；新图写进其 `unsorted/未分类` 收件箱（815-848）；两边共用 `captions` 表，体积上限同为 1.5 MiB（143-145）。该官方插件本任务不纳入改动 |

## 6. 配置与数据文件

| 路径 | 用途 | 谁写 | 谁读 |
|---|---|---|---|
| `data/vision_mode.json` | 识图档位 mode/port/model | apimode、visionmode、dashboard | 本插件 `_vision_mode()`、basicz |
| `data/vision_usage.json` | 云端识图 token 账本 + 分群额度 | 本插件 `_add_usage`、dashboard | 本插件 `_quota_ok`、dashboard |
| `data/vision_cache.db`（`captions`） | 图片释义缓存，跨插件共享 | 本插件、basicz、meme_manager | 本插件、basicz |
| `apps/AstrBot/data/cmd_config.json` | 群/私聊白名单、可识图 provider | WebUI、access、apimode | 本插件、basicz |
| `.../meme_manager/packs/*/manifest.json` | 表情分类描述 | meme_manager | 本插件 `load_meme_index` |
| `.../meme_manager/packs/unsorted/memes/未分类/` | 新图收件箱 | 本插件 `_collect_bytes` | meme_manager |

## 7. 顺序、坑与边界

- 模式分流（578-590,712-714）：`off` 直接返回（不下载 / 不识图 / 不调 flash）；`third_party` 跳过停掉的 8083/8085 直连 flash，且只对 `0 < size ≤ 1.5 MiB` 的图做；`local` 按 8085→8083 顺序试，本地全挂熔断 120 秒再走 flash（592-621）。
- 缓存命中即返回（761-765）：`hits+1`、`last_used` 更新，**0 token**；同一张图只识一次。表情库已收录且分类≠「未分类」的图直接用 `[表情库·分类] 描述`，并同步写一份进 `captions`（771-783），否则 basicZ 查不到会白等满 9 秒窗口再把原图发出去。
- 低质描述不当描述用：`caption_shaky`（192-213）判空 / <10 字 / 含「暂存·未归类·未分类」/ 中文占比 <30% → 不注入（891-892）；该图按「没描述」交给 basicZ 发原图兜底。
- 注入只追加不覆盖：`text in req.prompt` 去重（889-890）；判官唤醒额外过 `IMAGE_REF_HINTS`（866-878）；窗口 900 秒、上限 3 条 / 300 字（150-153）。
- 云端坑：flash 请求必须带 `"thinking": {"type": "disabled"}` 且 `max_tokens` 提到 200，否则 content 为空、内容全在 reasoning_content（675-678）；`Semaphore(1)` 串行（325,680）；云端失败熔断 300 秒（VISION.md §9）。额度由 `vision_usage.json` 自记，apimode 统计不到（36-38）。
- 顺序：`on_llm_request` 无显式 priority（默认 0），与 ltm/basicz/websearch 同档，同档执行顺序**待确认**（ltm.md:12）；本插件依赖「只追加自己的 prompt 块」避免互相踩踏。BOM：`vision_mode.json` 以 `utf-8-sig` 读（349），兼容带/不带 BOM；visionmode 写侧用 `utf-8`（visionmode/main.py:68）。
- 抓图上限：每条消息最多 3 张（735），`_inflight` 去重（737-740），session 隔离（群号 / `u<QQ>`）。

## 8. 代码依据

`main.py:29-31`（自声明）、`39-52`（账本/模式常量）、`59-124`（账本读写与额度闸）、`126-173`（端点/缓存/注入常量）、`182-189`（VISION_HINTS）、`192-317`（caption_shaky 与缓存三函数）、`330-442`（模式/白名单/云端端点）、`445-521`（meme 索引与分档）、`545-702`（`_caption` / `_caption_cloud`）、`704-705`（watch_images）、`743-848`（`_store_caption` / `_read_bytes` / `_collect_bytes`）、`850-907`（inject_context）。外部佐证：`docs/VISION.md` §4/§9、`docs/PROJECT.md:440`、`docs/plugins/basicz.md:46,66`、`docs/plugins/ltm.md:12`。
