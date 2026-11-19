# 人工接管指南

> 这份文档是**入口**，不是百科。作用：让一个没接触过本项目的人（或隔了一段时间的你自己）
> 在 5 分钟内知道"这是什么、现在什么状态、出问题翻哪份文档、改完怎么验证、怎么用 Git 留痕"。
> 最后更新：2026-11-19

---

## 1. 一句话说清这是什么

跑在本机、用真实 QQ 小号登录的群聊机器人，人格「阿灰」。本地 9B 大模型 + 一堆本地小服务（判官/读图/向量/联网）+ 自研 AstrBot 插件。设计取向：**宁可少说、装死，也不刷屏、不编事实**。

**当前状态（2026-11-19）**：运行在**第三方 DeepSeek 模式**。本地 9B/OCR/VL 已按切换逻辑停掉，判官 8082 和向量 8097 仍在跑。系统在线、群消息正常处理中。

---

## 2. 第一反应：先看这三份

| 你想干什么 | 翻哪份 |
|---|---|
| 日常运维（启停、端口、改权限、看日志、回滚） | [README.md](../README.md) |
| 理解整体架构、功能、已知限制、6 处源码补丁 | [PROJECT.md](PROJECT.md) |
| 搞砸了/改错了，想知道别人踩过什么坑 | [LESSONS.md](LESSONS.md) |

按主题再细分：

| 主题 | 文档 |
|---|---|
| 兽聚/运势/统计指令的词表、卡片样式 | [COMMANDS.md](COMMANDS.md) |
| 全部指令总表（框架自带 + 所有插件） | [PLUGIN-COMMANDS.md](PLUGIN-COMMANDS.md) |
| 本地 VL 读图（8085） | [VISION.md](VISION.md) |
| DeepSeek 第三方模式、双向切换实测 | [THIRD-PARTY-API.md](THIRD-PARTY-API.md) |
| 写一个新插件 / 加一条判断条件 | [MODULE-GUIDE.md](MODULE-GUIDE.md) |
| 提示词拼接与调用链（本次分析） | 见本文 §6 |

---

## 3. 铁律（违反会出事）

1. **重启 QQ 要重新扫码**。改 AstrBot 配置/插件/人格**绝不重启 QQ**，只跑 `scripts\restart-astrbot.ps1`（10 秒，QQ 不断线）。
2. **只用小号**。低频、不群发。看到"账号存在风险"提示立即停手。
3. **QQNT 版本锁死 9.9.25**，hosts 已屏蔽更新域名。一升级，注入即失效。
4. **AstrBot 升级会覆盖 6 处源码补丁且不报错**——功能会悄悄消失。用 Git 的 `git diff` 核对补丁是否还在（见 §5）。
5. **改完必须验证"运行过"，不是"编译过"**。这项目踩过三次 `str.replace()` 静默失败的坑（详见 LESSONS.md §1）。

---

## 4. 改代码的验证清单

每次改动后，对号入座跑一遍：

| 改动类型 | 必做验证 |
|---|---|
| Python 源码 | `py_compile` + grep 关键字 + 用到新模块要确认 import 存在 |
| 前端 JS/HTML | 拉服务端返回的 HTML，grep 新代码在不在（所有 `/api/*` 都 no-store） |
| 配置文件 | 读回 JSON 打印，确认值写对了 |
| 指令词表 | `python scripts/archive/dump_commands.py` 看匹配结果 |
| 调度/定时逻辑 | 等一个周期，看日志有没有跑 |

快捷入口：项目里有 `scripts\verify.ps1`（如已创建）——一条命令跑完上面能自动化的部分。

---

## 5. Git 使用手册（本项目）

仓库在 `D:\QQNTBOT` 本地，分支 `main`。策略：**完整保全**——依赖、运行时、改造版二进制、构建产物全部纳入，能整机恢复；只排除活动数据库、凭证、编译缓存。

### 日常三连

```powershell
cd D:\QQNTBOT
git status                      # 1. 改了什么
git add -A                      # 2. 暂存（或用 git add <具体文件> 更精确）
git commit -m "fix: 一句话说明改了什么"   # 3. 留痕
```

commit message 约定（Conventional Commits，让人一眼看懂）：
- `fix: ...` 修 bug
- `feat: ...` 加功能
- `chore: ...` 配置/依赖/杂项
- `docs: ...` 文档
- `refactor: ...` 重构

### 核对 AstrBot 补丁是否被升级覆盖

```powershell
# 看这 6 处文件的改动历史；升级后如果 diff 变了，说明补丁被冲掉了
git log --oneline -- apps/AstrBot/astrbot/core/pipeline/respond/stage.py
git diff HEAD -- apps/AstrBot/astrbot/
```

6 处补丁的清单在 [PROJECT.md §14](PROJECT.md)。

### 出问题回滚

```powershell
git log --oneline -20            # 找到出事前的那个 commit
git checkout <commit号> -- <文件路径>   # 只还原某个文件
# 或整库回到某版本（谨慎，会丢之后的改动）：
git reset --hard <commit号>
```

### 哪些东西不在 Git 里，要单独备份

- **数据库**：`data\memory.db`（长期记忆）、`data\caption_cache.db`、`apps\AstrBot\data\data_v4.db`（会话/消息历史）。这些实时写入，Git 存不了。定期在**停机后**复制到别处。
- **凭证**：`apps\NapCat\config\webui.json`（WebUI token）、`_tmp_*`。泄露风险，绝不入库。
- **DeepSeek API key**：目前 `cmd_config.json` 里是空的。真要填时，填完立刻确认它没被 Git 跟踪。

---

## 6. 提示词怎么拼、一轮消息调几次模型

这是 2026-11-19 做的源码级分析结论，接手时不必重新读全部代码：

**提示词拼接**（发往主模型的 system_prompt，6 层叠加）：
1. 人格 persona（框架按 `persona_id=grey` 注入）
2. 长期记忆（ltm 插件，向量召回）
3. 群图上下文（vision_context 插件，最近 3 张图释义）
4. 联网搜索（websearch 插件，像问句时）
5. 群聊格式 + STRICT_HINT（peer 插件）
6. 群历史块（group_chat_context，`extra_user_content_parts`）

所有 `on_llm_request` 钩子按加载顺序串行改同一个 req 对象，在 `reset()` 时一次性烘焙进消息列表，工具循环各轮复用、不重复注入。

**关键配置事实**（容易和文档描述混淆）：
- `group_icl_enable=false` → 第 6 层群历史块**当前未注入**；你感觉到的"上下文"来自 AstrBot 自己的会话历史（conversation contexts，`max_turns=12`）。
- 连带：判官的 `{recent}` 输入是空的（raw_records 只在 group_icl 开启时填充），判官目前在"盲判"单条消息——这可能是它准确率不稳的隐藏原因。

**调用次数**：主模型 `N = 1 + 工具调用轮数`，通常 1 次（`max_steps` 上限 128）。完整账本见本次对话的分析；一条群消息涉及：判官 8082（未 @ 时 1 次）+ 主模型（1+工具轮）+ 向量召回 8097（1 次）+  SearXNG 9000（问句时）。

**两处待办**（本次发现，尚未修改）：
- 表情标记 `&&...&&` 的清理规则 `&&[a-zA-Z]*&&` 只认纯字母，模型输出带数字/下划线的 ID 会残留成乱码 → 建议在 peer 后处理做白名单校验（符合 LESSONS.md §6）。
- `ltm.learn_from_turn` 的回复后抽取没做第三方模式检查，当前模式下会徒劳调用已停的 8080（被 except 吞掉，只是记 warning）。

---

## 7. 我在这个项目里的判断原则

接手者请记住这条（来自 LESSONS.md §11，被反复验证过）：

> **用户对"体感"的判断通常比 AI 对"机制"的推断更准。** 遇到分歧，先按体感去找机制，别先用机制否定体感。

换句话说：你说"表现差"、"这里不对"，先当真、先复现，再去代码里找原因，而不是先解释"按设计不该如此"。
