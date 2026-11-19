from pathlib import Path
p = Path(r"D:\QQNTBOT\docs\VISION.md")
s = p.read_text(encoding="utf-8")

s = s.replace(
    "| 启动脚本 | `scripts\\start-vl.ps1` |",
    "| 启动脚本 | `D:\\LLM\\scripts\\start-vl.ps1`（QQNTBOT 里留了同名薄封装） |",
)
s = s.replace(
    "| 日志 | `_backup\\vl.out` / `_backup\\vl.err` |",
    "| 日志 | `D:\\LLM\\logs\\vl.out` / `vl.err` |",
)
s = s.replace(
    "| API Key | `sk-vl-local` |",
    "| API Key | `sk-vl-local` |\n| AstrBot provider | `vl-local`（可在 WebUI 模型提供商里选） |",
)

extra = """
## 8. 在 AstrBot 里怎么管

模型文件与启动脚本都在 **D:\\LLM**，AstrBot 只当一个 OpenAI 兼容服务来用。
WebUI → 模型提供商 里现在能看到：

| provider id | 模型 | 地址 | 用途 |
|---|---|---|---|
| `vl-local` | Qwen3VL-4B-Instruct | `http://127.0.0.1:8085/v1` | 通用读图/描述 |
| `ocr-local` | PaddleOCR-VL-1.6 | `http://127.0.0.1:8083/v1` | 只认文字（OCR） |
| `local-embed` | bge-small-zh-v1.5 | `http://127.0.0.1:8097/v1` | 知识库嵌入 |

`vl-local` 带 `modalities: ["image","text"]`，所以：

- 可以把它设成「图片理解提供商」，走 AstrBot 自带的图片转文字
- 也可以被别的插件直接按 OpenAI 接口调用

新增模型时只要：模型文件放 `D:\\LLM\\models` → 写个启动脚本放 `D:\\LLM\\scripts` →
在 cmd_config 的 `provider` 里加一条 → 重启 AstrBot。
"""
s = s.rstrip() + "\n" + extra
p.write_text(s, encoding="utf-8")
print("VISION.md 已更新:", len(s.splitlines()), "行")
