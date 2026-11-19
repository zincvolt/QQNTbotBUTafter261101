from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\astrbot\builtin_stars\astrbot\group_chat_context.py")
s = p.read_text(encoding="utf-8")

# 1) 配置加载：dual_judge / 9B 端点
loader = '''

def load_dual_judge() -> dict:
    """读取双判官配置。

    Returns:
        dict: ``enable``(bool) 与 ``model``(str)。
    """
    data = {"enable": False, "model": ""}
    try:
        raw = json.loads(REPLY_CONFIG_PATH.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, OSError):
        return data
    data["enable"] = bool(raw.get("dual_judge", False))
    data["model"] = str(raw.get("dual_judge_model", "")).strip()
    return data

'''
if "def load_dual_judge" not in s:
    s = s.replace("\n\ndef load_history_window()", loader + "\ndef load_history_window()", 1)

# 2) 9B 复核方法
judge9 = '''
    async def _judge_with_main(self, prompt: str, model: str) -> bool | None:
        """用主模型（9B）复核一次判定。

        Args:
            prompt: 判官提示词。
            model: 主模型名。

        Returns:
            bool | None: True=同意回复，False=否决，None=调用失败（视为同意）。
        """
        if not model:
            return None
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    MAIN_JUDGE_URL,
                    headers={"Authorization": f"Bearer {MAIN_JUDGE_KEY}"},
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 4,
                        "temperature": 0.2,
                        "grammar": 'root ::= "0" | "1"',
                        "chat_template_kwargs": {"enable_thinking": False},
                    },
                )
                resp.raise_for_status()
                verdict = resp.json()["choices"][0]["message"]["content"].strip()
            logger.info(f"group judge | 9B 复核 verdict={verdict[:4]}")
            return verdict.startswith("1")
        except Exception as exc:  # noqa: BLE001 - 失败就放行
            logger.warning(f"group judge | 9B 复核失败，按同意处理: {exc}")
            return None

'''
anchor = "    async def _judge_reply(self, event: AstrMessageEvent, cfg: dict) -> bool:"
if "_judge_with_main" not in s:
    s = s.replace(anchor, judge9 + anchor, 1)

p.write_text(s, encoding="utf-8")
print("dual judge scaffolding added")
