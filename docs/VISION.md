# 本地读图（VL 模型）

> 当前装的是 **Qwen3-VL-4B-Instruct**（Q4_K_M + Q8 mmproj），跑在 `127.0.0.1:8085`。
> 最后更新：2026-11-18

---

## 1. 为什么用本地 VL

第三方模式（DeepSeek）下，图片有两条路：

| 方式 | 谁在看图 | 成本 | 速度 |
|---|---|---|---|
| 第三方 | DeepSeek 直接看 | 1000~2000 tokens/张 | 快 |
| **本地** | Qwen3-VL-4B 转成文字，再塞给 DeepSeek | **0 token** | 慢（约 11 秒/张） |

本地模式的好处是**图片一个字都不出本机**，坏处是慢。

## 2. 文件与端口

| 项 | 值 |
|---|---|
| 模型 | `D:\LLM\models\Qwen3VL-4B-Instruct-Q4_K_M.gguf`（2.38 GB） |
| mmproj | `D:\LLM\models\mmproj-Qwen3VL-4B-Instruct-Q8_0.gguf`（433 MB） |
| 启动脚本 | `D:\LLM\scripts\start-vl.ps1`（QQNTBOT 里留了同名薄封装） |
| 端口 | 8085 |
| API Key | `sk-vl-local` |
| AstrBot provider | `vl-local`（可在 WebUI 模型提供商里选） |
| 日志 | `D:\LLM\logs\vl.out` / `vl.err` |

`start-all.ps1` 已经把它并进第 3 步，开机自动拉起。

## 3. 切换命令

```
/读图 本地        本地 VL 转文字（默认）
/读图 第三方      交给 DeepSeek 看
/读图 关          忽略图片，完全不读
/读图             看当前状态和本地 VL 是否在线
```

状态文件：`data\vision_mode.json`

```json
{"mode": "local", "port": 8085, "model": "Qwen3VL-4B-Instruct"}
```

## 4. 什么时候才真的读图

不管哪种模式，都先过一道判断（`astrbot_plugin_peer` 里的 `_should_read_images`）：

- 命中「截图 / 看图 / 这是什么 / 什么字 / 翻译…」→ 读
- 句子里有问号 → 读
- 图片 ≥ 3 张 → 读
- 单张 > 60KB → 读
- 其余当表情包 → **跳过**

所以群里刷表情包不会触发读图，也不会让本地 VL 白跑 11 秒。

## 5. 本地 VL 不可用时

`_caption_local()` 失败（服务没起、超时、报错）会返回固定文案：

```
（读图能力不可用）
```

这段文字会被塞进提示词，模型看到就知道没读到图，不会瞎编内容。

## 6. 为什么选 4B 而不是 2B / 8B

| 模型 | 大小 | 单图耗时 | 质量 |
|---|---|---|---|
| Qwen3-VL-2B | ~1.3GB | 3~5 秒 | 描述偏简略，文字容易漏 |
| **Qwen3-VL-4B** | ~2.4GB | **11 秒** | 够用，能读图和中文 |
| Qwen3-VL-8B | ~5GB | 20 秒+ | 更好，但本机是共享显存的 Arc |

本机是 Intel Arc B370（共享显存），跑 4B 时单图约 11 秒，可接受。

## 7. 排错

| 现象 | 处理 |
|---|---|
| `/读图` 显示离线 | 跑 `scripts\start-vl.ps1`，看 `_backup\vl.err` |
| 一直返回「读图能力不可用」 | 检查 8085 是否监听、api-key 是否 `sk-vl-local` |
| 太慢（>20 秒） | 换 2B，或改用 `/读图 第三方` |
| 描述不准 | 4B 上限，建议第三方模式看图 |

## 8. 在 AstrBot 里怎么管

模型文件与启动脚本都在 **D:\LLM**，AstrBot 只当一个 OpenAI 兼容服务来用。
WebUI → 模型提供商 里现在能看到：

| provider id | 模型 | 地址 | 用途 |
|---|---|---|---|
| `vl-local` | Qwen3VL-4B-Instruct | `http://127.0.0.1:8085/v1` | 通用读图/描述 |
| `ocr-local` | PaddleOCR-VL-1.6 | `http://127.0.0.1:8083/v1` | 只认文字（OCR） |
| `local-embed` | bge-small-zh-v1.5 | `http://127.0.0.1:8097/v1` | 知识库嵌入 |

`vl-local` 带 `modalities: ["image","text"]`，所以：

- 可以把它设成「图片理解提供商」，走 AstrBot 自带的图片转文字
- 也可以被别的插件直接按 OpenAI 接口调用

新增模型时只要：模型文件放 `D:\LLM\models` → 写个启动脚本放 `D:\LLM\scripts` →
在 cmd_config 的 `provider` 里加一条 → 重启 AstrBot。
