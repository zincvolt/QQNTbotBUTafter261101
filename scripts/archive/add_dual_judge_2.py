from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\astrbot\builtin_stars\astrbot\group_chat_context.py")
s = p.read_text(encoding="utf-8")

# 常量：主模型判定端点
const = '''
MAIN_JUDGE_URL = "http://127.0.0.1:8080/v1/chat/completions"
MAIN_JUDGE_KEY = "sk-llm-7d41c9e2"

'''
if "MAIN_JUDGE_URL" not in s:
    s = s.replace("\nREPLY_CONFIG_PATH = Path(", const + "\nREPLY_CONFIG_PATH = Path(", 1)

# 在 _judge_reply 返回 verdict 前插入 9B 复核
old = '''            logger.info(f"group judge | verdict={verdict[:6]} | {message[:40]}")
            return verdict.startswith("1")'''
new = '''            logger.info(f"group judge | verdict={verdict[:6]} | {message[:40]}")
            if not verdict.startswith("1"):
                return False
            dual = load_dual_judge()
            if dual["enable"]:
                second = await self._judge_with_main(prompt, dual["model"])
                if second is False:
                    logger.info(f"group judge | 9B 否决: {message[:30]}")
                    return False
            return True'''
if old in s and "9B 否决" not in s:
    s = s.replace(old, new, 1)
    print("dual judge wired")

p.write_text(s, encoding="utf-8")
