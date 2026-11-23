# astrbot_plugin_visionmode — 与其他插件的接口

> 源码：`apps/AstrBot/data/plugins/astrbot_plugin_visionmode/`
> 版本：1.0.0（metadata.yaml）  分类：自写

## 1. 职责一句话

提供 `/读图 本地|第三方|关|状态` 四态切换，把档位写进 `data/vision_mode.json` 并报本地 VL 在线状态；是「识图档位」的**写入方**，自己不读图、不改 prompt、不注册工具。

## 2. 注册的钩子

| 钩子 | 优先级 | 触发时机 | 实际行为 |
|---|---|---|---|
| `@filter.event_message_type(filter.EventMessageType.ALL)` → `handle`（main.py:144-145） | 未显式声明（装饰器无 `priority` 参数，走框架默认） | 所有消息 | 自己用字符串识别 `/读图`（155-159）；非管理员 → 发「只有管理员能改」+ `stop_event`（161-164）；其余每个分支（查状态 / 切换 / 用法 / 未知参数）都 `event.send(plain_result)` + `stop_event`（169-198）。**不处理**的消息直接 `return`，不停事件 |

其他消息（非 `/` 开头或 body 非「读图」）不拦截（147-159）。无 `on_llm_request`、无 `llm_tool`、无 `set_extra`。

## 3. 输入（别人给它什么）

- **事件字段**：`message_str`、`message_obj.raw_message`（dict 取 `raw_message` 判斜杠，147-157）、`get_sender_id()` / `role`（36 行降级鉴权用）。
- **`event.get_extra` 键**：无。
- **读的配置文件**：`data/vision_mode.json`（`load_vision_state`，47-62），键 `mode` / `port` / `model`，缺省 `local` / 8085 / `Qwen3VL-2B-Instruct`；`utf-8` 读。
- **外部 HTTP（本地端口）**：`GET http://127.0.0.1:<port>/v1/models`，timeout=3，200 即在线（`local_vl_ready`，71-84）。注意：**本文件未使用** `http://127.0.0.1:<port>/v1/chat/completions`——`caption_image()`（87-134）定义了但 `handle` 没调用，全仓也未见外部 import，实际消费者**待确认**。
- **其他插件直接调用**：`from unified_perm import is_admin`（28-36，来自 astrbot_plugin_access；ImportError 时降级 `{1154487120}` + `role=="admin"`）。`load_vision_state` / `save_vision_state` / `local_vl_ready` / `caption_image` 为模块级函数，外部引用**待确认**。

**权限来源**：`DECLARED_COMMANDS` 自声明四条 `/读图*` 为「管理」（39-44），实际鉴权走 access，不自己维护名单。

## 4. 输出（它给别人什么）

- **`event.set_extra` 键与值**：无。
- **LLM 工具**：无。
- **改写 prompt / 图片链**：无。
- **`stop_event`**：所有 `/读图` 命中分支都停（164,175,189,198）；未命中的消息不停。
- **发消息**：`event.send(event.plain_result(...))`——状态（`读图方式 <mode> · 本地 VL 在线/离线（端口 <port>）`）、切换成功提示、非管理员提示、用法提示（161-198）。
- **写文件**：`save_vision_state()` 以 `json.dumps(ensure_ascii=False, indent=2)` + `utf-8` 覆盖写 `data/vision_mode.json`（65-68,192）。
- **面板接口**：无内置接口；dashboard「视觉」页 / 「模式与链路」表读同一文件（PROJECT.md:342-346）。

## 5. 与其他插件的协作关系

| 对方 | 关系 | 契约/约定 |
|---|---|---|
| apimode | 同写一份文件，无 import | `vision_mode.json` 的 mode 三方共写：apimode 切 provider 时写 `third_party`/`local`（apimode.md:14,219-237），本插件 `/读图` 写同键。**apimode 管主模型 provider（api_mode.json / provider_id），本插件管识图档位**，两者是不同维度。apimode.md:42 曾把「visionmode 侧读取点」标为待确认——本插件读取点即 `load_vision_state()`（47-62），已核实 |
| vision_context | 文件耦合，无 import | 本插件写档位，vision_context 的 `_vision_mode()` 按 mtime 读（vision_context/main.py:330-356），切换立即生效不用重启；`off` 时对方不下载、不识图、不调 flash |
| basicz | 文件耦合，无 import | basicz 读同一文件的 mode/port（basicz.md:23,59；basicz/main.py:849-864,927-933）决定本地/第三方看图链路 |
| access | 单向依赖 | import `unified_perm.is_admin`（31）；权限表归并到 access（PLUGIN-COMMANDS.md:389-391）；单拎时降级本地名单 |

## 6. 配置与数据文件

| 路径 | 用途 | 谁写 | 谁读 |
|---|---|---|---|
| `data/vision_mode.json` | 识图 mode/port/model | 本插件 `/读图`、apimode、dashboard | 本插件、vision_context、basicz、dashboard |
| （无其他文件） | — | — | — |

## 7. 顺序、坑与边界

- `ALL` 事件钩子对每个消息都跑，但先判空、再判 `/` 或 `／`、再判 body 以「读图」开头（147-159），非目标消息零副作用返回。
- 状态查询和切换成功都各探一次 8085（170,193）；`local` 模式且离线时切换回执追加「本地 VL 当前离线」（194-196）。
- 别名映射：`第三方|api|deepseek → third_party`；`关|off|关闭 → off`；`本地|local → local`；空或 `状态` → 只查询不写（167-190）。
- 默认 model 写死 `Qwen3VL-2B-Instruct`（58,62），但 VISION.md:3,273 标的是 `Qwen3VL-4B-Instruct`——**文档与代码默认值不一致，待确认**以哪个为准；实际识图端点由 vision_context 的 `CAPTION_ENDPOINTS` 指定 4B（vision_context/main.py:132）。
- 编码：本插件读合同 `utf-8`（55,68），vision_context 读侧用 `utf-8-sig`（vision_context/main.py:349）；若外部写入带 BOM 本插件会 json 解析失败并回退默认值。
- `caption_image`（87-134）用 `Bearer sk-vl-local`、`max_tokens=160`、`temperature=0.2`、timeout=60，失败返回 `None`；它不在本插件调用链上，消费者待确认。

## 8. 代码依据

`main.py:28-36`（权限降级）、`39-44`（指令自声明）、`47-84`（状态读写与探活）、`87-134`（`caption_image` 定义）、`137-198`（钩子与全部分支）。外部佐证：`apimode.md:14,42`、`basicz.md:23,59`、`PROJECT.md:342-346,389-391`、`PLUGIN-COMMANDS.md:226-238`、`docs/VISION.md:3,42-46`。
