# astrbot_plugin_access — 与其他插件的接口
> 源码：`apps/AstrBot/data/plugins/astrbot_plugin_access/`
> 版本：2.0.0（metadata.yaml）  分类：自写

## 1. 职责一句话
统一斜线指令的三档鉴权闸门（公开/管理/超管），并在加载时重排全部消息 handler 的优先级（闸门 > 指令 > 纯监听），同时在线维护指令权限表与按群开关文件。

## 2. 注册的钩子

| 钩子 | 优先级 | 触发时机 | 实际行为 |
|---|---|---|---|
| `@filter.on_astrbot_loaded()` → `on_loaded`（main.py:312-314） | — | AstrBot 加载完成（构造 `__init__` 也调一次，main.py:299-308） | 调 `_enforce_bands()`：把全部 `AdapterMessageEvent` handler 的 `extras_configs["priority"]` 改写后整体重排（main.py:316-361）。副作用：覆盖其他插件自报的 priority（含原 maxsize）；无 stop_event、不改 prompt、不释放锁。框架结构变化时 try/except 静默跳过（main.py:330-332）。 |
| `@filter.event_message_type(ALL, priority=GATE_PRIORITY)` → `gate`（main.py:516-517） | `GATE_PRIORITY = sys.maxsize`（main.py:45） | 每条消息；内部只对斜杠/唤醒消息做鉴权（main.py:428-467） | ① 本群 `warmup` 关 + contains 关键词命中 → `stop_event()`（main.py:526-540）；② 自有 6 指令（权限/指令/私聊/群聊/进群提醒/管理员）直接 `event.send` 并 `stop_event()`（main.py:544-575）；③ 其他指令权限不足 → 发拒答 + `stop_event()`（main.py:588-591），足够则尝试写 extra（main.py:582-586）并放行。顶层 try/except 保证异常不拦消息（main.py:592-593）。 |

本插件只有这两个钩子，不注册 `@filter.command`；自有指令全在 gate 里手写匹配（main.py:544）。

## 3. 输入（别人给它什么）

- **事件字段**：`message_str`、`message_obj.raw_message`、`is_at_or_wake_command`、`get_sender_id()`、`role`、`get_group_id()`（main.py:428-509）。
- **`event.get_extra` 键**：`handlers_parsed_params`（框架在 `astrbot/core/pipeline/waking_check/stage.py:265` 写入；access 仅在它是空 dict 时写回，main.py:582-586）。
- **读的配置文件/数据**：`cmd_perm.json`（main.py:129,365-380）、`group_flags.json`（main.py:139,160-184）；`self.config.super_admins`（main.py:471-475）；`context.get_config()` 的 `admins_id`、`platform_settings.id_whitelist`、`platform_settings.enable_id_white_list`（main.py:477-483,897-898,932,1066）。`unified_perm.py` 另读 `astrbot_plugin_access_config.json`（utf-8-sig）与 `cmd_config.json`（utf-8-sig）及环境变量 `FURCON_ADMINS`（unified_perm.py:25-47）。
- **外部 HTTP**：无。
- **其他插件直接调用**：`unified_perm` 的 `get_level/is_admin/is_super/admin_qqs`（unified_perm.py:50-78），已被 apimode（main.py:52）、furcon（main.py:120-121）、ltm（main.py:126）、visionmode（main.py:31）、creator（main.py:88）import；`card_render.render_text_card`（card_render.py:65），furcon 在用（furcon/main.py:952-953）；顶层 `load_group_flags/save_group_flag`（main.py:160,187）。`_load_declared()` 用 ast 扫描所有插件 main.py 的 `DECLARED_COMMANDS`/`DECLARED_BEHAVIOR`，不执行插件代码（main.py:782-823）。

## 4. 输出（它给别人什么）

- **`event.set_extra` 键与值**：向 `handlers_parsed_params` 字典写入 `__access_cmd__ = {"cmd": cmd}`（仅当该 extra 已存在且为空 dict，main.py:582-586）。下游消费者：**待确认**——全仓 grep 只见写入方；框架读该 extra 的 `builtin_stars/astrbot/main.py:214` 与 `group_chat_context.py:1882` 只读字典真假，不读 `__access_cmd__` 子键。
- **改写 req.system_prompt / req.prompt / 工具列表**：无。
- **`stop_event`**：热群关键词被拦、自有指令处理完、权限不足三种（main.py:539,574,591）。
- **发消息**：`event.send` 发图卡或纯文字兜底（main.py:222-231）；图卡由 `card_render.render_text_card` 写到 `D:\QQNTBOT\data\access_cards`（card_render.py:62,65-88），绘卡失败静默降级为文字。
- **写文件**：`cmd_perm.json`（main.py:382-389）、`group_flags.json`（main.py:187-204）、`cmd_config.json` 的 `admins_id` / `id_whitelist` / `enable_id_white_list`（`cfg.save_config()`，main.py:909,925,939,1090,1106）。
- **面板/HTTP 接口**：无；dashboard 直接读写同一批配置文件。
- **全局副作用**：重排所有消息 handler 的执行顺序（见 §2），这是它对其他插件最强的影响面。

## 5. 与其他插件的协作关系

| 对方 | 关系 | 契约/约定 |
|---|---|---|
| apimode / furcon / dice | 下游受闸 | 三者模块名列在 `_CMD_LISTENER_MODS`（main.py:50-54），分档为 `CMD_BAND = sys.maxsize-10`（main.py:46,349-350）；级别不够的指令到不了它们的 handler。 |
| apimode / furcon / ltm / visionmode / creator | 权限供给 | 统一 import `unified_perm.is_admin`，取消各自 ADMINS 名单；口径 = `super_admins ∪ admins_id ∪ FURCON_ADMINS ∪ 群管理角色`（unified_perm.py:50-69）。 |
| furcon | 绘卡复用 | 直接 import `card_render.render_text_card`（furcon/main.py:952-953）；缓存按标题+内容 SHA256 命名（card_render.py:81-88）。 |
| basicz | 单向供给 | basicz import `WELCOME_TEXT`（basicz/main.py:42），并只读同款 `group_flags.json`（basicz/main.py:73-75）；access 是这两个数据的唯一写入方。 |
| 框架判官 / 内置主动回复 / 复读机 | 顺序仲裁 | 未命中指令的纯监听被分到 `LISTENER_BAND = sys.maxsize-100`（main.py:47,352）；判官另读同一份 group_flags.json（PROJECT.md:440）。 |
| meme_manager | 同口径 | 走框架 `PermissionType.ADMIN`；本插件 `_autodiscover()` 对带 ADMIN 过滤器的指令默认给 admin 级（main.py:409-413）。 |

## 6. 配置与数据文件

| 路径 | 用途 | 谁写 | 谁读 |
|---|---|---|---|
| `astrbot_plugin_access/cmd_perm.json` | 指令权限表，在线改即时生效 | `/权限 设置/重置`（main.py:728,750） | access（main.py:368-376） |
| `astrbot_plugin_access/group_flags.json` | 按群 auto_chat / warmup / welcome | `/群聊`、`/进群提醒`（main.py:1001,1039）、dashboard | access、basicz（只读副本）、框架判官 |
| `data/config/astrbot_plugin_access_config.json` | 插件配置 `super_admins` | WebUI | `unified_perm._super_admins()`（unified_perm.py:25-34） |
| `apps/AstrBot/data/cmd_config.json` | admins_id、私聊白名单、白名单检查总闸 | WebUI + `/管理员`、`/私聊` | access、unified_perm、框架白名单检查 |
| `D:\QQNTBOT\data\access_cards\*.png` | 一图流卡缓存 | card_render（card_render.py:85-88） | access 发图时复用 |

## 7. 顺序、坑与边界

- 分档只处理 `EventType.AdapterMessageEvent`，且用框架私有属性 `star_handlers_registry._handlers`（main.py:341-359）；框架升级可能失效，届时只打 warning 不崩（main.py:330-332）。
- 存档用 `utf-8`，`unified_perm` 读两个全局配置用 `utf-8-sig` 兼容 BOM（unified_perm.py:31,39）；文件坏了按默认/空名单静默兜底。
- gate 异常一律 pass-through（main.py:592-593）；`_save_perm`/`save_group_flag` 写失败只打 error（main.py:388-389,203-204）——可能出现"提示改了但没落盘"。
- 自有指令必须 `event.send` 而非 yield：yield 通道会被 peer 的 decorate_result 判为「空回复」清空并 stop_event（main.py:553-555）。
- 旧键 `reply_at/proactive` 读取时映射到 `auto_chat/warmup`，落盘只写新键（main.py:142-157,187-204）；外部直接写旧键要确认消费方都走映射。
- `__access_cmd__` 写入条件苛刻（仅 extra 为空 dict 时生效）且全仓无读取方，不要把它当稳定跨插件契约。
- AstrBot 升级会覆盖 core 补丁（PROJECT.md:434-445），分档依赖的框架结构需重验。

## 8. 代码依据
`main.py:45-47`（三档常量）、`main.py:50-54`（跨插件模块名）、`main.py:129-143`（路径与默认值）、`main.py:160-204`（group_flags 读写）、`main.py:299-361`（构造 + on_loaded + 分档）、`main.py:365-417`（权限表与自动发现）、`main.py:428-496`（指令识别与权限分组）、`main.py:516-593`（gate）、`main.py:782-876`（声明扫描与权限卡）、`main.py:880-1111`（私聊/群聊/进群提醒/管理员）；`card_render.py:62-192`；`unified_perm.py:25-78`。
