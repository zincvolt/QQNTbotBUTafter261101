# 模块开发指南

> 本项目的"模块"就是 AstrBot 插件。这份文档讲清楚：一个模块长什么样、能挂在哪、怎么调试、怎么把新的判断条件加进群聊决策。
> 目录约定：`D:\QQNTBOT\apps\AstrBot\data\plugins\<插件名>\`

---

## 1. 最小可运行模块

```
plugins\my_module\
├─ metadata.yaml      # 元信息（控制台"已装模块"就是读它）
└─ main.py            # 入口，必须定义 Main(star.Star)
```

`metadata.yaml`：

```yaml
name: my_module
desc: 一句话说明这个模块干什么
author: local
version: 1.0.0
```

`main.py`：

```python
from astrbot.api import logger, star
from astrbot.api.event import AstrMessageEvent, filter


class Main(star.Star):
    def __init__(self, context: star.Context) -> None:
        self.context = context
        logger.info("[my_module] loaded")

    @filter.on_astrbot_loaded()
    async def on_ready(self) -> None:
        """AstrBot 启动完成后调用一次。"""
        logger.info("[my_module] ready")
```

放好文件后重启 AstrBot（**不要重启 QQ**）：

```powershell
D:\QQNTBOT\scripts\restart-astrbot.ps1
```

日志里出现 `[my_module] loaded` 就成了。控制台「已装模块」也会立刻显示。

---

## 2. 可用的钩子

| 装饰器 | 时机 | 典型用途 |
|---|---|---|
| `@filter.on_astrbot_loaded()` | 启动完成 | 起后台任务、初始化 |
| `@filter.on_llm_request()` | 调模型前 | 往 `req.system_prompt` 注入记忆/搜索结果 |
| `@filter.on_llm_response()` | 模型返回后 | 后处理、学习、统计 |
| `@filter.on_decorating_result()` | **发送前** | 改文案、掐掉整条回复 |
| `@filter.command("名字")` | 收到 `/名字` | 用户指令 |
| `@filter.llm_tool(name="xxx")` | 模型主动调用 | 给模型加工具 |
| `@filter.event_message_type(...)` | 每条消息 | 记录、过滤 |
| `@filter.after_message_sent()` | 发送后（**所有分段发完之后**） | 回执、日志；判官的「在途锁」靠它收敛成真实发完时刻 |

### 各钩子的签名

```python
@filter.on_llm_request()
async def hook(self, event: AstrMessageEvent, req: ProviderRequest) -> None:
    req.system_prompt += "\n额外上下文"

@filter.on_llm_response()
async def hook(self, event: AstrMessageEvent, resp: LLMResponse) -> None:
    text = resp.completion_text

@filter.on_decorating_result()
async def hook(self, event: AstrMessageEvent) -> None:
    result = event.get_result()
    result.chain.clear()      # 清空 = 这条不发了
    event.stop_event()

@filter.command("记忆")
async def cmd(self, event: AstrMessageEvent):
    yield event.plain_result("回复内容")
```

### event 上最有用的几个方法

| 方法 | 说明 |
|---|---|
| `event.message_str` | 纯文本内容（已去 @） |
| `event.get_sender_id()` | 发送者 QQ 号 |
| `event.get_group_id()` | 群号（私聊为空） |
| `event.unified_msg_origin` | 会话唯一标识，如 `qq:GroupMessage:1154487120_1128093050` |
| `event.get_message_type()` | `GROUP_MESSAGE` / `FRIEND_MESSAGE` |
| `event.plain_result(text)` | 构造一条纯文本回复（配合 `yield`） |
| `event.stop_event()` | 终止后续处理 |

---

## 2.5 指令自声明（必备规范，2026-11-20 起强制）

**每个插件必须在 `main.py` 顶层声明自己的指令清单。** 这是插件加入统一权限管理（access 闸门）的前提：`/权限 列表` 的按插件分组图卡就是从这里自动读取的（ast 解析字面量，不执行插件代码）。

> 完整配套文档在权限插件目录内：指令管理指南 `apps/AstrBot/data/plugins/astrbot_plugin_access/COMMAND-GUIDE.md`，新插件部署指南同目录 `DEPLOY-GUIDE.md`。

### 有斜线指令的插件

```python
# 指令自声明：/权限 列表 按插件分组展示用（插件开发规范要求）
DECLARED_COMMANDS: dict[str, tuple[str, str]] = {
    "/指令 <参数>": ("一句话说明", "公开"),   # 级别：公开 / 管理 / 超管
    "/指令 子命令": ("一句话说明", "管理"),
}
```

- 键写**用户实际输入的完整形式**（带 `/`，带子命令和参数占位）
- 值是 `(说明, 级别)` 二元组；级别要与 access 权限表里该指令的级别一致
- 同义别名写进说明里即可（如 dice：`"掷骰（同义别名：roll/dice/骰/掷骰/投骰）"`），不用每个别名一条

### 无斜线指令的插件（纯被动行为）

```python
DECLARED_COMMANDS: dict[str, tuple[str, str]] = {}
DECLARED_BEHAVIOR = "无斜线指令：一句话说清被动行为（注入防护/复读/缓存等）"
```

### 规则

1. **新增插件必须带声明**——没有声明的插件会在 `/权限 列表` 图卡的「⚠ 未声明指令」节里被点名
2. **改了指令（增删改子命令）要同步改声明**，否则权限表展示过时
3. access 启动时自动扫描全部插件目录（`ast.literal_eval` 安全提取），无需注册
4. 声明的级别是展示口径；真正拦截以 access 权限表（`/权限 设置`）为准，两者别矛盾

---

## 3. 现有模块（照着抄最快）

| 模块 | 用到的钩子 | 干了什么 |
|---|---|---|
| `astrbot_plugin_peer` | `on_astrbot_loaded`、`on_decorating_result` | 载入人格、静默过滤、冷群水群 |
| `astrbot_plugin_ltm` | `on_llm_request`、`on_llm_response`、`on_astrbot_loaded`、`command` | 记忆注入、抽取、群历史扫描 |
| `astrbot_plugin_websearch` | `on_llm_request`、`llm_tool` | 自动检索 + 工具调用 |
| `astrbot_plugin_dice` | `command("r", alias=...)` | 桌游骰子，只输出随机数；精确指令、无全局处理器 |

**读代码顺序建议**：`peer/main.py`（最短，看人格与静默）→ `websearch/main.py`（看请求注入）→ `ltm/main.py`（看后台任务与存储）。

---

## 4. 改"要不要接话"的三种姿势

群聊决策链**按模式分两套**，改之前先确认当前是哪一套（`is_third_party_mode()` 读的就是 AstrBot 的 `provider_id`）：

```
群消息 → 白名单 → @ / 唤醒前缀？
                    ├─ 是 → AstrBot 内置回复通道（不经过判官！）
                    │         └─ 第三方模式：on_req_llm 里还挡一道「在途硬锁」
                    └─ 否 → need_active_reply()
                              ├─ 本地模式（local-llama）：
                              │    judge.json 规则 → 8082 小模型 → 概率闸
                              └─ 第三方模式（deepseek 等）：
                                   话段聚合 → 规则层 → 省 token 复用
                                   → 第三方判官 API → 可选概率闸
```

两个容易踩的点：

- **@ 它和唤醒前缀不走判官**（`need_active_reply` 第一句就 `return False`）。想约束这条路径，只能加在 `on_llm_request`。
- **本地模式不读 `judge_api.json`**，第三方模式才启用话段聚合和在途硬锁；改判官逻辑时不要把两套混在一起。

第三方判官的完整行为规格（判定顺序、话段聚合、在途硬锁三层、强触发分工、日志与调参）见 `docs\THIRD-PARTY-API.md` §14，或插件仓 `astrbot-plugin-apimode` 的 README「判官模块（描述文档）」。

### 姿势一：加关键词（不改代码，最快）

控制台「判官」页 → 必答关键词 / 免打扰关键词，一行一个。保存即生效，**不用重启**。

- 必答：消息含该词 → 一定回（比如 `bot`、`阿灰`）
- 免打扰：消息含该词 → 一定不回（比如 `刷屏`、`广告`）

判断顺序：**免打扰优先于必答**。

### 姿势二：改判官提示词（不改代码）

控制台「判官」页的文本框。要求：

- 必须保留 `{message}`（新消息）
- `{recent}` 可选（最近聊天上下文）
- 结尾要求模型只输出 `1` 或 `0`

改完点"保存判官"，下一条群消息生效。旁边的"试判"可以立刻验证效果，不用真的去群里发。

### 姿势三：写插件接管判断（要写代码）

在内置判官之前插入自己的规则，最省事的做法是在 `on_llm_request` 里读配置：

```python
@filter.on_llm_request()
async def gate(self, event, req):
    text = event.message_str
    if "抽奖" in text:
        event.stop_event()          # 直接不处理
```

更彻底的做法是改 `need_active_reply`（见第 6 节），但那是 AstrBot 源码补丁，升级会丢。

---

## 5. 判官配置：两份文件，别搞混

| 文件 | 谁读 | 用在 | 管什么 |
|---|---|---|---|
| `data\judge.json` | `load_judge_config()` | 本地模式 | 提示词 + 必答/免打扰/召唤词，交给 8082 小模型 |
| `data\judge_api.json` | `load_judge_api_config()` | **仅第三方模式** | 独立密钥/模型、短提示词、日限额、话段聚合、在途硬锁 |

`judge.json`：

```json
{
  "prompt": "……\n最近聊天：\n{recent}\n\n新消息：{message}\n\n只输出 1 或 0。",
  "force_reply": ["bot", "阿灰"],
  "ignore": ["刷屏", "广告"]
}
```

- 由 `builtin_stars\astrbot\group_chat_context.py` 的 `load_judge_config()` 读取，按文件 mtime 缓存
- 缺文件 / 格式错 → 回退到代码里的默认提示词
- 提示词里没有 `{message}` → 也回退，避免写出无效配置

`judge_api.json`：字段较多（`burst_*` / `inflight_lock` / `bot_names` / `break_words` 等），完整清单见插件仓的 `judge_api.example.json` 与 README。改完即生效，不需要重启；控制台「判官」页写的就是这份文件（合并写入，只覆盖请求里真带了的字段）。

---

## 6. 本项目对 AstrBot 源码的补丁（升级会覆盖）

| 文件 | 改了什么 |
|---|---|
| `core\pipeline\whitelist_check\stage.py` | 未授权私聊自动回一句"未授权…" |
| `core\pipeline\respond\stage.py` | 新增 `human` 分段间隔算法（按字数模拟打字） |
| `builtin_stars\astrbot\group_chat_context.py` | 群上下文注入 + 判官两套判定（`judge.json` 本地 / `judge_api.json` 第三方）、话段聚合、在途硬锁 |

完整清单（含 `core\updater.py` 禁自动升级）见 `docs\PROJECT.md` §14，那是唯一的补丁真相。重装 AstrBot 后要按它逐处重打；升级后如果 `git diff` 里看不到这些改动，说明补丁已经被冲掉了。

---

## 7. 开发流程与调试

```powershell
# 1. 改完先做语法检查（必做）
D:\QQNTBOT\apps\AstrBot\.venv\Scripts\python.exe -m py_compile <文件路径>

# 2. 只重启 AstrBot（QQ 不用动，不掉登录）
D:\QQNTBOT\scripts\restart-astrbot.ps1

# 3. 看日志
Get-Content D:\QQNTBOT\apps\AstrBot\data\logs\astrbot.log -Tail 40
```

控制台 `http://127.0.0.1:6190` 的「运行日志 → AstrBot」是同一个文件。

**查数据库**（只读，别写）：

```powershell
$py = 'D:\QQNTBOT\apps\AstrBot\.venv\Scripts\python.exe'
& $py -c "import sqlite3;c=sqlite3.connect(r'file:D:\QQNTBOT\data\memory.db?mode=ro',uri=True);print(c.execute('select uid,text from facts order by created desc limit 5').fetchall())"
```

---

## 8. 踩过的坑（务必避开）

1. **不要用 PowerShell 的 `Set-Content` / `-replace` 改带中文的 Python 文件**
   PS 5.1 会按 ANSI 读 UTF-8，把中文写成乱码，`py_compile` 直接报 `unterminated string literal`。
   → 用编辑工具直接写文件，或 `[System.IO.File]::WriteAllText($path, $text, (New-Object System.Text.UTF8Encoding $false))`

2. **文件必须是 UTF-8 无 BOM**
   LiteLoader / JSON 解析对 BOM 敏感，脚本也一样。

3. **插件 `__init__` 里不要做耗时操作**
   会卡启动。要跑循环用 `asyncio.create_task()` 放在 `on_astrbot_loaded` 里。

4. **`on_decorating_result` 里想取消发送**
   必须同时 `result.chain.clear()` **和** `event.stop_event()`。

5. **日志走 `logger`，别用 `print`**
   `print` 进不了 `astrbot.log`，控制台看不到。

6. **不要在插件里直接写 AstrBot 的数据库**
   用 `?mode=ro` 只读打开；要写就写自己的库（本项目写在 `data\memory.db`）。

7. **新指令别抢别人的斜杠命令**
   只注册精确的 `@filter.command("名字")`，匹配上再 `stop_event()`；不要为了
   「智能一点」注册 `event_message_type(ALL)` + 模糊兜底。兽聚插件曾用「带地名
   就当展会查询」吞掉过别的 `/` 指令，修了很久。骰娘插件是反面教训的正例：
   6 个精确别名、没有全局 handler、解析失败也只回提示。

---

## 9. 想加的功能该写在哪

| 想做的事 | 写在哪 |
|---|---|
| 新的聊天指令（`/xx`） | 新插件，`@filter.command` |
| 新的自动回复规则 | `judge.json` 关键词，或插件的 `on_llm_request` |
| 给模型加工具（查天气、查库） | 新插件，`@filter.llm_tool` |
| 改回复风格/长度 | `data\persona.json` + 控制台 max_tokens |
| 换模型 | `cmd_config.json` → `provider[0].model` |
| 加后台定时任务 | 插件的 `on_astrbot_loaded` + `asyncio.create_task` |
