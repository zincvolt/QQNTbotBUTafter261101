# astrbot_plugin_dice — 与其他插件的接口
> 源码：`apps/AstrBot/data/plugins/astrbot_plugin_dice/`
> 版本：1.0.0（metadata.yaml）  分类：自写

## 1. 职责一句话
零配置桌游骰子：只注册精确指令 `/r`（含 5 个别名），按骰式输出一行随机数，不调模型、不抢别的指令、不记录任何状态。

## 2. 注册的钩子

| 钩子 | 优先级 | 触发时机 | 实际行为 |
|---|---|---|---|
| `@filter.command("r", alias=ALIASES, priority=maxsize)` → `roll_command`（main.py:62-79） | 源码 `priority=maxsize`；运行时被 access `_enforce_bands` 归到 `CMD_BAND = maxsize-10`（access/main.py:45-46,341-355） | 仅 `/r`、`/roll`、`/dice`、`/骰`、`/掷骰`、`/投骰` 完整命中；别名集合见 main.py:40 | `_expr_from_event` 取第一个空格后的骰式（50-56）；空骰式 → stop_event + `USAGE`（66-69）；`dice_core.roll(expr)` 成功 → stop_event + 一行结果（71,78-79）；`DiceError` → stop_event + 「骰子没读懂」+ `USAGE`（72-76）。 |

没有 `event_message_type(ALL)`、没有正则兜底、没有 `on_llm_request` / `llm_tool` / `on_astrbot_loaded`；这是刻意的防抢指令设计（main.py:3-7）。

## 3. 输入（别人给它什么）

- **事件字段**：`event.get_message_str()`（53，`_expr_from_event` 用 `re.sub(r"\s+", " ")` 规整后取 `split(" ", 1)[1]`）；其余事件字段未使用。
- **`event.get_extra` 键**：无（两个 .py 均无 `get_extra` / `set_extra`）。
- **读的配置文件/数据库**：无。零配置——没有 json、没有管理员开关、不记录状态（main.py:22）。
- **外部 HTTP**：无。随机数用 `random.SystemRandom()`（dice_core.py:151），纯本地。
- **其他插件直接调用**：`dice_core` 的 `DiceError` / `USAGE` / `roll` 仅被本插件 `main.py:33` import；全仓 grep 未见其他插件调用（`parse` / `roll` 的仓外单测调用**待确认**）。`roll(expr, rng=None)` 的 `rng` 可注入以便测试（dice_core.py:148-151）。
- **权限来源**：access 的 `cmd_perm.json` 中 `r`/`roll`/`dice`/`骰`/`掷骰`/`投骰` 默认 user 级（access/main.py:100-102），闸门在派发前判定，本插件不直接读该文件。

## 4. 输出（它给别人什么）

- **`event.set_extra` 键与值**：无。
- **LLM 工具**：无（不注册工具，模型不参与）。
- **改写 prompt**：无。
- **`stop_event`**：三个分支全部 stop_event（67 / 74 / 78）；命中后复读机、判官、大模型都不会再补一句（main.py:58-61 注释）。不命中时框架根本不会激活这个 handler。
- **发消息**：`event.send(event.plain_result(...))`——用法提示（68）、解析错误（75）、结果（79）；结果格式 `🎲 {表达式} = {逐项式} = {合计}`（dice_core.py:166），弃骰标 `(弃)`（143）。下游消费者：群里/私聊里的终端用户。
- **写文件**：无。
- **面板/HTTP 接口**：无。`DECLARED_COMMANDS`（36-38）供 access 的 `/权限 列表` 做 ast 扫描展示。

## 5. 与其他插件的协作关系

| 对方 | 关系 | 契约/约定 |
|---|---|---|
| access | 单向被仲裁 | 本插件在 `_CMD_LISTENER_MODS` 名单里（access/main.py:50-54），handler 被强制到 CMD_BAND；指令名默认 user 级（101-102）；命中后 stop_event 让后续监听 break（main.py:59-60）。 |
| furcon | 互斥、不重叠 | 只认精确指令名，不吞 `/下次展` 等（PLUGIN-COMMANDS.md:393-394）；没有"像掷骰就接管"的兜底。 |
| basicZ / 判官 / 复读机 | 钩子顺序 | stop_event 后这些监听不补话（main.py:58-61）；与 furcon 不同，本插件无 ALL 监听，不参与消息匹配竞争。 |
| 其他插件 | 无数据契约 | 无 set_extra、无 import、无共享文件（grep 验证）。 |

## 6. 配置与数据文件

| 路径 | 用途 | 谁写 | 谁读 |
|---|---|---|---|
| `astrbot_plugin_dice/main.py`、`dice_core.py`、`metadata.yaml` | 全部实现；无 json / 无状态文件 | 随插件发布 | AstrBot 加载 |
| `access/cmd_perm.json` | 6 个指令名的权限级别（默认 user） | access `/权限` 指令 | access 闸门（本插件不读） |
| `PLUGIN-COMMANDS.md` §9 | 指令文档（非运行依赖） | 人工维护 | 维护者 |

## 7. 顺序、坑与边界
- 防抢指令是刻意设计：只注册精确 `command`，无 ALL 监听、无正则兜底（main.py:3-7,62）；消息里含骰子字也不会接管。
- 源码 `priority=maxsize` 在 access 加载后失效：被 `_enforce_bands` 改写为 `maxsize-10`（access/main.py:320-355），实际与兽聚 handler 同档；access 未加载/升级失败时回落到 `maxsize`，仍高于判官/复读。
- 解析有界、不静默截断：表达式 64 字符 / 一次 100 颗 / 1000 面 / 修正 1000000 / 爆骰最多 20 次 / 总掷骰 200（dice_core.py:9-14,73-89,96-101,118-120）；超出走 `DiceError` 分支。
- 随机源 `random.SystemRandom()`（dice_core.py:151），同式不同次结果不同；单测可 `roll(expr, rng=...)` 注入（148）。
- 只 catch `DiceError`（72）；其他异常冒泡到框架（是否触发 creator 的日志告警**待确认**：creator 的 `WARN_PATTERNS` 不含骰子错误文本，main.py:74-79）。
- 指令名冲突：全仓仅本插件注册 `r`/`roll`/`dice`/`骰`/`掷骰`/`投骰`（grep 验证）；别名与 access 权限表需保持同步，新增别名要同时改 main.py:40 与 access/main.py:101-102。
- 不写文件、不读配置，因此没有合并写入/并发覆盖问题；`terminate()` 也未定义（无后台任务）。

## 8. 代码依据
`main.py:1-23`（设计说明）、`main.py:33`（dice_core import）、`main.py:36-40`（声明与别名）、`main.py:50-56`（`_expr_from_event`）、`main.py:62-79`（唯一钩子与三分支）；`dice_core.py:9-19`（上限与 USAGE）、`dice_core.py:22-27`（正则）、`dice_core.py:43-103`（`parse`）、`dice_core.py:106-145`（`_roll_term`）、`dice_core.py:148-166`（`roll` 与输出格式）；`metadata.yaml:4`；`access/main.py:45-54,100-102,316-361`（权限表与优先级覆盖）；`PLUGIN-COMMANDS.md:302-324`（指令表与防抢说明）。
