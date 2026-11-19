"""Update docs for the period rule and meme mood scoring."""

from pathlib import Path

PROJECT = Path(r"D:\QQNTBOT\docs\PROJECT.md")
LESSONS = Path(r"D:\QQNTBOT\docs\LESSONS.md")

# ---- PROJECT §5 文本后处理 ----
p = PROJECT.read_text(encoding="utf-8")
old_rule = '''```json
{"pattern": "。(?=\\\\s|$)", "to": "~"}
```

只替换句末句号，中间的句子不受影响。'''
new_rule = '''```json
{"pattern": "。(?=\\\\s|$|[（(\\\\[【「『])", "to": "~"}
```

只替换**句末**句号，中间的句子不受影响。

"句末"的定义包含三种情况：后面是空白、后面是结尾、**后面紧跟括号动作**。
第三条是后补的——模型常把动作放句尾写成 `你好。（歪头）`，
最初的正则只认空白和结尾，这种就漏掉了，表现是"规则突然失效"。

注意必须用前瞻 `(?=...)`，不能用捕获组，否则括号会被一起吃掉。'''
if old_rule in p:
    p = p.replace(old_rule, new_rule, 1)
    print("PROJECT 5 updated")
else:
    print("PROJECT 5 pattern missing")

# ---- PROJECT §8 表情情绪打分 ----
old_meme = '''2. **随机附带**：正常回复按 30% 概率挂一张，按回复情绪选分类（控制台可调 0~100%）'''
new_meme = '''2. **随机附带**：正常回复按 30% 概率挂一张（控制台可调 0~100%）'''
if old_meme in p:
    p = p.replace(old_meme, new_meme, 1)
    anchor = '''3. **模型自己调工具**：`send_meme` 可用，但 9B 在长提示下经常不调'''
    detail = '''3. **模型自己调工具**：`send_meme` 可用，但 9B 在长提示下经常不调

**第 2 种的分类怎么选**：不是随机抽，而是按情绪打分。

```
12 类情绪词库，每个词带权重 1~3
用户消息命中权重 × 2  +  机器人回复命中权重 × 1  =  该分类得分
取最高分；全部 0 分才全库随机
```

同一个词可以在多个分类里带不同权重，用来消歧：

| 词 | 归属 |
|---|---|
| 离谱 | 无语 2 / 生气 1 / 惊讶 1 → 判成**无语** |
| 算了 | 无语 1 / 拒绝 1 → 看其他词谁加分 |
| 不想 | 拒绝 2 |

日志：`[peer] meme mood 难过 scores={'难过': 10, '拒绝': 1}`'''
    if anchor in p:
        p = p.replace(anchor, detail, 1)
        print("PROJECT 8 updated")
PROJECT.write_text(p, encoding="utf-8")

# ---- LESSONS 新增两条 ----
t = LESSONS.read_text(encoding="utf-8")
add = '''
---

## 13. 正则的捕获组会吃掉字符

**症状**：想"把句末句号换成波浪号"，规则写好后括号动作被删掉了：

```
你好。（歪头）  ->  你好~歪头）
```

**原因**：写成了捕获组 `。(\\s|$|[（(\[])`。
`re.sub` 替换的是**整个匹配**，捕获组里的那个括号也算在匹配里，一起被替换成 `~`。

**正确写法**：用前瞻，只匹配、不消耗。

```python
"。(\u5c0f"  # 错误：捕获组
"。?=\\s|$|[（(\\[【「『])"  # 正确：前瞻，后面的字符原地保留
```

**推广**：凡是要"在某字符前插入/替换"的，先想清楚
**匹配的边界到底吃掉了几个字符**。这个错误我在测试脚本里连犯两次才发现。

---

## 14. 规则"突然失效"，多半是输入形态变了

**症状**：句末句号替换规则一直在跑，突然不生效了。

**不是规则坏了，是输入变了**：模型开始把动作放句尾，写成 `你好。（歪头）`，
句号后面跟着 `（`，不再满足"后面是空白或结尾"的条件。

**教训**：写文本规则时，不要只按"正常句式"设计边界，要枚举同类变体：

| 变体 | 例子 |
|---|---|
| 句末无动作 | `行吧。` |
| 句末带动作 | `你好。（歪头）` |
| 动作在句中 | `他说。（小声）我听见了。` |
| 连续句号 | `好的。。` |
| 结尾带引号 | `嗯。」` |

改规则前先把这些列一遍，用它们跑测试，比拍脑袋改一次准得多。

'''
if "正则的捕获组会吃掉字符" not in t:
    LESSONS.write_text(t.rstrip() + "\n" + add, encoding="utf-8")
    print("LESSONS updated")

print("PROJECT 行数:", len(PROJECT.read_text(encoding="utf-8").splitlines()))
print("LESSONS 行数:", len(LESSONS.read_text(encoding="utf-8").splitlines()))
