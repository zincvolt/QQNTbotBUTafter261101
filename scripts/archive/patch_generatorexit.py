from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\astrbot\builtin_stars\astrbot\main.py")
s = p.read_text(encoding="utf-8")
old = """                except BaseException as e:
                    logger.error(traceback.format_exc())
                    logger.error(f"主动回复失败: {e}")"""
new = """                except GeneratorExit:
                    # 事件被插件 stop（比如直接发了表情包）时生成器会关闭，
                    # 这不是错误，别再打 traceback
                    raise
                except BaseException as e:
                    logger.error(traceback.format_exc())
                    logger.error(f"主动回复失败: {e}")"""
if old in s:
    s = s.replace(old, new, 1)
    p.write_text(s, encoding="utf-8")
    print("patched GeneratorExit")
else:
    print("pattern not found")
