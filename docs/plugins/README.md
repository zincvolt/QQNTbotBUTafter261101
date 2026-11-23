# 插件接口文档索引

> 本目录回答一个问题：**某个插件怎么被别的插件用 / 它往外交什么数据 / 它注册哪些 AstrBot 钩子。**
> 面向维护者，按插件一份。分「自写」与「官方/内置」两类：**自写逐份写接口文档；官方/内置只在此登记，不展开。**

## 范围与口径

- **自写插件**（12 个）：`author: local` / `zincvolt`，本项目的核心逻辑，逐份建文档。
- **官方/内置插件**：只登记来源、版本、职责一句话，**不写接口文档**——它们随上游升级变动，且本项目不改其源码（meme_manager 的本地补丁例外，记在 [PROJECT.md §14](../PROJECT.md)）。
- 文档中「待确认」= 全仓 grep 未找到明确消费方/赋值点，不臆测。所有 `文件:行号` 均按核对时的源码，行号会随改动漂移，以源码为准。

---

## 一、自写插件（12 个，逐份文档）

| 插件 | 一句话职责 | 文档 |
|---|---|---|
| **access** | 统一斜线指令三档鉴权（公开/管理/超管）+ 加载时重排全部消息 handler 优先级；对外稳定契约 `unified_perm`、`card_render` | [access.md](access.md) |
| **apimode** | 本地/第三方模式切换与真相（`provider_id`）、token 额度闸、输出审查、provider 守护；靠改写配置文件与 basicz/判官耦合 | [apimode.md](apimode.md) |
| **basicz** | 群聊基础行为层：要不要开口 → 改 prompt 与图片 → 改回复；6 个钩子串成链，单向依赖 access | [basicz.md](basicz.md) |
| **creator** | 创造者专属通道：`tell_creator` 工具、日志监控、健康探测、好感度、主动搭话（全走创造者私聊） | [creator.md](creator.md) |
| **dice** | 骰娘：精确匹配 `/r`（5 个别名），`maxsize` 指令钩子三分支全 `stop_event`，纯函数掷骰 | [dice.md](dice.md) |
| **furcon** | 兽聚倒计时/活动/运势/统计卡片，自解析指令 + 定时播报，命中即发图不进模型 | [furcon.md](furcon.md) |
| **ltm** | 长期记忆：抽取/去重/过期清理/注入 `req.system_prompt`；私聊即时学、群聊扫 `data_v4.db` | [ltm.md](ltm.md) |
| **private_settle** | 私聊话段合并（1.0.2）：连发几条合成一条用户消息再回一次，等 `settle` + `min_gap`、`merge_window` 兜底；不送判官 | [private_settle.md](private_settle.md) |
| **repeat** | 复读机：群聊纯文本重复计数达标后原文复读 + `stop_event`，不落库无面板 | [repeat.md](repeat.md) |
| **vision_context** | 群图上下文：后台给白名单图生成文字描述（sha256 去重）写入 `captions`，回复时注入 `req.system_prompt` | [vision_context.md](vision_context.md) |
| **visionmode** | `/读图` 档位切换（local/third_party/off），唯一输出是覆盖写 `data/vision_mode.json` | [visionmode.md](visionmode.md) |
| **websearch** | `web_search` LLM 工具 + 自动搜索，依赖本地 SearXNG（9000），失败静默降级 | [websearch.md](websearch.md) |

## 二、官方 / 内置插件（登记，不写接口文档）

| 插件 | 来源 | 版本 | 职责 | 本项目关系 |
|---|---|---|---|---|
| **meme_manager** | anka（`anka-afk/astrbot_plugin_meme_manager`） | 5.4.1 | 表情包管理、智能发送、语义检索、WebUI 图库 | 官方第三方插件，源码在 `data/plugins/`。本项目对它打过私聊策略补丁（见 [PRIVATE-CHAT.md §4](../PRIVATE-CHAT.md)、[PROJECT.md §14](../PROJECT.md)），升级会覆盖需重打；本目录不展开其接口 |
| **astrbot** | AstrBot Team（内置） | 4.4.0 | 框架内置基础能力 | `astrbot/builtin_stars/astrbot/`，随框架升级，不写文档 |
| **builtin_commands** | Soulter（内置） | 0.0.1 | 框架内置指令（如 `/reset`） | `astrbot/builtin_stars/builtin_commands/`，随框架升级，不写文档 |

> 另：判官 `group_chat_context.py` 是**框架内置模块**（非 Star 插件），本项目对其打过话段聚合/追文补丁，见 [PROJECT.md §14](../PROJECT.md) 与 [THIRD-PARTY-API.md §14.6](../THIRD-PARTY-API.md)。它不在插件文档范围，但被多份文档作为协作方引用。

---

## 三、跨插件契约速查

维护时最常问的几条「谁给谁什么」，集中在此（详见各文档 §3/§4/§5）：

| 契约 | 提供方 → 消费方 | 形态 |
|---|---|---|
| `unified_perm.get_level/is_admin/is_super/admin_qqs` | access → apimode/furcon/ltm/visionmode/creator | Python import（函数） |
| `card_render.render_text_card` | access → furcon | Python import（函数） |
| `WELCOME_TEXT` / `group_flags.json` | access → basicz / 框架判官 | import + 只读共享文件 |
| `vision_judge_wake` extra | 框架判官补丁 → vision_context | `event.get_extra` 布尔标记 |
| `captions` 表 (`vision_cache.db`) | vision_context ⇄ basicz / meme_manager | SQLite 共享表 |
| `vision_mode.json` | apimode / visionmode / dashboard → vision_context / basicz | 文件 + mtime 缓存（按 mtime 立即跟随） |
| `api_mode.json` / `reply.json` / `cmd_config.json` | apimode ↔ basicz / 框架判官 | 配置文件（真相是 `provider_id`） |
| 消息 handler 优先级分档 | access → 全体 Star 插件 | 加载时改写 `extras_configs["priority"]` 并重排 |
| 合并后的 `event.message_str` | private_settle → basicz / ltm / vision / 主模型 | 改写事件文本 + 图片链 |

## 四、钩子类型与优先级（速记）

- **指令钩子** `@filter.command(...)`：被 access 归到 `CMD_BAND = maxsize-10`，指令权限不足到不了 handler。
- **纯监听** `event_message_type(ALL/GROUP_MESSAGE)`：被 access 归到 `LISTENER_BAND = maxsize-100`，始终晚于指令。
- **响应阶段钩子**（`on_waiting_llm_request` / `on_llm_request` / `on_llm_response` / `on_decorating_result` / `after_message_sent`）：**不属于** `AdapterMessageEvent`，不受 access 分档重排影响，各插件用各自 `priority` 竞争。
- 关键顺序：`private_settle(maxsize)` 等待合并 → `basicz` gate(默认 0) → 各 `on_llm_request` 注入（basicz/ltm/vision_context/websearch 同默认 0，同档顺序待确认）→ `on_decorating_result`。

## 五、新增插件时

1. 在 `metadata.yaml` 里写好 `DECLARED_COMMANDS` / `DECLARED_BEHAVIOR`（access 会 ast 扫描）；
2. 按本目录模板补一份 `docs/plugins/<名>.md`（8 个章节），登记到上面第一节表格；
3. 若引入新的跨插件 extra 键 / import / 共享文件，同步更新第三节速查表与对方文档的 §5；
4. 若改了框架补丁，更新 [PROJECT.md §14](../PROJECT.md)。
