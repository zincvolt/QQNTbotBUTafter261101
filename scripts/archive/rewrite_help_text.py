"""Rewrite the help text so it matches actual behaviour."""

from pathlib import Path

PLUGIN = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py")
s = PLUGIN.read_text(encoding="utf-8")

new_help = '''HELP_TEXT = """可用指令（所有人可用，需本群已启用）

▍展会
/下次展            最近那一场（单场卡）
/江苏下次展        该城市/省份最近那一场（单场卡）
/近期展            近期 10 场 + 刚结束 2 场
/江苏近期展        该城市/省份的展会列表（最多 6 场）
/江苏有什么展      同上
/江苏上次展        该城市/省份办过的展会（灰色卡片）

▍其他
/运势              今日人品（也支持 /jrrp /jrys /人品）
/群统计            本群近 7 天活跃
/兽聚help          这张说明

▍管理员
/启用功能          开启本群功能
/关闭功能          关闭本群功能
/关心 <展会名> [HH:MM]   设为特别关心，每天定时播报倒计时
/取消关心          关掉播报

也可以直接喊「阿灰 下次展」「小灰 运势」"""'''

start = s.index('HELP_TEXT = """')
end = s.index('"""', start + len('HELP_TEXT = """')) + 3
s = s[:start] + new_help + s[end:]
PLUGIN.write_text(s, encoding="utf-8")
print("help text rewritten")
