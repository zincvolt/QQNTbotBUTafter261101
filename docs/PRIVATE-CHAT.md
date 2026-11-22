# 私聊话段合并与表情策略

> 对应插件：`astrbot_plugin_private_settle`（本地，1.0.1）
> 对应配置：`data/private_settle.json`、`data/meme_dm.json`
> 面板位置：控制台 → 判官 → 「私聊话段合并」/「私聊表情策略」

---

## 1. 为什么需要它

群聊的"一句话拆成三条发"由判官处理：消息到了先等 `burst_settle`（默认 3.5 秒），
期间又来新的就让前面那条让位，最后只回一次。私聊不能用这套——

- 私聊必回复（等价于判官恒返回 1）；
- 判官链第一行就是 `if message_type != GROUP_MESSAGE: return False`，整条链在私聊直接短路。

结果是：用户连发三条，机器人回三条。2026-11-23 的私聊实测日志：

```
00:32:23 用户：不知道，离开了前任那个吸血鬼应该来说是个好事……
00:32:25 机器人回复（带「难过」表情）
00:32:28 用户：唉，跟你说也没啥用
00:32:33 机器人回复（带「日常」表情）
```

这个插件只做两件事：**等用户把这一口气说完**，**把这几条合成一条用户消息再回**。
不送判官、不掷任何"要不要回"的概率、不加 token 成本。

---

## 2. 一条消息进来之后

```
消息 A（第一条）
  └─ on_waiting_llm_request(priority=maxsize)   ← 抢在 basicZ 闸门之前
       ├─ 斜杠指令 / 纯文件语音 / 白名单外 → 直接放行，不等待
       ├─ 会话里没有"正在攒的那组" → 自己当 owner，登记 pending[umo]
       │    ├─ 上一条还在生成？先排队等它结束（inflight_wait，默认 45s 封顶）
       │    └─ 安静 settle 秒（默认 3.5）→ 收工
       └─ 收工后：把攒到的文本拼成 "A\nB\nC"，图片接进消息链，交给主模型

消息 B、C（连发）
  └─ 看见 pending[umo] 存在 → 文本 append 进这一组、图片 append 进 images
       └─ event.stop_event()：自己不回复，也不进对话历史
```

合成后的样子（`event.message_str` 被改写）：

```
在吗
[图片]
我今天有点难受
想找人说说话
```

后面的链路（basicZ 的闸门、`astr_main_agent`、记忆抽取）拿到的都是这一条：
`req.prompt = event.message_str`，图片从 `event.message_obj.message` 逐个收集，
所以识图、图片记忆照常工作。被合并掉的 B、C 不会再落历史——它们的事件在
LLM 请求之前就停了，`update_conversation` 根本不会执行。

### 等待窗口的两个上限

| 字段 | 默认 | 作用 |
|---|---|---|
| `settle` | 3.5s | 安静这么久算"说完"。每来一条新消息都会把计时往后推 |
| `merge_window` | 15s | 一直说个不停时的天花板：从开始等待算，到了就发，不再攒 |

`settle = 0` 等于关掉等待（直接回），用于排查是不是等待拖慢了响应。

### 在途排队

私聊里 basicZ 走 @/唤醒直通、不抢在途锁，但 AstrBot 的 session 锁会把同一会话的
LLM 请求串行化。如果不排队，B、C 都可能在 A 生成期间过钩子，然后各回一条。
所以 owner 在开始 `settle` 之前会先等 `inflight_wait`（默认 45s，可调到 0 关闭）。

---

## 3. 与指令、图片、历史的交互

**指令不会冲突**（2026-11-23 自查，见 §6）：

- 指令在 `ProcessStage` 的 handler 阶段就被消费，根本不进 `on_waiting_llm_request`，
  所以不会被合并；
- 斜杠开头的消息（含全角 `／`）在本插件里第一行就 return：既不等待、也不 `stop_event`，
  交给指令链路自己处理；
- 合并只改**本条 owner 事件**的 `message_str`，不动其他事件，也不改 `raw_message`；
- 合并结果的第一个字符来自 owner 原文（owner 必须是普通消息才会被选中），
  不可能"冒充"成斜杠指令；AstrBot 的指令路由也早在改文本之前就定了。

**图片**：连发中带的图片会用原组件接进 owner 的消息链，`basicZ` 的
`_should_read_images` / 本地识图 / 第三方 flash 照常判断要不要读。

**历史**：只有合并后那一条用户消息入库，B、C 不留痕；下一轮追问时模型看到的是
完整的一整段，不是只剩最后一句。

**已知边界**：

- 等待窗口里发指令，指令会**立刻执行并回复**，owner 的聊天回复仍在 `settle` 后回来，
  于是短时间内可能看到两条（一条指令结果 + 一条聊天回复）。这是预期行为。
- 等待窗口里发"发个表情包"这类请求：合并后 `basicZ` 会直接发图并 stop，
  前面的正文不会再回。符合"用户就是要图"的直觉。
- 纯文件/语音不进合并（没有"话段"概念），原样放行。

---

## 4. 私聊表情策略

### 原先的问题

表情来自 `meme_manager` 的分类标记模式：每轮请求把
`发送格式 + 12 个分类描述 + 防泄露说明`（实测 **817 字符 ≈ 500 token**）塞进
`system_prompt`，模型看到分类表就倾向每条回复挂一个 `&&分类&&`。
`generation.emotion.probability=100` 时每条都允许发，于是私聊变成"每句一张图"。

### 现在的做法

`data/meme_dm.json` 的 `mode` 决定私聊怎么办：

| mode | 行为 | 用途 |
|---|---|---|
| `llm`（默认） | 不掷概率，能不能发交给主模型自己判断；额外注入一句「私聊默认只回文字，情绪明显且贴切才配 1 张」 | 同群聊那套，安静但不死板 |
| `off` | 不注入分类表、不挂表情工具，私聊完全不发表情 | 想彻底关掉时用 |
| `random` | 走 `generation.emotion.probability`（当前 35%） | 保留随机，回到旧行为 |

实现是 `meme_manager` 的本地补丁（`main.py` 的 `_apply_request_prompt` 与
`mixins/event_handlers.py`）：私聊判定在前，`off` 直接 strip + 摘工具并 return，
`llm` 则把 `meme_manager_send_probability_hit` 预置为 `True`（发送阶段读缓存，
不会再掷一次随机），群聊仍走原概率。**升级该插件会覆盖补丁**，记在
`docs/PROJECT.md §14`。

### 成本口径

- 图片本身**不进对话历史**（历史只存文本），发过的表情不会在后续每轮重复计费；
- 真实开销是那份每轮都注入的分类表。`llm` 模式下仍会注入（否则模型不知道能发图），
  但概率不再拦；`off` 和 `random` 未命中的轮次完全不注入；
- 群聊的 35% 概率保持不变——群里本来就回得少，配图反而加分。

---

## 5. 配置与面板

`data/private_settle.json`：

```json
{
  "enabled": true,
  "merge": true,
  "settle": 3.5,
  "merge_window": 15.0,
  "poll": 0.2,
  "inflight_wait": 45,
  "whitelist_only": true,
  "log": true
}
```

面板（6190 → 判官 → 私聊话段合并）可改：启用、合并开关、白名单限定、
等候窗口（`settle`）、最长等候（`merge_window`）、在途排队（`inflight_wait`）；
私聊表情策略单独一块（`off / llm / random`）。全部是合并写入，
保存后**下一条私聊生效，不用重启**。

`log=true` 时日志里能看到：

```
[dm] merged into #1 (3 msgs) | 我今天有点难受
[dm] settle 3.5s done, reply, merged 2 (waited 12 / yielded 0) | 在吗
```

---

## 6. 验证记录（2026-11-23）

隔离测试（`_tmp_verify_dm_merge.py`、`_tmp_check_cmd.py`、`_tmp_check_meme.py`）：

| 场景 | 结果 |
|---|---|
| 三条连发（含一张图） | 合成 `在吗\n[图片]\n…`，只回一条，图片进消息链 |
| `merge=false` 回退 | 旧组让位、最后一条回；缺陷已修（接管时不再误停自己） |
| 持续连发 5 条 | `merge_window` 到点发出，5 条全带出，不丢话 |
| 等待窗口内发 `/记忆 清理`、`／切换` | 不并入、不被本插件 stop、不计入合并文本 |
| 首条就是指令 | 0.000s 放行，不等待 |
| 表情三档（off/llm/random）+ 群聊 | 分支正确：off 摘 3 个工具且 flag=False；llm 预置 True 且不掷概率；random/群聊照旧 |

运行态：`restart-astrbot.ps1` 热重启两次（QQ 未断线），插件 1.0.1 加载、
`[dm] private settle ready (merge mode)`、无 Traceback；面板接口 GET/POST 读回落盘一致。
真实私聊连发与表情频率仍需看 `[dm]` 日志与用户体感确认。

---

## 7. 回退

- 只想回到"只回最后一条"：面板勾掉「合并连发内容」（`merge=false`）。
- 完全不等待：`settle=0`。
- 私聊表情想彻底静音：表情策略切 `off`。
- 停用整个插件：面板取消「启用私聊话段合并」，或删掉插件目录后重启 AstrBot。
