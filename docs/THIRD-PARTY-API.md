# 第三方 API 模式（DeepSeek）

> 本文覆盖：怎么买 DeepSeek API、怎么接进来、怎么切换、token 限额、
> 省 token 模式、按群审查开关，以及切过去之后哪些本地模型必须停。

最后更新：2026-11-18

---

## 1. 购买 DeepSeek API

1. 打开 <https://platform.deepseek.com/>
2. 用手机号注册 / 登录（需实名认证才能调用）
3. 左侧 **充值** → 支付宝 / 微信，最低 ¥10
4. 左侧 **API keys** → **创建 API key** → 复制（只显示一次）

余额扣费顺序：赠送余额 → 充值余额。

### 当前价格（2026-11 官方）

按百万 tokens 计，**空闲时段是高峰时段的一半**。
高峰时段＝北京时间周一至周五（非节假日）9:00–12:00、14:00–18:00，其余全算空闲。

| 项目 | deepseek-flash | deepseek-v4-pro |
|---|---|---|
| 输入（缓存命中）空闲 | 0.02 元 | 0.15 元 |
| 输入（缓存命中）高峰 | 0.04 元 | 0.30 元 |
| 输入（未命中）空闲 | 1 元 | 4.5 元 |
| 输入（未命中）高峰 | 2 元 | 9.0 元 |
| 输出 空闲 | 4 元 | 13.5 元 |
| 输出 高峰 | 8 元 | 27.0 元 |

机器人聊天用 `deepseek-flash` 就够，`v4-pro` 贵 4~6 倍。
按每天 2000 条短对话估算，flash 大概几毛到几块钱一天。

---

## 2. 接入（填 key）

配置文件：`apps\AstrBot\data\cmd_config.json` → `provider` 数组里已有占位项：

```json
{
  "id": "deepseek",
  "type": "openai_chat_completion",
  "provider_type": "chat_completion",
  "enable": false,
  "api_key": "填你的 DeepSeek API Key",
  "api_base": "https://api.deepseek.com/v1",
  "model": "deepseek-flash",
  "custom_extra_body": {"max_tokens": 300, "temperature": 0.8}
}
```

把 `api_key` 换成你的 key 即可，**默认 `enable: false`**，不影响现在的本地模式。

也可以直接在 WebUI（`http://localhost:6185` → 服务提供商）里填。

---

## 3. 切换命令（管理员）

| 命令 | 作用 |
|---|---|
| `/切换 api 第三方` | 切到 DeepSeek，8 秒后自动重启 |
| `/切换 api 本地` | 切回本地 9B，8 秒后重启 |
| `/用量` | 看当前模式、今日已用、额度、省 token 状态 |
| `/额度 200000` | 设每日 token 上限（0 = 不限） |
| `/省token on` / `off` | 省 token 模式 |
| `/审查 on` / `off` | **本群**内容审查（仅第三方模式生效） |

状态文件：`data\api_mode.json`

```json
{
  "mode": "local",
  "save_token": true,
  "daily_limit": 200000,
  "used": {"date": "20261118", "tokens": 0},
  "review_groups": {"942316942": true}
}
```

---

## 4. 切到第三方之后，本地 AI 怎么处理

你的要求：**第三方模式下不许本地大模型参与，≤2B 的可以。**

切换时会自动做这些：

| 组件 | 大小 | 第三方模式 | 说明 |
|---|---|---|---|
| 主对话模型 `local-llama` | 9B | **停用** | 改由 DeepSeek 接管 |
| 双判官 9B | 9B | **停用** | `reply.json` 的 `dual_judge` 自动置 false |
| 思维链 | 9B | **停用** | `thinking.enable` 置 false |
| 记忆抽取（LTM） | 9B | **跳过** | 插件检测到第三方模式直接 return |
| 判官 1.5B | 1.7B | **保留** | ≤2B，允许 |
| 嵌入 bge-small | 0.1B | **保留** | 知识库检索要用 |
| OCR / caption | 0.9B | 停用 | 本地对话链整体关掉，避免误用 |

切回本地时，`dual_judge` 和 `thinking` 会恢复。

---

## 5. 省 token 模式

`/省token on` 时（第三方模式生效）：

- 历史上下文**只保留最近 10 条**，不再整段回放
- `max_tokens` 由 provider 配置控制（默认 300，够一次群聊回复）
- 思维链保持关闭（思考内容也计费）

效果：长群聊场景下输入 token 大约能省 50~70%。

---

## 6. 按群审查

`/审查 on` 在**当前群**打开，只对第三方模式生效。

- 词表：`data\review_words.txt`，一行一个词，`#` 开头是注释
- 命中后整条回复替换为「这个话题我不接」，并写日志 `[apimode] review blocked`
- 默认给了 15 个词，自己改成需要的

为什么只在第三方模式开：本地跑没人管你，走 DeepSeek 是人家在审，
封号的是你的账号和余额，所以这时候才需要自我审查。

---

## 6.5 图片理解（DeepSeek 看图）

`deepseek-flash` **支持图像输入**（`deepseek-v4-pro` 不支持），已经配好：

```json
"model": "deepseek-flash",
"modalities": ["image", "text"]
```

行为区别：

| 模式 | 图片怎么处理 |
|---|---|
| 本地 | 本地 9B 不支持图片，peer 插件会把图片剥掉，只靠 OCR 插件转成文字 |
| 第三方 | **不再剥图**，图片原样发给 DeepSeek 直接看 |

所以第三方模式下 `vl-ocr`（本地 OCR）是停用的——没必要先转文字，还多一层损耗。

peer 插件里的判断：

```python
if req.image_urls and not _third_party_mode():
    req.image_urls = []      # 只有本地模式才剥
```

**成本提醒**：图片按 token 计费，一张普通图大约 1000~2000 tokens。
群里有人连续刷图时，建议把 `/额度` 设低一点。

---

## 6.6 读图只在必要时

表情包不能每次都送进视觉模型（一张 1000~2000 tokens），所以加了一道判断：

```python
VISION_HINTS = ("截图", "看图", "这张图", "图上", "图里", "图片里",
                "识别", "翻译", "这是什么", "什么字", "写的啥", …)

def _should_read_images(text, images):
    if 命中上面的词:            return True
    if 句子里有问号:             return True
    if 图片 >= 3 张:            return True   # 多图多半是求助
    if 单张体积 > 60KB(base64): return True   # 长截图/照片
    return False                              # 其余当表情包，不读
```

实测：

| 消息 | 图 | 读不读 |
|---|---|---|
| `[表情包]` | 1 张小的 | ❌ 跳过 |
| `这图什么意思？` | 1 张 | ✅ 读 |
| `看这个截图` | 1 张 | ✅ 读 |
| 无文字 | 1 张大图 | ✅ 读 |
| 无文字 | 3 张 | ✅ 读 |

所以：**发表情包不会触发视觉**，只有明显在问图的时候才花这个钱。
日志里会打 `[peer] vision skipped: N image(s), likely sticker`。

---

## 6.7 思维链（第三方适配）

DeepSeek 的思考模式和本地 9B 用的参数不一样：

| | 本地 9B | DeepSeek |
|---|---|---|
| 开/关 | `chat_template_kwargs.enable_thinking` | `thinking: {type: enabled/disabled}` |
| 长度 | `max_tokens` | `reasoning_effort: low/high/max` |
| temperature | 生效 | 思考模式下**被忽略** |

所以 `/思维链` 命令改成按第三方语法写：

```
/思维链 off        关掉（默认，省钱）
/思维链 on         开，强度 high
/思维链 low        开，强度 low（最省）
/思维链 max        开，强度 max（最贵）
```

会写进 `deepseek` provider 的 `custom_extra_body`：

```json
{"thinking": {"type": "enabled"}, "reasoning_effort": "low"}
```

开启时会自动移除 `temperature`（思考模式下它无效，留着只是噪音）。

**成本提示**：思维链内容也按输出 token 计费，强度 `max` 可能让单条回复贵 3~5 倍。
日常群聊建议 `off`，遇到需要推理的话题再 `/思维链 low`。

---

## 7. 每日额度

- `/额度 200000` 设上限，`used.tokens` 每天零点自动重置（按日期判断）
- 超了之后：**不再请求第三方**，直接回一句「今日第三方额度已用完」
- 用量来自 provider 返回的 `usage`，不是估算

---

## 8. 排错

| 现象 | 原因 |
|---|---|
| 切换后没反应 | 重启要 8 秒，等日志出现 `AstrBot started` |
| 报 401 | key 没填或填错 |
| 报 402 | 余额不足，去平台充值 |
| 回的还是很机械 | 可能还在本地模式，`/用量` 看 mode |
| 审查不生效 | 当前不是第三方模式，或该群没开 |

---

## 9. 控制台面板对照（第三方模式）

**模式的唯一真相**是 `agent_runner.config.model.provider_id`（WebUI 里选的那个），
不是 `data/api_mode.json`。后者只是 `/切换` 的记账，两边不一致时以配置为准
（控制台、peer、ltm 都已改成读配置）。

| 面板 | 第三方模式 | 说明 |
|---|---|---|
| 状态灯 | ✅ | 多了 VL/OCR 两个灯，返回里带 `mode` |
| 系统状态 | ✅ | CPU/内存/显存无关，照常 |
| 手动加记忆 / 最近记住的事 | ✅ | 直接写 memory.db |
| 最近对话 / 对话上下文 | ✅ | 读 AstrBot 自己的库 |
| 触发权限 / 自动接话 / 水群 | ✅ | 读 cmd_config |
| 人格 | ✅（只读展示） | **不提供服务端改写**，提示词你自己维护 |
| 判官 | ✅ | 1.7B 本地，第三方模式下仍可用（≤2B） |
| 判官与思维链 | ⚠️ 已适配 | 开关映射到 `thinking.type`，预算折算成 `reasoning_effort` |
| 回复行为 | ✅ | reply.json |
| 模型采样参数 | ⚠️ 部分生效 | 温度在 DeepSeek 思考模式下被忽略；`repeat_penalty` 不支持 |
| 主模型 | ⚠️ 已适配 | 第三方模式下列表变成 `deepseek-flash` / `deepseek-v4-pro` |
| 图片理解 | ✅ | 显示 caption 缓存；本地 VL 状态看状态灯 `vl` |
| 已装模块 | ✅ | 插件列表 |
| 日志 | ✅ | AstrBot 日志尾部 |

“⚠️ 已适配”指这次改过：面板不再只读写 `provider[0]`，而是读写**当前真正在用的 provider**。

---

## 10. 控制台新增面板（审查 / 额度 / 识图）

### 审查 · 额度 · 省 token

- **本群审查开关**：按白名单群逐个勾选，写 `api_mode.json.review_groups`
- **每日额度**：`daily_limit`，0 = 不限；`used.tokens` 每天按日期重置
- **省 token 模式**：勾上后只发最近 N 条历史
- **历史消息数量滑块**：2~40 条，写 `history_keep`，由 `astrbot_plugin_apimode`
  在请求前截断 `req.contexts`

写入即时生效，**不需要重启**。

### 识图

| 按钮 | 效果 |
|---|---|
| 本地 VL 读图 | 图先转文字再发给模型，不耗视觉 token |
| 交给第三方看图 | 图片直接发 DeepSeek |
| 关闭读图 | 忽略图片 |

另有「启动/停止本地 VL」按钮，状态显示本地 VL 在线/离线、端口、模型名。

### 不支持的功能自动置灰

- 第三方模式下 `repeat_penalty` 滑条禁用，显示「API 不支持」
- 第三方模式下双判官勾选框禁用（要本地 9B）
- 第三方模式下思维链预算滑条禁用，改为显示 `reasoning_effort` 档位

## 11. 切换时自动卸载本地模型

主模型切到 DeepSeek 后，会**自动卸载**这三个本地服务：

| 端口 | 服务 | 处理 |
|---|---|---|
| 8080 | 本地 9B 聊天 | 终止进程 |
| 8083 | OCR | 终止进程 |
| 8085 | 本地识图 VL | 终止进程 |

保留：8082 判官（1.7B，筛回复频率继续用）、8097 嵌入（知识库要用）。

实测卸载后内存空闲从 7.8GB 回到 14.2GB。

切回本地时会自动把它们拉起来（`start-router.ps1` / `start-ocr.ps1` / `start-vl.ps1`），
切换同时会把识图模式改成 `local`；切到 API 时识图改成 `third_party`。

守护逻辑：`astrbot_plugin_apimode` 每 20 秒读一次 `agent_runner` 的 provider，
发现从本地变 API（或反向）就执行卸载/拉起，所以**在 WebUI 里直接改主模型也会生效**。

⚠️ 卸载后本地 fallback 不可用：DeepSeek 报错时没有备用模型。要恢复就 `/切换 api 本地`。

---

## 12. 本地优化开关与记忆提示词

### 本地优化 / 第三方精简（一键）

面板两个按钮写 `data/reply.json`：

| 预设 | meme_chance | text_rules |
|---|---|---|
| 套用本地优化 | 0.3（自动挂表情） | 保底一条「句号→波浪号」 |
| 套用第三方精简 | 0 | 清空 |

理由：

- **表情**：本地模型不会主动调 `send_meme` 工具，只能靠概率挂；DeepSeek 会自己调工具，
  再概率挂就重复了
- **文本替换**：本地模型常忘“别用句号”，只能正则兜底；第三方能读懂提示词，不必再改原话

两个复选框可以单独开关，改完立刻生效（不用重启）。

### 记忆提取提示词

面板「记忆提取提示词」直接编辑 `data/ltm_prompt.txt`，保存后下一轮提取生效。

- 必须保留 `{user}` 和 `{bot}` 两个占位符，否则保存会被拒绝
- 插件读取逻辑：文件存在且含占位符就用文件，否则回落到内置默认
- 想减少“莫名其妙”的记忆，把「不收」那几条写具体，比如点名“不记录群友转述、不记录假设句”

提取侧仍有两道硬校验：

1. `evidence` 必须真的出现在用户原话里（去空白后比对）
2. 去重相似度 0.92，超过就不写入

所以提示词写严之后，误记会明显减少。

---

## 13. 双向切换的兼容性（实测）

这一节是 2026-11-18 晚上真机来回切了一次之后写的，不是推演。

### 13.1 切到第三方会发生什么

| 动作 | 结果 |
|---|---|
| `agent_runner.config.model.provider_id` | `local-llama` → `deepseek` |
| `fallback_provider_ids` | `["local-llama"]`（本地兜底，但此时本地已卸载） |
| provider 启用位 | `local-llama`、`vl-ocr` 关；`deepseek` 开 |
| `reply.json` | `meme_chance=0`、`text_rules=[]`、`dual_judge=false`、`thinking=false` |
| DeepSeek 参数 | `thinking.type=disabled`、`temperature=0.8`、`max_tokens` 保留 |
| 识图模式 | `third_party`（图直接发 DeepSeek） |
| 本地进程 | **终止** 8080 聊天 / 8083 OCR / 8085 识图 VL |
| 保留 | 8082 判官（1.7B）、8097 嵌入（知识库） |

内存实测：**7.8 GB 空闲 → 16.5 GB 空闲**。

### 13.2 切回本地会发生什么

| 动作 | 结果 |
|---|---|
| `provider_id` | `deepseek` → `local-llama` |
| 启用位 | `local-llama`、`vl-ocr` 开；`deepseek` 关 |
| `reply.json` | `meme_chance=0.3`、`text_rules` 补回句号规则、`dual_judge=true` |
| 本地 provider 参数 | 复位成 `max_tokens≤300`、`temperature=0.5`、`enable_thinking=false` |
| 识图模式 | `local`（图先由 VL 转文字，不进第三方） |
| 本地进程 | **自动拉起** 8080 / 8083 / 8085 |
| LTM 记忆抽取 | 从「跳过」恢复为「每 30 分钟扫一次」 |

内存实测：**16.5 GB 空闲 → 2.1 GB 空闲**（9B 的 131K 上下文很吃内存）。

### 13.3 切回来会不会炸：实测结果

```
本地 9B        「只回两个字：在线」→ 在线         ✅
本地 VL 识图   江苏 4 场兽展…（21.4 秒）          ✅
OCR 8083       已监听                              ✅
判官 8082      已监听                              ✅
AstrBot        适配器已连接，无 provider 报错       ✅
控制台面板     采样/思维链/主模型 全部切回本地视图  ✅
```

**结论：不会炸。** 早先会出问题的两处已经修掉：

1. 本地 provider 带着 `enable_thinking=true` + `max_tokens=500` 回来
   → 回复又慢又长，现在强制复位
2. 表情概率和文本规则停在第三方精简的 0 和空
   → 本地模型少了两个保底，现在自动补回

### 13.4 切换时不要手动做的事

- 别在 WebUI 里同时启用 local-llama 和 deepseek —— 选哪个由 `agent_runner` 决定，
  同时启用只会让人搞不清当前在跑谁
- 别在切换的 8 秒重启窗口里改配置，会被覆盖
- 切回本地后如果卡顿，先看内存：`Get-CimInstance Win32_OperatingSystem | % FreePhysicalMemory`

### 13.5 内存不够时的两个开关

| 做法 | 效果 |
|---|---|
| 把 `models.ini` 里主模型 `c = 131072` 改小（如 32768） | 省几 GB，长上下文能力下降 |
| 控制台「识图」面板点「停止本地 VL」 | 省 1~2 GB，识图改走第三方或关闭 |

### 13.6 守护逻辑

`astrbot_plugin_apimode` 每 20 秒读一次 `agent_runner` 的 provider：

- 本地 → DeepSeek：停 8080/8083/8085，识图切第三方
- DeepSeek → 本地：拉脚本，识图切本地，参数复位

所以**直接在 WebUI 里改主模型也会触发**，不必非得走 `/切换` 命令。

---

## 14. 判官双后端（2026-11-19）

判官现在有两套**完全独立**的配置，按主模型 provider 自动选择，互不覆盖：

| 模式 | 后端 | 配置 | 上下文 | 概率闸 |
|---|---|---|---|---|
| 本地 `local-llama` | 8082 Qwen3-1.7B | `data/judge.json`（原有） | 8 条 | 0.3（原有） |
| 第三方 `deepseek` | OpenAI 兼容 API | `data/judge_api.json`（新增） | 3 条 × 60 字 | **默认关闭** |

### 14.1 第三方判官的判定顺序

1. **唤名词**（`summon`，句中叫它名字）：0 token 直通，**不等静默窗口、不吃"刚回过话"的冷却**；只挡"回复真的正在发"和 `summon_gap` 内的连叫
2. **回复在途**（`inflight_ttl`）：判定通过 → 生成完的认领窗口（默认 45 秒）；生成完会按分段配置估出真实发送时长接着占位，见 14.6
3. **刚回过话的冷却**（`reply_gap`）：默认 6 秒，从**真正发完**开始算；命中强触发规则可以破例（见 14.6）
4. 回复条数限制**前处理**（`budget_gate`，默认开）：超预算直接不回，不花 token
5. 必答/免打扰关键词、必答正则
6. 追问直通（0 token）：命中 `followup_patterns`（如"你不是猫吗怎么汪汪叫"）直接回
7. **话段复用**（`burst_reuse`）：这一段已经判过/回过就不再送判官 —— 省 token 的主力（见 14.6）
8. 过短（按**合并后**的话段长度）、复读直接不回
9. **相似去重**：和刚触发过回复的那句几乎一样 → 不回（`dup_window` / `dup_ratio`）
10. 才调 API：短提示词 + 最近 3 条 + bot 最近一句
11. 判官说接 → 概率闸（`use_reply_chance`，默认关）→ 回复
12. 判官关闭/失败/超限 → 不碰 8082，按 `fallback_chance`（默认 0.3）兜底

第 1 步之前的**静默等待**（`burst_settle`）在锁外完成：等这一口气说完，期间又来消息就放弃，让最新那条去判。这一步是"拆句合并"的关键。

**这套顺序只覆盖"要不要主动接话"。@ 它和唤醒前缀走的是 AstrBot 内置回复通道，不经过这里**，所以另有一道上层硬锁（`on_llm_request` → `event.stop_event()`），在回复在途时把它们一并挡掉，见 14.6「在途硬锁」。

### 14.2 省 token 的手段

- 提示词从 550 字压到约 150 字，去掉 8 个 few-shot
- 上下文 8 条 → 3 条，每条截 60 字，另加 bot 最近一句（`note_bot_reply` 记录）
- `max_tokens=2`、`thinking:disabled`、`temperature=0`，**没有** `grammar`（DeepSeek 不支持 GBNF）
- 规则直通 + 相同文本 30 秒指纹缓存
- 独立日限额 `daily_limit`，超限走"规则 + 概率"兜底，不硬闭嘴
- 连续失败 3 次熔断 5 分钟，避免错误重试烧钱

实测单次约 **139 tokens**（含 3 条上下文），本地老链路约 600-800。

### 14.3 密钥与记账

- `api_key` 留空 → 自动沿用 `cmd_config.json` 里 `deepseek_source` 的密钥
- 想单独开一条密钥/额度：填 `api_key`，判官与主模型互不影响
- 用量记在 `judge_api.json.used`，控制台「判官」面板和 `/判官 状态` 都能看
- 判官直连 httpx，不经过 `on_llm_response`，所以主模型的 `/用量` 不含它，必须看判官自己的计数

### 14.4 控制台与命令

- 控制台「判官」面板底部新增"第三方模式判官"：Base/模型/密钥/上下文条数/日限额/开关/提示词
- 面板里还能直接改**必答/免打扰关键词、追问直通正则、结果缓存秒数、每条截断字数**（这些就是省 token 的规则层，改完即时生效）
- 密钥只写不回显，留空保存不会覆盖原值
- 「话段聚合」一栏可调 `burst_enable` / `burst_settle` / `burst_gap` / `burst_reuse` / `reply_gap` / `summon_gap` / `dup_window` / `dup_ratio` / `break_follow`（0 即关闭对应机制），以及 `bot_names`（名字）和 `break_words`（让判官看一眼的脏话词）
- 「在途硬锁」勾选框对应 `inflight_lock`：回复生成/分段发送期间，@ 它和唤醒前缀也一律不接
- `/判官 预算 on|off`、`/判官 概率 on|off`、`/判官 开关 on|off`、`/判官 话段 on|off`、`/判官 锁 on|off`、`/判官 等待 N`、`/判官 限额 N`

### 14.5 注意

- 本地模式**不受影响**：仍走 8082、原提示词、8 条上下文、0.3 概率闸
- 第三方模式下 8082 可以停掉省 1.8GB，但停掉后本地模式要记得先拉起
- 改 `judge_api.json` 无需重启，下一条群消息生效

### 14.6 话段聚合 + 在途硬锁（2026-11-19 第四版）

**现象**：群里连着发两三句（很多人习惯把一句话拆成两三段发），或者一句刚发完又补一句带"阿灰"，机器人会连着回三四条语义差不多的；回复到一半再 @ 它一次，还会再发一条。

**第一版根因判断偏了**：以为 `judge_delay` 的静默窗口在生效，其实那两行是**死代码**——它在 `_get_lock` 里面 `sleep`，而后续消息的 `handle_message` 也要拿同一把锁，被挡在外面。于是 `_record_marker` 永远不变，"来了新消息就放弃"这个分支一次都不会走。真正的效果只是"每条消息都白等 2 秒"。

**第二版漏了一点：生成完 ≠ 发完**。回复是 AstrBot **分段发送**的（`platform_settings.segmented_reply`，本项目 `interval_method: human`），每段之间 `sleep`。而 `note_bot_reply` 在 `on_llm_response` 触发，那时才刚生成完，发送还没开始。所以从"生成完"开始算冷却，发送期间和刚发完的几秒都是漏挡的。

**第三版还漏了两点**：① 耗时估算取的是**均值**，有一半概率估短，估短了就会在真正发完之前放开锁；② @ 它和唤醒前缀走的不是这套判定（`need_active_reply` 第一句就 `return False`），所以"回复到一半又被 @ 一次"根本没人挡。

**做法：话段聚合 + 按分段配置估算发送时长**

| 机制 | 字段（默认） | 作用 |
|---|---|---|
| 话段总开关 | `burst_enable`（true） | 关掉＝退回逐条判定，不等待、不复用 |
| 到达时间戳 | — | `_last_arrival` 在**锁外**写，后面来的消息能被看见（死代码的修法） |
| 静默等待 | `burst_settle`（3.5） | 判定前等 3.5 秒；期间又来消息就放弃，交给最新那条。等待在**锁外**，多条并行等，不排队 |
| 话段间隔 | `burst_gap`（15） | 两条消息间隔小于它算同一段；中间冷场超过它就当新话题 |
| 话段复用 | `burst_reuse`（45） | 这一段**判过或回过后**不再送判官（省 token），除非命中强触发 |
| 在途硬锁 | `inflight_lock`（true） | 回复生成/分段发送期间，**@ 它、唤醒前缀也一律不接**（见下文） |
| 发送耗时上沿 | — | `_estimate_send_seconds(text, upper=True)` 取最坏情况顶住，真实发完信号一到就收敛 |
| 回复后冷却 | `reply_gap`（6） | 只挡"紧接着的下一条"，从**真正发完**开始算 |
| 在途上限 | `inflight_ttl`（45） | 判定通过 → 生成完的认领上限；生成失败也不会把群锁 90 秒 |
| 召唤词间隔 | `summon_gap`（4） | 叫名字不吃冷却，但 4 秒内连叫只应一次 |

**发送耗时：上沿兜底 + 真实信号收敛**

不能只靠估算。"什么时候发完"有两个来源，两个都用：

```text
兜底（生成完时）：_estimate_send_seconds(text, upper=True)
  human 模式每段 = min((0.45 + 字数/7) × 1.35 + 1.8, 5.5)，再加 0.4s 网络
  三段各 5 字 ≈ 11.3s（均值只有 5.0s，取均值会有一半概率估短）

真实（发完后）：after_message_sent 钩子 → note_message_sent()
  _inflight_until = 0
  _cool_until     = now + reply_gap
  _last_bot_span  = (start, now)     ← 发言区间收敛到真实发完
```

`after_message_sent` 在 `respond/stage.py` 的分段发送循环**和所有 sleep 之后**触发，是真正"用户已经看到消息"的时刻，比任何估算都准。估算取上沿只是为了"信号没到之前绝不能提前放开"，取均值就会漏。

**在途硬锁：正在回复时，@ 也不放行**

这是第三版最大的洞：`need_active_reply` 第一句是 `if event.is_at_or_wake_command: return False`，@ 和唤醒前缀**根本不进判官这套判定**，走的是 AstrBot 内置回复通道。所以判官挡得再好，回复到一半再 @ 一次还是双发。

挡的位置只能往前挪到 `on_llm_request`：

```python
if event.is_at_or_wake_command and is_third_party_mode():
    if api_cfg["inflight_lock"] and not is_command:
        if self._inflight_for(umo) > 0:
            event.stop_event()   # 钩子返回 True → pipeline 放弃本次 LLM 调用
            return
        # 不在途：这条 @ 的回复自己先占住在途，避免它发送期间又被人喊一声
        self._inflight_until[umo] = now + api_cfg["inflight_ttl"]
        event.set_extra("_judge_inflight_owned", True)
```

三个细节：

- **只处理第一轮**：同一条消息可能多轮进 `on_llm_request`（工具调用循环），用 `_judge_inflight_owned` 标记，否则第二轮会被自己占的锁挡掉。
- **指令优先**：`handlers_parsed_params` 非空的（@ 它 + `/reset`）不拦，聊天锁不该吞掉明确指令。
- **配对释放**：只有 `_judge_inflight_owned` 的事件发完才允许 `note_message_sent` 释放在途，别的插件推送不会把我们的锁提前放掉。

**效果**：拆成三句发 → 只有最后一句去判定，判官看到的是完整意思（前三句已进上下文）→ 一段只回一条；回复期间不管喊名字、@、唤醒前缀，一律等到这条发完再说。

**强触发：规则只筛候选，归属交给判官**

| 触发 | 条件 | 处理 |
|---|---|---|
| 叫名字 | 含 `bot_names`（阿灰/灰灰/…） | **直接接**，0 token（明确点名，没什么可犹豫的） |
| 脏话 | 含 `break_words` | **只放行给判官**，不直接接 |

为什么脏话不直接用规则定：规则只能看出"有脏话"，看不出骂的是谁。"你傻逼吧"可能是骂它，也可能是骂群里刚说话的那个人。这件事只有能读上下文的判官做得来——它的 prompt 里有 `{recent}` 和 `{last_bot}`，所以放行时会在提示词末尾追加一段：

```text
注意：这句带脏话。先判断它在骂谁——如果是在接你刚才说的「…」，或者用「你」指的是你，回 1；
如果明显在骂群里另一个人、跟你无关，回 0。
```

多花约 130 tokens，只在脏话出现时才花（频率很低）。判 0 就标记 `judged`，这一段后面不再送判官。

辅助函数 `_bot_spoke_last()` 改成用**发言区间** `(start, end)` 而不是一个时间点：它一句话分几段发，中间隔好几秒，只记一个点会漏掉"发送期间插话"。

**日志判别**（`group judge | ...`）：

- `话段未说完，交给最新一条` → 拆句合并生效，本条让位
- `同话段已answered/judged，不再送判官` → 省 token 生效
- `点名打破冷却(剩Xs)` / `话段内点名，打破复用` → 叫名字破例
- `脏话待判(剩Xs)，交给判官看骂谁` / `话段内脏话待判` → 放行给判官判归属
- `发送耗时上沿 Xs，等真实发完信号收敛` → 生成完，先按最坏情况顶住
- `发送完成，冷却从此刻起算 Ns` → 真实发完信号到了
- `在途硬锁，@/唤醒被挡(剩Xs)` → **正在回复时 @ 它被挡住**（正常）
- `唤醒/点名已占在途锁` → @ 的回复自己占位，发送期间不会被人再喊一遍
- `召唤词但回复在途` → 句中叫名字也在让路
- `召唤词间隔过密` → `summon_gap` 生效

**调参**：

- 嫌回得慢：`/判官 等待 2` 或面板把 `burst_settle` 降到 2.0（拆句间隔长的群别低于 2）
- 嫌还是连发：`reply_gap` 加到 10；确认 `segmented_reply` 没被改成 `random`（`random` 估不出准确时长）
- 嫌话段复用太省、明显不理人：`burst_reuse` 降到 20，或把常见叫法加进 `bot_names`
- 觉得"回复期间 @ 它也不理"太硬：`/判官 锁 off`（或面板关掉「在途硬锁」），代价是发送那几秒里 @ 会再发一条
- 想完全退回逐条判定：`/判官 话段 off`

### 14.7 兼容性清单（别的插件、指令、实际群聊）

| 场景 | 会不会被挡 | 说明 |
|---|---|---|
| **@ 它 / 唤醒前缀（空闲时）** | **不会** | `need_active_reply` 第一道就是 `if event.is_at_or_wake_command: return False`，@ 和唤醒前缀不走这套主动接话流程，直接走内置回复通道——所以它一定应 |
| **@ 它 / 唤醒前缀（回复在途时）** | **会，而且是故意的** | 这是第三版最大的洞：@ 不经过 `need_active_reply`，判官挡不住。现在在 `on_llm_request` 里 `event.stop_event()` 硬挡，等这条真正发完（`after_message_sent`）再放开。`inflight_lock` 可关 |
| @ 它 + 明确指令（`/reset`） | 不会 | `handlers_parsed_params` 非空就跳过硬锁，聊天锁不吞指令 |
| 句中叫它名字（`summon`） | 不会 | 不吃冷却、不等静默窗口，只挡"正在发"和连叫 |
| 其他插件（兽聚/运势/统计/OCR） | **不会** | `on_message` 的 priority 是 `maxsize - 2`（最后执行）且**从不 `stop_event()`**；各插件的指令 handler 走自己的注册，与这里的返回值无关 |
| `/` `/` 开头的指令 | 不会 | 判定入口显式跳过 `message[0] in "/／"`，不花 token、不计入回复预算 |
| 插件主动推送的消息 | 不进冷却 | 只有 `on_llm_response` 会 `note_bot_reply`。所以插件刚推完，bot 仍可能接一句——取舍是"宁可少挡，不误挡" |
| 多群并发 | 互不影响 | 所有状态按 `umo` 分键，锁也按群 |
| 重启 | 无副作用 | 全部是内存状态，重启即清空；不会把"冷却"写进配置 |
| **本地模式** | **完全不受影响** | ① 所有判定只在 `is_third_party_mode()` 分支里；② `note_bot_reply` / `note_message_sent` / `on_req_llm` 的硬锁都先判 `is_third_party_mode()`，本地模式连一个状态都不写、也不拦 @。本地仍是 8082 + 8 条上下文 + 0.3 概率闸 |
| 改了 `segmented_reply` | 估算跟着变 | 分段配置是按 mtime 缓存的，改完下一条回复就用新值。真实发完靠 `after_message_sent`，所以即使估算不准也不会提前放开；改成 `random` 也安全 |

**实际群聊里的两种取舍**：

- 拆句发（3 条，间隔 3-8 秒）→ 合并成一段判一次，回一条。延迟比原来多 `burst_settle`（3.5s），但内容对得上。
- 一段里既有正事又有情绪（"我跟你说个事" → "我买了新相机" → "你猜多少钱"）→ 判官看到的是最后一句 + 前三句上下文，比只看"你猜多少钱"准得多。
- 骂人场景：它刚说完话就有人骂"你傻逼吧" → 放行给判官，判官看到 `{last_bot}` 会判 1；如果是两个群友互喷"你傻逼吧" → 判官判 0，它不插嘴。
