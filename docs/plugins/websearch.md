# astrbot_plugin_websearch — 与其他插件的接口

> 源码：`apps/AstrBot/data/plugins/astrbot_plugin_websearch/`
> 版本：1.0.0（metadata.yaml）  分类：自写

## 1. 职责一句话

接本地 SearXNG（9000），给主模型注册 `web_search` 工具，并对问句类消息在请求前自动搜索、把结果块追加进 `req.system_prompt`；无斜线指令。

## 2. 注册的钩子

| 钩子 | 优先级 | 触发时机 | 实际行为 |
|---|---|---|---|
| `@filter.llm_tool(name="web_search")` → `web_search`（main.py:94-100） | 不适用（工具注册，无 `priority` 参数） | LLM 主动调用时 | 注册工具；参数 `query(string)`；返回格式化结果串或错误文案；不碰事件 / prompt |
| `@filter.on_llm_request()` → `auto_search`（main.py:110-111） | 未显式声明（装饰器无 `priority` 参数，默认 0；与 basicz/vision_context/ltm 同档，同档顺序**待确认**，ltm.md:12） | 每次 LLM 请求组装时 | 问句自动查 SearXNG（最多 4 条、snippet 140 字），**只追加** `req.system_prompt`；不 `stop_event`、不发消息、不改 extra |

无 `event_message_type` 钩子、无 `set_extra`。

## 3. 输入（别人给它什么）

- **事件字段**：`event.message_str`（`CQ_AT` 去掉 `[CQ:at,qq=...]` 后 strip，38,118）。
- **`event.get_extra` 键**：无。
- **读的配置文件**：无——`QUESTION_HINTS`、`*_MAX_RESULTS`、`*_SNIPPET_CHARS` 全是硬编码常量（26-36）。
- **外部 HTTP**：`GET http://127.0.0.1:9000/search`，params `q` / `format=json` / `language=zh-CN`，timeout=12（26,56-72）。
- **其他插件直接调用**：无（模块级 `_searx` / `_format` / `_looks_like_question` 全仓未见外部 import，**待确认**）。

## 4. 输出（它给别人什么）

- **`event.set_extra` 键与值**：无。
- **LLM 工具**：`web_search`，参数 `query(string)`（「搜索关键词，尽量简短准确」）；返回 `- 标题：摘要（URL）` 列表（工具 5 条 / snippet 180 字，27,29,75-85,101-108）；异常 → `搜索服务当前不可用，直接凭已有知识回答，并说明不确定。`；无结果 → `没有搜到结果。直接说明不确定，不要编造。` 下游 = 主模型自行决定是否调用。
- **改写 `req.system_prompt`**：`auto_search` 追加 `\n\n[实时搜索结果，可能不全或过时，只取和问题相关的部分；资料里没有的就直接说不知道，不要编]\n` + 结果块（131-134）；下游 = 主模型。
- **改写 `req.prompt` / `req.image_urls`**：无。
- **`stop_event` / 发消息 / 写文件 / 面板接口**：均无。

## 5. 与其他插件的协作关系

| 对方 | 关系 | 契约/约定 |
|---|---|---|
| 其他 LLM 工具（meme_manager `send_meme`、creator `tell_creator`） | 共存，互不摘除 | 本插件只**新增** `web_search`，不改框架工具列表（源码无工具增删）；各工具由各自插件注册，是否同时暴露给模型由框架决定 |
| basicz / vision_context / ltm（同挂 `on_llm_request`） | 同档追加 | 各方只追加自己那块 prompt（websearch/main.py:131-134），不共享 extra 键；meme_manager `priority=99999` 早于本插件默认 0（ltm.md:64），默认 0 之间的先后**待确认** |
| 框架 / provider | 与模式无关 | SearXNG 本地、第三方两种模式都起（PROJECT.md:400）；工具与自动搜索都不判断 api_mode / vision_mode |
| access | 无 | 本插件无斜线指令，不经过权限闸门（PLUGIN-COMMANDS.md:56 归为纯被动插件） |

## 6. 配置与数据文件

| 路径 | 用途 | 谁写 | 谁读 |
|---|---|---|---|
| （无本地配置文件 / 数据库） | 常量硬编码在 main.py:26-36 | — | — |
| `http://127.0.0.1:9000/search` | SearXNG 搜索服务 | Docker 容器（`restart=unless-stopped`，PROJECT.md:406） | 本插件 `web_search` 与 `auto_search` |

## 7. 顺序、坑与边界

- 自动触发条件（`_looks_like_question`，41-53）：去 @ 后长度 5~120 字且命中 `QUESTION_HINTS`（`?` / 什么 / 怎么 / 多少 / 谁 / 最新 / 新闻 / 今天 / 价格…）；不满足直接返回，零 HTTP。
- 查询只用前 60 字（`text[:60]`，122），工具入参由模型给。
- 失败不阻塞回复：工具异常返回文字让模型凭已有知识答（103-107）；自动搜索异常 / 无结果直接 `return`（121-127），不影响主模型。
- 搜索结果块自带「可能不全或过时 / 不知道就说不知道」防编造提示（132-133）。
- 9000 端口是 Docker SearXNG；容器没起时两条路都静默降级（PROJECT.md:397,406）。
- 想临时关自动搜索需改源码 `QUESTION_HINTS` 或用会话级 `/set`（PLUGIN-COMMANDS.md:298，框架是否支持待确认）。

## 8. 代码依据

`main.py:22-24`（自声明）、`26-36`（常量与问句词表）、`41-53`（判定）、`56-85`（SearXNG 与格式化）、`94-108`（工具）、`110-134`（自动搜索）。外部佐证：`PLUGIN-COMMANDS.md:56,291-299`、`PROJECT.md:397,400,406`、`docs/plugins/ltm.md:12,64`。
