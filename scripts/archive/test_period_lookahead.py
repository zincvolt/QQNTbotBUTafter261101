"""Verify the sentence-end period rewrite handles trailing parenthetical actions."""

import re

# 关键：句号后面是 空白/结尾/开括号 时算句末；用前瞻(?=...)，不消耗后面的字符
PATTERN = "。(?=\\s|$|[（(\\[【「『])"

CANDIDATES = [
    "行吧。那我先躺一会。",
    "你好。（歪头）",
    "真的吗。（歪头）晚安。",
    "说完了。 （动作）",
    "第一句。第二句。第三句。",
    "好的。。",
    "（揉眼）行吧。",
    "就这样吧。(smile)",
    "嗯。」",
    "他说。（小声）我听见了。（笑）",
]


def main() -> None:
    """Print before/after for each sample."""
    pattern = re.compile(PATTERN)
    for text in CANDIDATES:
        print(f"{text!r}\n   -> {pattern.sub('~', text)!r}")
    print("\n最终使用: ", PATTERN)


if __name__ == "__main__":
    main()
