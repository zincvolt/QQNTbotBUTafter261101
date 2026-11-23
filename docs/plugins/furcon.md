# astrbot_plugin_furcon — 与其他插件的接口
> 源码：`apps/AstrBot/data/plugins/astrbot_plugin_furcon/`
> 版本：1.2.1（metadata.yaml）  分类：自写

## 1. 职责一句话
兽聚工具箱：抓 FEC 兽展日历并渲染倒计时/列表/城市/运势/群统计图片卡，由斜杠指令或喊名字触发、一张图 + `stop_event` 不进大模型；另有「特别关心」每日定时播报。

## 2. 注册的钩子

| 钩子 | 优先级 | 触发时机 | 实际行为 |
|---|---|---|---|
| `@filter.event_message_type(EventMessageType.ALL)` → `handle`（main.py:1059-1256） | 源码无显式 priority（注释 1054-1058 说明不再自报 maxsize）；运行时被 access `_enforce_bands` 归到 `CMD_BAND = maxsize-10`（access/main.py:49-54,341-355） | 每条适配器消息 | `match_command(text, slash)`（1077）命中才继续；不匹配静默 return 且**不** stop_event（1078-1082）；管理员开关写 `furcon_enabled.json`（1089-1102）；未启用群回提示（1104-1116）；watch / help / fortune / stats / 展会查询各分支发图或文字并 stop_event（1123-1252，经 `_send_card` 1048-1052）；`_busy[umo]` 防重入（1118-1121,1256）；异常只记日志。 |
| `@filter.on_astrbot_loaded()` → `start_watch`（main.py:1258-1261） | — | AstrBot 加载完成 | 起 `_watch_loop()` 每分钟扫一次 `furcon_watch.json`（1263-1270）；到点按 `targets` 用 `context.send_message(umo, chain)` 发倒计时图并回写 `last_sent`（1272-1313）。 |

没有 `@filter.command(...)`、`on_llm_request`、`llm_tool`、`on_decorating_result`；所有指令由 `match_command()` 在 ALL 监听内自行解析（COMMANDS 表 147-155 + 组合词表 163-236）。

## 3. 输入（别人给它什么）

- **事件字段**：`message_str`（1062,1073）、`message_obj.raw_message`（1066-1072；dict 取 `raw_message` 字符串，用于判斜杠前缀）、`unified_msg_origin`（1118,1146,1299；防重入键与播报目标）、`get_group_id()`（1085,1173）、`get_sender_id()`（1086,1167）、`get_sender_name()`（1168）、`event.role`（降级 admin 判定时使用，128）。
- **`event.get_extra` 键**：无（全文件无 `get_extra` / `set_extra`）。
- **读的配置文件/数据库**：`data/furcon_enabled.json`（59,958-967；`groups` → bool，默认 false）；`data/furcon_watch.json`（58,1272-1287,1294-1312；`enabled`/`event`/`time`/`targets`/`last_sent`）；`data/furcons_cache.json`（56,313-322；`fetched` + `events`，TTL 6h）；`apps/AstrBot/data/data_v4.db`（64-69,836-851；`platform_message_history` 只读，取 `sender_name`/`sender_id`/`created_at`，条件 `user_id LIKE '%:{group_id}'` 且近 7 天，排除 `sender_id=1474388967`）；`astrbot_plugin_access/unified_perm.py`（118-121 import `admin_qqs` / `is_admin`）；`access/card_render.py` 惰性 import（950-955,1153）；字体 `fonts/NotoSansSC-Bold.ttf`（93-112）。
- **环境变量**：`QQNTBOT_ROOT`（45-47）、`FURCON_BOT_DB`（64-69）、`FURCON_FONT`（94-95）、`FURCON_NAME_CALL`（115，默认 `阿灰|小灰|灰狼`）、`FURCON_ADMINS`（124-125，降级管理员名单）。
- **外部 HTTP**：`GET https://www.furrycons.cn/`（70,324-327，从 `__NEXT_DATA__` 取 events，失败回退旧缓存）；宣传图下载 `https://images.furrycons.cn/{thumb}`（376,285,495）。
- **其他插件直接调用**：顶层函数 `expand_place` / `fetch_events` / `pick_next` / `fortune_of` / `group_stats` / `match_command` / `group_enabled` / `set_group_enabled` / `render_*` 全为模块级函数，但全仓 grep 显示仅本文件内部调用。反向依赖：access 的 `card_render.py:21-28` 直接读本插件字体文件，并在注释中声明参考本插件绘卡风格（`card_render.py:1-4`）。

## 4. 输出（它给别人什么）

- **`event.set_extra` 键与值**：无。
- **LLM 工具**：无（命中即发图并 stop_event，消息不进模型）。
- **改写 prompt**：无。
- **`stop_event`**：除"未匹配"与"未启用群的 help"外，所有命中分支都 stop_event——开关类 1092/1096/1101、未启用提示 1115、watch 类 1126/1132/1137/1149、help 1163、fortune 经 `_send_card` 1051、stats 1176、数据失败 1184、next 1191、recent 经 1051、city 类 1206/1213/1223/1246/1251。下游效果：判官/复读机/大模型不再补一句。
- **发消息**：`event.send(event.image_result(str(path)))` 发各类卡（1050）；`event.send(event.plain_result(...))` 发提示/用法/失败文案；定时播报走 `self.context.send_message(umo, chain)`（1306，`ImageComp.fromFileSystem`，绕开当前 event）。
- **写文件**：`furcon_enabled.json`（970-981，按 group_id 写 bool）、`furcon_watch.json`（1129-1147 设置、1311-1313 回写 `last_sent`）、`furcons_cache.json`（395-402）、`data/furcons_cards/YYYYMMDD_<key>_<hash>.png`（269-276 路径；485-487/706-708/768-770/831-833/920-922 保存）。
- **面板/HTTP 接口**：无；开关与关心只由聊天指令改 JSON（dashboard 是否也直接写这两个文件**待确认**）。
- **下游消费者**：群/私聊终端用户；access 读本插件字体；AstrBot 主模型收不到被 stop 的消息。

## 5. 与其他插件的协作关系

| 对方 | 关系 | 契约/约定 |
|---|---|---|
| access | import + 文件 + 优先级三重关系 | import `unified_perm.admin_qqs` / `is_admin`（118-121），单拎降级 `FURCON_ADMINS`（124-130）；在 `_CMD_LISTENER_MODS`（access/main.py:51）被强制到 CMD_BAND；权限表默认：查询 user、开关/关心 admin（access/main.py:100-125）；access `card_render.py:23-28` 读本插件 `fonts/NotoSansSC-Bold.ttf`。 |
| basicZ / 判官 / 复读机 | 钩子竞争 | 原注释（1054-1058）：不抢在主动回复前会"一句话 + 一张卡"；现由 access 分档保证先跑完并 stop_event；不匹配立即 return，不影响正常聊天（1078-1082）。 |
| 骰子 / meme_manager 等 | 无数据交换 | 无 set_extra、无 LLM 工具、无共享 JSON；`match_command` 识别不到就返回 `("", "")` 且不 stop_event（1026-1029 注释：别的插件可能有同名指令）。 |
| 特别关心播报 | 跨请求定时 | `_watch_loop` 用 `context.send_message(umo, ...)` 主动发，targets 存 `event.unified_msg_origin`（1146），每天只发一次（`last_sent == 今天` 即跳过，1285-1287）。 |

## 6. 配置与数据文件

| 路径 | 用途 | 谁写 | 谁读 |
|---|---|---|---|
| `data/furcon_enabled.json` | 按群开关 `groups` | furcon（`/启用`、`/关闭`） | furcon `group_enabled` |
| `data/furcon_watch.json` | 关心的展会 / 时间 / targets / last_sent | furcon（`/关心`、`/取消关心`、播报回写） | furcon `_maybe_broadcast` |
| `data/furcons_cache.json` | 展会数据缓存 `fetched` + `events` | furcon `fetch_events` | furcon `fetch_events` |
| `data/furcons_cards/` | 当天图片缓存 `YYYYMMDD_<key>_<hash>.png` | furcon `render_*` | furcon `_send_card`、定时播报 |
| `apps/AstrBot/data/data_v4.db` | `platform_message_history` 表 | AstrBot 主框架 | furcon `group_stats`（mode=ro 只读） |
| `astrbot_plugin_access/unified_perm.py` + `astrbot_plugin_furcon/fonts/` | 权限判定 + 帮助卡字体 | access（代码）/ 随插件发布（字体） | furcon import；access `card_render.py` 读字体 |
| 环境变量（见 §3） | 路径 / 库 / 字体 / 唤醒词 / 管理员覆盖 | 部署环境 | furcon `_detect_root` 等 |

## 7. 顺序、坑与边界
- 优先级：源码删掉了 `priority=maxsize`（注释 1054-1058），靠 access 强制 CMD_BAND；单拎运行（access 未加载）时按普通 ALL 监听顺序，可能晚于主动回复——实测表现**待确认**。
- 斜杠被框架剥掉：靠 `message_obj.raw_message` 的原始文本判 `slash`（1070-1075）；`event.message_str` 里没有 `/`（COMMANDS.md:302-303）。
- 不匹配一律让路：非斜线且未喊名字早退（993-998）；识别不到命令返回 `("", "")` 且不 stop_event（1026-1029），故早期"带地名就当展会查询"吞指令的坑不会重演。
- 组合匹配顺序：固定语法 `COMMANDS` 先判（1001-1003），再按位置取最早城市名（1007-1012）与最早时间词（1016-1022）；有 kind/marker 才当展会查询（1024-1029）；`watch` 排在 `fortune`/`stats` 前，避免 `/关心 苏州小聚` 被当城市查询（144-155 注释）。
- 按群开关默认 false：未写进 `furcon_enabled.json` 的群一律未启用（958-967,1104-1116）；但 `help` 在未启用群仍可用（1105-1107）；`enable_on/off` 在私聊会被提示"请在要开启的群里发"（1094-1097）。
- 缓存与时间戳：卡片按天 + key 缓存（269-276），命中旧文件直接返回，卡底"生成于"仍是首次生成时间（COMMANDS.md:196-198）；展会数据 6h TTL（71,318），抓取失败回退旧缓存（328-335）。
- `_busy` 按 `umo` 的内存锁（1045,1118-1121,1256），重启即丢；同一会话重复触发直接 return 且不 stop_event，此时若另一 handler 正在生成会怎样**待确认**。
- 群统计只读库且排除 `sender_id=1474388967`（859），`mode=ro` URI 打开（841），异常返回空不抛（838-849）；库路径可被 `FURCON_BOT_DB` 覆盖（64-69）。
- 时区：展示日期用 CST=UTC+8（72,264-266,1282），统计小时也 +8（866-867）；`start`/`end` 由 ISO 串转换（352-353）。
- 帮助卡 `render_text_card` 是惰性 import（950-955），失败降级纯文字（1162）；COMMANDS.md:195 记"纯文字帮助"已滞后，以代码 1152-1164 的"优先图卡"为准。

## 8. 代码依据
`main.py:55-72`（根路径/数据常量）、`main.py:93-130`（字体/环境变量/access import）、`main.py:133-155`（声明与 COMMANDS）、`main.py:163-236`（时间/类别/省市词表）、`main.py:215-221`（`expand_place`）、`main.py:269-276`（卡缓存路径）、`main.py:313-403`（`fetch_events`）、`main.py:406-410`（`pick_next`）、`main.py:424-487`（`render_next`）、`main.py:558-571`（`_full_name`）、`main.py:643-922`（`render_recent` / `render_city` / `fortune_of` / `render_fortune` / `group_stats` / `render_stats`）、`main.py:925-955`（帮助文案与惰性图卡）、`main.py:958-981`（`group_enabled` / `set_group_enabled`）、`main.py:984-1037`（`match_command`）、`main.py:1048-1256`（`handle`）、`main.py:1258-1313`（定时播报）；`metadata.yaml:4`；`access/main.py:45-54,100-125,316-361`、`access/card_render.py:1-4,21-28`；`COMMANDS.md:10-48,196-203,302-307`。
