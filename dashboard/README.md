# QQNT Bot 控制台（dashboard）

一个单页的运维面板：看进程/内存、读日志、改人格与判官、调采样参数、管记忆和群权限。
后端 FastAPI，前端纯原生 HTML + 一个 `<script>`，没有构建步骤。

> 这是「给完整安装用的运维面板」，不是独立产品。大部分面板读的是 AstrBot / NapCat
> 的运行时数据，所以**换成一份没有那些数据的代码仓时，对应面板会自动置灰**，而不是报错或空白。

## 快速启动

### 场景 1：完整安装（有 `D:\QQNTBOT` 全套环境）

```powershell
# 随整套服务一起起
.\start-all.ps1

# 或只起控制台
.\scripts\start-dashboard.ps1
```

打开 <http://127.0.0.1:6190>。

### 场景 2：只有这份代码仓，手动起

```powershell
# 用你本机的 Python；也可以指向 AstrBot 的 venv
pip install -r dashboard\requirements.txt

cd dashboard
python -m uvicorn app:app --host 127.0.0.1 --port 6190
```

启动时控制台会打印实际使用的项目根目录（`ROOT = ...`），先确认它指对了地方。

### 场景 3：路径不在默认位置

```powershell
$env:QQNTBOT_ROOT = "E:\somewhere\QQNTBOT"
cd E:\somewhere\QQNTBOT\dashboard
python -m uvicorn app:app --port 6190
```

## 环境变量

| 变量 | 作用 | 默认值 |
|---|---|---|
| `QQNTBOT_ROOT` | 项目根目录（下面有 `data/`、`apps/`） | 自动推断：`app.py` 所在 `dashboard/` 的上一级 |
| `LLAMA_MODELS_INI` | 本地模型预设清单 | `D:\LLM\scripts\models.ini` |
| `LLAMA_LOG_FILE` | 模型路由日志 | `D:\LLM\logs\llama-router.log` |
| `QQNTBOT_PYTHON` | 启动脚本用的 Python（仅 `start-dashboard.ps1`） | `<ROOT>\apps\AstrBot\.venv\Scripts\python.exe` |
| `QQNTBOT_DASH_PORT` | 监听端口（仅 `start-dashboard.ps1`） | `6190` |

路径推断逻辑写在 `app.py` 的 `_detect_root()`：环境变量 > 目录结构 > 旧的硬编码
`D:\QQNTBOT`。所以在原来的机器上行为完全不变，换台机器也能跑。

## 接口缺失时自动置灰

每个面板声明自己依赖哪些能力（HTML 上的 `data-caps`），页面启动时先请求
`GET /api/capabilities`，拿到一张能力表，再把缺失能力对应的面板整体置灰：

- 面板半透明、内部所有 `button/input/select/textarea` 变 `disabled`
- 面板顶部插入一行 `⚠ 不可用：<具体原因>`，例如「缺少记忆数据库 memory.db」
- 单个按钮也可以声明 `data-cap`，只在自身能力缺失时禁用（如「试一下」判官、「启动/停止全部」）

能力表长这样（`available: false` 时附 `reason`）：

```json
{
  "config":  {"available": false, "reason": "缺少 apps/AstrBot/data/cmd_config.json"},
  "botdb":   {"available": false, "reason": "缺少聊天数据库 data_v4.db"},
  "memdb":   {"available": false, "reason": "缺少记忆数据库 memory.db"},
  "judge":   {"available": true,  "reason": ""},
  "cores":   "..."
}
```

**双保险**：就算能力表本身拿不到（比如前端配了一个老版本后端，`/api/capabilities`
404），每个面板的 `fetch` 也走统一的 `api()` 包装——请求失败、超时（9 秒）、或返回
非 JSON 时，同样会把该面板置灰并写出原因。所以「没有对应接口」一定会变成「置灰」，
不会卡在「加载中…」。

## 面板 ↔ 数据来源 ↔ 能力

| 面板 | 读/写什么 | 能力键 | 缺什么会置灰 |
|---|---|---|---|
| 系统状态 | psutil、端口探测 | `core` | 永不置灰 |
| 手动加记忆 | `memory.db` → 写向量库 8097 | `memdb,botdb,embedding` | 缺任一 |
| 最近记住的事 | `data/memory.db` | `memdb` | 缺库 |
| 最近对话 | AstrBot `data_v4.db` | `botdb` | 缺库 |
| 触发权限 / 水群 | `cmd_config.json` | `config` | 缺配置 |
| 本地优化 / 第三方精简 | `data/reply.json` | — | 缺文件会自动创建 |
| 记忆提取提示词 | `data/ltm_prompt.txt` | — | 缺文件会自动创建 |
| 审查 · 额度 | `cmd_config.json` | `config` | 缺配置 |
| 人格 | `data/persona.json` | — | 缺文件会自动创建 |
| 判官 | `data/judge.json`；试判调 8082 | — / `judge` | 仅「试一下」按钮 |
| 判官与思维链 | `cmd_config.json` | `config` | 缺配置 |
| 回复行为 | `data/reply.json` | — | — |
| 模型采样参数 | `cmd_config.json` | `config` | 缺配置 |
| 对话上下文 | AstrBot `data_v4.db` | `botdb` | 缺库 |
| 自动接话开关 | `cmd_config.json` + `data_v4.db` | `config,botdb` | 缺任一 |
| 主模型 | `cmd_config.json` + `models.ini` | `models` | 缺任一 |
| 识图 | `data/vision_mode.json`；启停 VL 调 8085 | — / `vl` | 仅启停按钮 |
| 图片理解 | `data/caption_cache.db` | `caption` | 缺库 |
| 已装模块 | `apps/AstrBot/data/plugins/` | `plugins` | 缺目录 |
| 运行日志 | NapCat / AstrBot / 模型路由日志 | `logs` | 找不到日志 |

## 依赖

见 `requirements.txt`。当前实测版本：fastapi 0.163 / uvicorn 0.54 / httpx 0.28 / psutil 7.1。

## 安全

- 只绑 `127.0.0.1`，不要暴露到公网。
- **没有登录鉴权**，能访问端口就能改人格/配置/启停服务。需要远程用时请自己套一层反代 + 认证。
- 所有 `/api/*` 和 `/` 都返回 `no-store`，避免改了代码看不到变化。

## 排错

| 现象 | 原因 | 处理 |
|---|---|---|
| 面板显示「⚠ 不可用：缺少…」 | 该功能依赖的数据/服务不在 | 按提示补数据，或确认 `ROOT` 指对了 |
| 整个页面都是灰的 | `ROOT` 推断错了 | 设 `QQNTBOT_ROOT` 后重启 |
| 启动报 `ModuleNotFoundError` | 没装依赖 | `pip install -r requirements.txt` |
| 端口被占 | 6190 已被别的进程用 | 换端口 `--port 6191` |
| 页面 404 | 工作目录不对 | 必须在 `dashboard/` 下执行 `uvicorn app:app` |
