import re
NAME_CALL = r"(阿灰|小灰|灰狼)"
COMMANDS = [
    ("help", re.compile(r"^(帮助|help|指令|能干什么|功能列表)$", re.I)),
    ("city_past", re.compile(r"(哪里|哪个城市|哪).{0,6}(上次|上一次|办过).{0,4}(展|兽聚)")),
    ("city_next", re.compile(r"(哪里|哪个城市|哪).{0,6}(下次|下回|接下来).{0,4}(展|兽聚)")),
    ("city_list", re.compile(r"(有什么展|有哪些展|有啥展|有什么兽聚|哪有展|有什么活动|近期展|近期兽聚)")),
    ("recent", re.compile(r"(最近.{0,4}(展|兽聚)|近期.{0,4}(有什么|有啥)|最近的展)")),
    ("next", re.compile(r"(下次展|下一次展|下一场|下次兽聚|最近的兽聚|还有几天|倒计时|下一届)")),
    ("fortune", re.compile(r"(运势|今天运气|今日运气|抽个签|求签|吉凶)")),
    ("stats", re.compile(r"(群统计|发言统计|谁最活跃|水群榜|活跃度)")),
]
CITIES = ["北京","上海","广州","成都","嘉兴"]
def match(text):
    body = re.sub(r"^\[[^\]]*\]\s*", "", text).strip()
    called = bool(re.search(NAME_CALL, body))
    has_slash = bool(re.match(r"^\s*[/／]", body))
    clean = re.sub(r"^\s*[/／]\s*", "", body).strip()
    city = next((c for c in CITIES if c in clean), "")
    for key, pat in COMMANDS:
        if pat.search(clean):
            if key.startswith("city_") or key == "city_list":
                return key, city
            return key, city
    return "", city
cases = ["/下次展","下次展","阿灰 下次展","小灰近期展","/运势","阿灰今天运势","/群统计",
         "哪里下次展","成都哪里下次展","/哪里上次展","广州有什么展","/help","阿灰 有什么展","今天天气"]
for c in cases:
    print(f"{c:<16} -> {match(c)}")
