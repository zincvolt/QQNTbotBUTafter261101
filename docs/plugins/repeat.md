# astrbot_plugin_repeat — 与其他插件的接口
> 源码：`apps/AstrBot/data/plugins/astrbot_plugin_repeat/`
> 版本：1.0.0（metadata.yaml）  分类：自写

## 1. 职责一句话
群里同一句纯文本在相邻 `window` 秒内连刷到 `threshold` 条且来自 `min_senders` 个不同的人时，原样复读一次并 `stop_event`，用 `cooldown` 防止同一句反复复读。

## 2. 注册的钩子

| 钩子 | 优先级 | 触发时机 | 实际行为 |
|---|---|---|---|
| `@filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE, priority=maxsize-1)` `echo`（`main.py:115-119`） | 源码声明 `maxsize-1`；**实际被 access 重排为 `LISTENER_BAND = maxsize-100`**（`access/main.py:316-359`，仅重排 `AdapterMessageEvent`） | 每条群消息 | 纯文本连续计数；达标 `await event.send(event.plain_result(text))` 原文复读一次 + `event.stop_event()`（`main.py:180-181`）；不写 `event.set_extra`、不改 prompt、不落库 |

> 无其他钩子、无斜线指令：`DECLARED_COMMANDS = {}`，`DECLARED_BEHAVIOR` 声明被动行为（`main.py:43-45`）。副作用：发消息 = 是；`stop_event` = 是（仅命中复读时）；写历史/写文件 = 否。

## 3. 输入（别人给它什么）

**事件字段**：`event.get_messages()` 逐个取 `Plain.text` 拼成文本，任何非 `Plain` 组件直接返回空串（`_pure_text`，`main.py:105-113`）；`event.get_group_id()` 查 `disabled_groups`（`main.py:125-128`）；`event.get_sender_id()` 与 `event.get_self_id()` 比对，跳过机器人自己（`main.py:137-139`）；`event.unified_msg_origin` 作 `_state`/`_echoed` 键（`main.py:141`）；`event.message_str` **未使用**（文本只来自消息链里的 `Plain`）。

**`event.get_extra` 键**：无。源码未出现 `event.get_extra(...)` 调用，不消费 basicZ 的 busy 标记、判官的 `vision_judge_wake` 或其他插件的 extra 键（**待确认**：框架侧是否透传——未发现读取路径）。

**读的配置文件**：插件自身目录 `repeat.json`（`CONFIG_PATH = Path(__file__).resolve().parent / "repeat.json"`，`main.py:47`），`utf-8`（**非 `utf-8-sig`**），文件缺失用默认值，损坏/类型不对 WARN 后回落默认值（`main.py:60-78`）；`_config()` 按 mtime 缓存，改文件不用重启（`main.py:94-103`）。键：`enabled/threshold/window/cooldown/min_senders/max_len/disabled_groups`，默认 `true/3/240/300/2/60/[]`（`main.py:49-57`）。

**数据库表 / 外部服务**：无。不读 `data_v4.db`，不调任何 HTTP。

**其他插件直接调用**：无公开 API；`load_config()` 是模块级函数，仓库内无其他插件 import 记录；`_config`/`_pure_text` 为内部方法。

## 4. 输出（它给别人什么）

**`event.set_extra` 键与值**：无。

**改写 `req.system_prompt` / `req.prompt`**：无。本插件不挂 `on_llm_request`，不碰 `ProviderRequest`。

**注入上下文内容**：无。复读发出的是一条独立 `plain_result`，不是上下文注入。

**`stop_event`**：复读命中后 `event.stop_event()`（`main.py:181`），阻断同一事件上后续处理器（basicZ 闸门、判官/主动回复、其他纯监听）继续产生第二条回复。

**发消息**：`await event.send(event.plain_result(text))`，`text` 就是累计的原文（不做任何改写），并打 `[repeat] echo ...` 日志（`main.py:180-182`）。未达阈值时只写进度日志（`main.py:162-169`），不发消息。

**写数据库 / 文件**：无。状态全在内存：`_state[umo] = {"text","count","senders","ts"}` 与 `_echoed[umo] = (text, ts)`（`main.py:86-89,157,178`）。

**面板接口**：无。dashboard 未引用 `repeat.json`（`dashboard/app.py` 中无该路径），配置只能手工编辑插件目录里的文件。

**下游消费者**：仅 AstrBot 事件链——`stop_event` 决定 basicZ/判官是否还会补一句；复读消息本身对模型不可见（不进对话历史）。

## 5. 与其他插件的协作关系

| 对方 | 关系 | 契约/约定 |
|---|---|---|
| `astrbot_plugin_access` | 优先级被统一仲裁 | access 加载/`on_astrbot_loaded` 时把 `AdapterMessageEvent` handler 重排：gate=`maxsize`、指令类=`maxsize-10`、纯监听=`maxsize-100`（`access/main.py:45-47,316-359`）；repeat 属纯监听，源码注释里的 `maxsize-1` 实际失效，原相对顺序在**同档内**保持稳定（`access/main.py:320-321`） |
| `astrbot_plugin_basicz` 刷屏防护 | 防「复读 + 聊天」双回复 | repeat 命中即 `stop_event`，basicZ 的 `on_waiting_llm_request` gate（`basicz/main.py:1493`）不再触发；basicZ 自身另有 `_busy` / `COOLDOWN_SECONDS` / `MAX_CONCURRENT`（`basicz/main.py:1538-1560`），与 repeat 的 `cooldown` 是两套独立计数，互不读写 |
| `astrbot_plugin_furcon` | 指令优先、备注已过时 | repeat 源码注释称留一档给 furcon 的 `maxsize` 先判展会（`main.py:28-29`）；当前 furcon 用 `@filter.event_message_type(ALL)` 无自报优先级（`furcon/main.py:1059`），由 access `_CMD_LISTENER_MODS` 放进 `CMD_BAND = maxsize-10`（`access/main.py:50-54,349-350`），始终早于 repeat |
| dice / ltm / 所有指令插件 | 指令路由不冲突 | 斜杠命令由 access 闸门 CMD_BAND 先消费并 stop；repeat 不注册 `command`，且文本以 `/` 或 `／` 开头直接 return（`main.py:134`），不会复读 `/r`、`/记忆` 等；含 `&&`/`$$` 的内部表情语法也跳过（同行） |
| 判官 / `group_chat_context` | 同档纯监听 | 判官也在 LISTENER_BAND，repeat 命中后 `stop_event` 使其不再补话；未命中时两者各走各的，先后取决于同档注册顺序——**待确认** |
| 私聊插件（`private_settle`） | 无交集 | repeat 只注册 `GROUP_MESSAGE`，私聊消息完全不进本插件；反之私聊合并也不影响群复读计数 |

## 6. 配置与数据文件

| 路径 | 用途 | 谁写 | 谁读 |
|---|---|---|---|
| `apps/AstrBot/data/plugins/astrbot_plugin_repeat/repeat.json` | 阈值/相邻窗口/冷却/人数门槛/最大长度/禁用群 | 人工编辑（无面板入口） | 本插件 `load_config()`，经 `_config()` 按 mtime 刷新 |
| 无数据库 / 无状态文件 | `_state` / `_echoed` 全在内存 | 本插件进程 | 本插件进程（重启即清零，计数与冷却都不持久） |

## 7. 顺序、坑与边界
- **优先级声明 ≠ 实际**：`maxsize-1` 是源码里的旧假设；access 把纯监听统一压到 `maxsize-100`（`access/main.py:316-359`）。排查「复读抢了判官/指令」要先看 access 分档，不要只看本文件注释。
- `window` 是**相邻两条**之间的间隔，不是从第一条起算；默认 240s，源码注释记过 32s+143s 三连在 120s 窗口下漏判的实测（`main.py:7-9,144`）。
- 只认纯文本：图片、语音、引用等任何非 `Plain` 组件让整条消息不参与（`main.py:105-113`）；`max_len=60` 以上的长文本也不参与。
- 人数门槛 `min_senders=2`：同一个人刷满 `threshold` 也不复读（日志 `need N — 一个人刷屏不算复读`，`main.py:164-169`）。
- 冷却 `_echoed` 按 `umo + 文本` 记，默认 300s（`main.py:171-178`）；先落状态再 `await event.send`，并发下也只有第一条能走到发送（`main.py:175`）。
- 达标后 `count` 清零、`senders` 清空（`main.py:176-177`），不保留半截链；同句超窗口会打 `chain broken` 日志再重新起链（`main.py:148-155`）。
- BOM：`read_text(encoding="utf-8")` 而非 `utf-8-sig`（`main.py:68`），手工存的带 BOM JSON 会解析失败并静默回落默认值——改配置后注意日志里有没有 `[repeat] repeat.json 读不了`。
- 静默失败：文件缺失/损坏/类型不对均回落默认值，只 WARN 不发消息（`main.py:67-78`）；配置里没有 `enabled` 之外的值做范围校验（**待确认**：`threshold/window` 等非法值可能直接参与比较）。
- 升级：本插件是本地自写目录，AstrBot 升级不覆盖；但 `repeat.json` 与插件同目录，手工替换插件目录时会被一起覆盖（**待确认**：无独立仓库同步记录）。

## 8. 代码依据
`main.py:1-30`（设计说明/优先级注释）、`43-57`（声明与默认值）、`47`（CONFIG_PATH）、`60-103`（load_config/_config mtime 缓存）、`105-113`（_pure_text）、`115-182`（echo 全钩子：过滤/计数/门槛/冷却/发送/stop_event）；交叉核对 `access/main.py:42-54,316-359`、`basicz/main.py:1487-1560`、`furcon/main.py:1059-1061`、`group_chat_context.py:514-515,826`、`dashboard/app.py:58-59`（无 repeat 配置路径）。
