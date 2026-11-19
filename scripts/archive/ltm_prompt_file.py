from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_ltm\main.py")
s = p.read_text(encoding="utf-8")

# 1) 提示词改从文件读，文件不存在时回落到内置常量
old = '''EXTRACT_PROMPT = """从下面这段对话里提取关于「用户」的、可长期记住的稳定事实。'''
new = '''PROMPT_FILE = Path(r"D:\\QQNTBOT\\data\\ltm_prompt.txt")

EXTRACT_PROMPT = """从下面这段对话里提取关于「用户」的、可长期记住的稳定事实。'''
if old in s and "PROMPT_FILE" not in s:
    s = s.replace(old, new, 1)

helper = '''

def load_prompt() -> str:
    """Return the extraction prompt, preferring the editable file.

    Returns:
        Prompt template containing ``{user}`` and ``{bot}`` placeholders.
    """
    try:
        text = PROMPT_FILE.read_text(encoding="utf-8")
        if "{user}" in text and "{bot}" in text:
            return text
        logger.warning("[ltm] ltm_prompt.txt 缺少占位符，回落到内置提示词")
    except OSError:
        pass
    return EXTRACT_PROMPT

'''
if "def load_prompt()" not in s:
    anchor = "def _cosine("
    s = s.replace(anchor, helper.lstrip("\n") + anchor, 1)

# 2) 调用处换成 load_prompt()
s = s.replace("EXTRACT_PROMPT.replace(", "load_prompt().replace(")
p.write_text(s, encoding="utf-8")
print("ltm 提示词改为文件驱动")
