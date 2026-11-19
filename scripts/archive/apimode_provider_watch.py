"""Watch the active provider and unload/restart local models on change."""

from pathlib import Path

APIMODE = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_apimode\main.py")
s = APIMODE.read_text(encoding="utf-8")

watcher = '''    def _current_provider_id(self) -> str:
        """Return the chat provider id configured in agent_runner.

        Returns:
            Provider id string, or an empty string when unreadable.
        """
        try:
            cfg = json.loads(CONFIG.read_text(encoding="utf-8-sig"))
            return str(
                cfg.get("agent_runner", {})
                .get("config", {})
                .get("model", {})
                .get("provider_id", "")
            )
        except (json.JSONDecodeError, OSError):
            return ""

    @filter.on_astrbot_loaded()
    async def watch_provider_switch(self) -> None:
        """Start the provider watcher."""
        import asyncio

        asyncio.create_task(self._provider_watch())

    async def _provider_watch(self) -> None:
        """Poll the active provider and react to local <-> API transitions."""
        import asyncio

        last = self._current_provider_id()
        while True:
            await asyncio.sleep(20)
            try:
                current = self._current_provider_id()
                if current == last:
                    continue
                was_api = "deepseek" in last
                is_api = "deepseek" in current
                if is_api and not was_api:
                    stopped = unload_local_models()
                    logger.info(f"[apimode] provider->API, unloaded {stopped}")
                elif was_api and not is_api:
                    start_local_models()
                    logger.info("[apimode] provider->local, starting local models")
                last = current
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"[apimode] provider watch failed: {exc}")

'''

if "_provider_watch" not in s:
    anchor = "    @filter.event_message_type(filter.EventMessageType.ALL)"
    s = s.replace(anchor, watcher + anchor, 1)
    APIMODE.write_text(s, encoding="utf-8")
    print("provider watcher 已加")
else:
    print("watcher 已存在")
