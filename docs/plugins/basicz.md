# astrbot_plugin_basicz — 与其他插件的接口
> 源码：`apps/AstrBot/data/plugins/astrbot_plugin_basicz/`
> 版本：2.0.0（metadata.yaml）  分类：自写

## 1. 职责一句话
群聊基础行为层：把 persona.json 落到数据库人格行、决定要不要开口（注入防护/刷屏闸/自动冒泡开关）、按模式处理图片输入输出，并在回复装饰阶段做标记归一、表情附带与文本替换。无斜线指令，全被动。

## 2. 注册的钩子

| 钩子 | 优先级 | 触发时机 | 实际行为 |
|---|---|---|---|
| `@filter.on_waiting_llm_request()` → `gate`（main.py:1493-1494） | 无显式 priority；PROJECT.md:386 记载 private_settle 用 `priority=maxsize` 抢在其前 | 消息等待进入 LLM 队列时 | 斜杠消息直接 `stop_event()`（main.py:1500-1513）；注入防护命中 `stop_event()`（1515-1519）；「要表情包」发图成功后 `stop_event()`（1521-1525）；@/唤醒但 `auto_chat` 关 → `stop_event()`（1527-1536）；本会话 busy / 冷却 / 全局并发上限 → `stop_event()`（1538-1557）；放行的自动接话占槽 `_busy[umo]`（1559-1560）。 |
| `@filter.on_llm_response()` → `release_after_reply`（main.py:1562-1563） | — | LLM 回复产出 | `_release(umo)` 清 busy 槽并记 `_last_done`（main.py:1487-1491）。 |
| `@filter.after_message_sent()` → `release_after_send`（main.py:1567-1568） | — | 分段发送全部完成后 | 同上，安全网，避免只生成未发送时漏释放。 |
| `@filter.on_astrbot_loaded()` → `start_watch`（main.py:1572-1573） | — | AstrBot 加载完成 | 起 `_idle_loop()` 每分钟扫一次冷群（1626-1664）；注册 aiocqhttp `group_increase` 欢迎监听（1580-1624），开关读 access 的 `group_flags.welcome`，文本用 `WELCOME_TEXT`。 |
| `@filter.on_llm_request()` → `log_system_prompt`（main.py:1777-1778） | — | LLM 请求组装 | 改 `req.system_prompt`：转发消息占位说明（1786-1796）、群聊格式说明（1954-1959）；改 `req.prompt`：图片释义 / 跨轮图简述 / 说话人前缀（1835,1880,1905,1927-1937,1951-1953）；改 `req.image_urls`：本地模式全剥（1806）、第三方按需保留 ≤2 张并转 base64（1885-1894）。不 stop_event，不改工具列表。 |
| `@filter.on_decorating_result()` → `decorate_result`（main.py:1966-1967） | — | 回复装饰阶段 | 空/None 回复清空 `result.chain` + `stop_event()`（1980-1985）；`&&...&&` 标记挪句末（1986-1990）；按 `meme_chance` 概率附图（1992-1993）；按 `text_rules` 正则替换（1994-2003）。 |

## 3. 输入（别人给它什么）

- **事件字段**：`unified_msg_origin`、`message_str`、`message_obj.raw_message`、`is_at_or_wake_command`、`get_group_id()` / `get_sender_id()` / `get_sender_name()`、`get_messages()`（判 Forward，main.py:1786-1796）、`get_result()`（main.py:1973-1977）。
- **`event.get_extra` 键**：无（本文件无 get_extra/set_extra）。
- **读的配置文件/数据库**：`persona.json`（main.py:32,192-211，取 `text`）；`water.json`（67,156-190，取 `idle_min`）；`reply.json`（235,239-266，utf-8-sig，取 `meme_chance`/`text_rules`）；access 的 `group_flags.json`（73-119，只读）；`cmd_config.json`（303-309,441-452,1248-1262,1275-1295，取白名单、`provider_id`）；`api_mode.json`（455-460，mode 兜底）；`vision_mode.json`（849-864,927-933，mode/port）；`vision_cache.db`（983-1029，captions 表）；`meme_manager/furry/manifest.json`（689,694-718）；meme 包目录（410,1676-1693,1740-1762）。
- **外部 HTTP**：本地 VL `http://127.0.0.1:<port>/v1/chat/completions`（909-977，端口来自 vision_mode.json，默认 8085）；`_pin_image` 下载远程图（626-634）。
- **其他插件直接调用**：本插件顶层函数仅供内部使用，全仓未见外部 import（**待确认**）。反向依赖：import access 的 `WELCOME_TEXT`（main.py:42）。

## 4. 输出（它给别人什么）

- **`event.set_extra` 键与值**：无。
- **改写 req.system_prompt**：追加转发占位说明、群聊格式说明（main.py:1789,1955-1959）。
- **改写 req.prompt**：追加图片内容/「没看图」提示/跨轮图简述/「你刚才发的表情包」/说话人前缀（main.py:1835,1880,1905,1927-1937,1951-1953）。
- **改写 req.image_urls**：本地模式清空（main.py:1806）；第三方模式按需保留 ≤2 张并转 `data:` base64（main.py:1885-1894）。
- **工具列表**：不改。
- **`stop_event`**：gate 各拦截分支 + 空回复整条丢弃（main.py:1512,1518,1524,1533,1543,1550,1556,1984）。
- **发消息**：`event.send(image_result)` 直接发表情（1695）；`context.send_message(umo, MessageChain([Plain(line)]))` 发冷场暖场话（1658）；aiocqhttp `bot.call_action("send_group_msg", ...)` 发进群欢迎（1611-1618）；`result.chain.append(Image...)` 给回复附带表情（1764）。
- **写文件**：`data_v4.db` 的 `personas` 表（`grey` 与 `default` 两行 system_prompt，main.py:214-231）；`vision_cache.db.captions`（1355-1380,1408-1434）；`data/temp/peer_recent/` 图片快照（585,604-665）。
- **面板/HTTP 接口**：无；人格/文本规则由外部 dashboard 写 persona.json / reply.json。人格文本本身不复述，来源即 persona.json。

## 5. 与其他插件的协作关系

| 对方 | 关系 | 契约/约定 |
|---|---|---|
| access | 单向依赖 | import `WELCOME_TEXT`（main.py:42）；只读 access 写的 `group_flags.json`（73-75）；`auto_chat` 关时连 @/唤醒也被 gate 丢掉（1530-1534）。 |
| apimode | 文件耦合，无 import | apimode 写 reply.json / cmd_config.json / vision_mode.json，basicz 读；双方都独立以 `provider_id` 含 `deepseek` 判模式（basicz/main.py:430-461）。 |
| meme_manager | 数据与格式契约 | 读其 `packs/furry/manifest.json` 取分类描述（689）、`packs/furry/memes` 取图（410）；`&&分类&&` 标记被挪到句末以配合其标记模式（1437-1460,1986-1990）。 |
| vision_context | 共享识图缓存 | basicz 读写 `data/vision_cache.db.captions`（983-1029）；按 cmd_config 白名单判断后台识图是否会写（1235-1295），等待窗口 local 9s / third_party 4s（479-484,1298-1352）。代码注释称与 vision_context 同规则、两边独立实现（1178）。 |
| private_settle | 钩子顺序 | 据 PROJECT.md:386 其 `on_waiting_llm_request(priority=maxsize)` 抢在 basicz gate 之前合并话段；basicz 源码未见对应 extra 键交互，交接细节**待确认**。 |

## 6. 配置与数据文件

| 路径 | 用途 | 谁写 | 谁读 |
|---|---|---|---|
| `data/persona.json` | 人格文本（不复述内容） | dashboard | basicz `__init__` → data_v4.db |
| `data/reply.json` | meme_chance / text_rules | dashboard、apimode 切换 | basicz |
| `data/water.json` | 每群 `idle_min` | dashboard | basicz（`enabled` 已废弃） |
| `astrbot_plugin_access/group_flags.json` | auto_chat / warmup / welcome | access、dashboard | basicz（只读） |
| `cmd_config.json` | provider_id、白名单 | WebUI、access、apimode | basicz |
| `data/api_mode.json` | mode 兜底 | apimode | basicz `_third_party_mode` 兜底 |
| `data/vision_mode.json` | 识图 mode / port | apimode、visionmode、dashboard | basicz |
| `data/vision_cache.db` | 图片释义缓存 | basicz、vision_context | basicz |
| `apps/AstrBot/data/data_v4.db` | `personas.system_prompt` | basicz（`grey`/`default` 两行） | AstrBot 主模型 |
| `data/temp/peer_recent/` | 图片快照 | basicz | basicz 跨轮追问 |

## 7. 顺序、坑与边界

- 本地 9B 不支持图片，本地模式直接剥掉 `req.image_urls`（1804-1806）；第三方保留，但只在明确问图 / 带问号 / ≥3 张 / 大图 / @ 带图时才送（511-544,1808-1821）。
- 跨轮图片记忆 `_RECENT_IMAGE` 是纯内存（687-766），重启即丢；先把图快照进 peer_recent 再记路径，因为 QQ 的 `file://` 临时文件几十秒失效（604-665）。
- 人格只读 persona.json 的 `text`，读不到就跳过、不用默认值（192-211），避免旧硬编码人设冲掉控制台设置；写库同时覆盖 `grey` 和 `default`（214-231）。
- BOM：reply.json / cmd_config.json 用 `utf-8-sig`（254,441,1256,1283）；persona / group_flags / water / api_mode / vision_mode 用 `utf-8`。
- 「要表情包」是硬拦截：命中 `MEME_REQUEST` 且发图成功才 stop_event（1521-1525）；发图失败会继续进模型。
- 表情概率与文本规则来自 reply.json，第三方模式下 apimode 会置 0 / 清空（apimode/main.py:328-332），表现为「第三方没表情没波浪号」，改动前先看是谁写的。
- 冷场暖场话只在 9–23 点、白名单群、warmup 开、空闲 ≥ idle_min 且 40 分钟节流时才发（1626-1664）；它是插件主动消息，不进对话历史、不计入判官冷却。
- `none`/`null`/`nan`/空文本回复会被整条清空并 stop_event（1980-1985），其他插件若靠空文本触发后续逻辑会被误杀。
- AstrBot 升级覆盖 core 补丁时（PROJECT.md:434-445），`on_waiting_llm_request`/`after_message_sent` 等钩子的触发点需重验。

## 8. 代码依据
`main.py:31-143`（路径与 access 依赖）、`main.py:156-309`（water/persona/reply 与群活动读取）、`main.py:410-461`（meme 目录与模式判定）、`main.py:511-544`（读图判定）、`main.py:585-766`（图片快照与跨轮记忆）、`main.py:849-977`（识图模式与本地 VL）、`main.py:983-1460`（缓存、标记归一）、`main.py:1463-1624`（类、gate、释放、欢迎）、`main.py:1626-1775`（水群与发图）、`main.py:1777-2003`（log_system_prompt 与 decorate_result）。
