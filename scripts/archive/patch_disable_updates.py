from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\astrbot\core\updater.py")
s = p.read_text(encoding="utf-8")

if "LOCAL_UPDATES_DISABLED" not in s:
    # 1) 常量
    anchor = "class AstrBotUpdater(_RepoZipUpdater):"
    s = s.replace(anchor,
        "# 本地部署：禁止自动升级，否则 5 处源码补丁会被覆盖\n"
        "LOCAL_UPDATES_DISABLED = True\n\n\n" + anchor, 1)

    # 2) check_update 直接返回"已是最新"
    old_check = '''        return await self._check_update(
            self._release_api,
            VERSION,
            consider_prerelease,
        )'''
    new_check = '''        if LOCAL_UPDATES_DISABLED:
            logger.info("自动升级已禁用（本机部署），跳过检查")
            return None
        return await self._check_update(
            self._release_api,
            VERSION,
            consider_prerelease,
        )'''
    if old_check in s:
        s = s.replace(old_check, new_check, 1)

    # 3) update() 直接拒绝
    old_update = '''        async def emit_progress(
            stage: Literal["dashboard", "core", "verify", "apply"],'''
    new_update = '''        if LOCAL_UPDATES_DISABLED:
            raise RuntimeError(
                "自动升级已禁用（本机部署），升级会覆盖源码补丁。"
                "确需升级请先备份并临时修改 updater.py"
            )

        async def emit_progress(
            stage: Literal["dashboard", "core", "verify", "apply"],'''
    if old_update in s:
        s = s.replace(old_update, new_update, 1)

p.write_text(s, encoding="utf-8")
print("patched:", "LOCAL_UPDATES_DISABLED" in s)
