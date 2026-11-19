from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_peer\main.py")
s = p.read_text(encoding="utf-8")
old = """            text = result.get_plain_text().strip()
        except Exception:  # noqa: BLE001 - non-text results are left alone
            return
"""
new = """            text = result.get_plain_text().strip()
        except Exception:  # noqa: BLE001 - non-text results are left alone
            return
        # 模型报错时 AstrBot 会把 None 当字符串发出去，这里直接拦掉
        if text.lower() in ("none", "null", "nan", ""):
            logger.info("[peer] dropped empty/None reply")
            result.chain.clear()
            event.stop_event()
            return
"""
if old in s:
    p.write_text(s.replace(old, new), encoding="utf-8")
    print("patched mute filter")
else:
    print("pattern not found")
