from pathlib import Path
p = Path(r"D:\QQNTBOT\docs\LESSONS.md")
s = p.read_text(encoding="utf-8")

add = '''

### 附：同一类问题的第二、第三次形态

**第二次：用了没导入的模块（`Image`）**

`_attach_meme()` 里用 `Image.fromFileSystem()`，但文件里只 import 了 `Plain`。
`py_compile` 通过（运行时才求值），直到发表情包时才抛 `AttributeError`。

**第三次：用了没导入的模块（`time`）**

加回复预算时写 `time.time()`，但 `group_chat_context.py` 只导入了 `datetime`。
每次群友说话都抛 `NameError`，表现是"@ 它能回，不 @ 就完全不说话"。

**共同点**：`py_compile` 只检查语法，**查不出 NameError 和 AttributeError**。
所以"编译通过"不等于"能跑"。

**现在的验证清单**：

| 改动类型 | 必须做的验证 |
|---|---|
| 新增函数/方法 | `python -c "import module"` 或实际调用一次 |
| 用到新模块 | grep 确认 import 存在 |
| 前端 JS | 拉服务端 HTML，grep 新代码在不在 |
| 配置写入 | 读回 JSON 打印 |
| 调度/定时逻辑 | 等一个周期，看日志有没有跑 |

一句话：**验证"运行过"，不是验证"编译过"**。
'''
if "第二次：用了没导入的模块" not in s:
    anchor = "\n---\n\n## 2. 前端"
    s = s.replace(anchor, add + "\n---\n\n## 2. 前端", 1)
    p.write_text(s, encoding="utf-8")
    print("lessons updated")
