# 新插件部署指南

> 权限闸门插件（astrbot_plugin_access）配套文档。
> 本文讲「怎么把一个新插件安全地部署进本机 AstrBot」；指令怎么接入统一权限管理见同目录 `COMMAND-GUIDE.md`。
> 通用插件开发规范见仓库 `docs/MODULE-GUIDE.md`，指令总表见 `docs/PLUGIN-COMMANDS.md`。

## 1. 目录结构

```
apps/AstrBot/data/plugins/astrbot_plugin_<名字>/
├── main.py            # 必需，入口
├── metadata.yaml      # 必需
├── _conf_schema.json  # 有 WebUI 可配项时需要
└── (其他模块文件)
```

`metadata.yaml` 至少包含 `name` / `desc` / `author` / `version`；`desc` 里写明用途和配套文档位置。

## 2. 必守的框架约定（都踩过坑）

### 2.1 构造函数必须收 config

```python
class MyPlugin(star.Star):
    def __init__(self, context: star.Context, config=None) -> None:
        super().__init__(context, config=config)
        self.config = config
```

star_manager 以 `config=plugin_config` 关键字实例化；签名不收 config 会抛 TypeError 被**框架静默降级**为无 config 构造，配置读空且不报错。

### 2.2 配置读写

- AstrBot 主配置用 `self.context.get_config()`（Context 没有 `astrbot_config` 属性，第一版栽过）。
- 改配置后必须 `cfg.save_config()`。
- 自己的 JSON 状态文件写入遵循**合并原则**：只覆盖请求真带了的字段，空列表视为「这次没传」，清空要显式标记（如 `clear_rules: true`）。

### 2.3 优先级：不要用 maxsize 力大砖飞

access 加载时会把全部 handler 分档排序：**闸门 > 指令类（CommandFilter + 手写指令插件）> 纯监听**，插件自己写的 `priority`（包括 maxsize）全部失效。新插件：

- 用 `@filter.command` 的指令不用管；
- 手写指令匹配的 listener，把模块名加进 access `main.py` 的 `_CMD_LISTENER_MODS`；
- 纯监听不用管。

### 2.4 输出通道：长输出/图卡用 `event.send()` 直发

图卡的消息链纯文本为空，走 `yield` 的 result 处理通道会被 peer 的 `on_decorating_result` 误判为「LLM 空回复」整链清空并停事件——**图发了但那是在别的改动之前的事，表现为指令无响应**。凡是输出图卡（`event.image_result`）或长列表，一律：

```python
await event.send(event.image_result(str(path)))
# 或 async for r in self._do_xxx(...): await event.send(r)
```

并在处理完自己的指令后 `event.stop_event()`。一图流绘卡直接复用本插件的 `card_render.py`（PIL 暗色卡 + SHA256 内容指纹缓存，内容不变不重画），惰性 import，绘卡失败要降级或报错，**不得拖垮插件主功能**。

### 2.5 指令自声明

必备，写法见 `COMMAND-GUIDE.md` §3。没有声明会在 `/权限 列表` 被点名，纯被动插件不会出现在公开 `/指令` 卡。

## 3. 部署与热更新

1. 把插件目录放进 `apps/AstrBot/data/plugins/`。
2. 热加载：`scripts\restart-astrbot.ps1`（约 10 秒，QQ 不断线）。
3. **绝不重启 QQ**——重启要重新扫码，且有风控风险。改插件/改 AstrBot 配置永远走热重启脚本。
4. 确认加载成功：看 AstrBot 日志有无 import 报错；`/权限 列表` 里能看到你的插件分组。

## 4. 改代码的验证铁律

`str.replace()` 静默失败最贵。改完**必须验证运行过，不是验证编译过**：

- Python：`py_compile` + grep 关键字确认替换生效 + 用到新模块要确认 import（py_compile 查不出 NameError/AttributeError）。
- 涉及前端：拉服务端 HTML grep 新代码（所有 `/api/*` 和 `/` 都 no-store）。
- 配置改动：读回 JSON 打印确认实际值。
- 排查顺序：日志报错 → 端口/进程 → 配置实际值 → 代码调用点 → 最后才猜。

## 5. 兼容性要求（单拎可用）

每个插件单独拎出来（脱离本机其他插件环境）也要能跑：

- 权限判断：优先 import access 的 `unified_perm`，失败 fallback 到 AstrBot 原生 `admins_id`。
- 不 import 其他自制插件的主模块；共享能力（绘卡、统一权限）做成可选依赖并降级。
- 生图前用内容指纹（SHA）对比，内容不变不重复渲染。

## 6. 上线前检查清单

- [ ] metadata.yaml 齐全，desc 提到配套文档
- [ ] `restart-astrbot.ps1` 热加载后日志无报错
- [ ] `/权限 列表` 分组正常，`/指令` 公开卡内容正确
- [ ] 普通用户实测：该拦的拦、该放的放
- [ ] 多群自查：状态全部按群号/umo/发送者分键，不会跨群触发、不会回错位置
- [ ] 删掉本插件目录，其他插件不受影响（无反向依赖）
