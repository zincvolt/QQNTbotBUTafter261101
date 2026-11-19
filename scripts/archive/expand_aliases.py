from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py")
s = p.read_text(encoding="utf-8")

fixes = [
 ('("recent", re.compile(r"(最近.{0,4}(展|兽聚)|近期.{0,4}(有什么|有啥)|最近的展)")),',
  '("recent", re.compile(r"(近期展|近期兽聚|最近有什么|最近有哪些|最近的展|前瞻|展会一览|近期活动)")),'),
 ('("next", re.compile(r"(下次展|下一次展|下一场|下次兽聚|最近的兽聚|还有几天|倒计时|下一届)")),',
  '("next", re.compile(r"(下次展|下一次展|下一场|下次兽聚|最近的兽聚|还有几天|倒计时|下一届|下场展)")),'),
 ('("fortune", re.compile(r"(运势|今天运气|今日运气|抽个签|求签|吉凶)")),',
  '("fortune", re.compile(r"(运势|运气|抽个签|求签|吉凶|今日份|转运)")),'),
 ('("stats", re.compile(r"(群统计|发言统计|谁最活跃|水群榜|活跃度)")),',
  '("stats", re.compile(r"(群统计|发言统计|谁最活跃|水群榜|活跃度|话最多|谁话多)")),'),
 ('("city_past", re.compile(r"(哪里|哪个城市|哪).{0,6}(上次|上一次|办过).{0,4}(展|兽聚)")),',
  '("city_past", re.compile(r"((哪里|哪个城市|哪).{0,6}(上次|上一次|办过|过去).{0,4}(展|兽聚)|办过什么展|上次展|上一次展)")),'),
 ('("city_next", re.compile(r"(哪里|哪个城市|哪).{0,6}(下次|下回|接下来).{0,4}(展|兽聚)")),',
  '("city_next", re.compile(r"((哪里|哪个城市|哪).{0,6}(下次|下回|接下来|将来).{0,4}(展|兽聚)|下次展在哪|城市下次展)")),'),
 ('("city_list", re.compile(r"(有什么展|有哪些展|有啥展|有什么兽聚|哪有展|有什么活动)")),',
  '("city_list", re.compile(r"(有什么展|有哪些展|有啥展|有什么兽聚|哪有展|有什么活动|哪里的展|本地展)")),'),
]
for old, new in fixes:
    if old in s:
        s = s.replace(old, new, 1)
        print("ok:", new[:38])
    else:
        print("MISS:", old[:38])
p.write_text(s, encoding="utf-8")
