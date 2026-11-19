from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py")
s = p.read_text(encoding="utf-8")

mapping = '''PROVINCE_CITIES = {
    "江苏": ["南京", "苏州", "无锡", "常州", "扬州", "徐州", "南通", "镇江", "泰州", "盐城"],
    "浙江": ["杭州", "宁波", "温州", "嘉兴", "绍兴", "金华", "湖州", "台州", "舟山"],
    "广东": ["广州", "深圳", "佛山", "东莞", "珠海", "中山", "惠州", "汕头", "江门"],
    "四川": ["成都", "绵阳", "乐山", "德阳", "宜宾"],
    "山东": ["济南", "青岛", "烟台", "潍坊", "临沂", "淄博"],
    "湖北": ["武汉", "宜昌", "襄阳"],
    "湖南": ["长沙", "株洲", "衡阳"],
    "河南": ["郑州", "洛阳", "开封"],
    "河北": ["石家庄", "唐山", "保定"],
    "福建": ["厦门", "福州", "泉州"],
    "安徽": ["合肥", "芜湖", "蚌埠"],
    "江西": ["南昌", "赣州", "九江"],
    "山西": ["太原", "大同"],
    "陕西": ["西安", "咸阳"],
    "辽宁": ["沈阳", "大连", "鞍山"],
    "吉林": ["长春", "吉林"],
    "黑龙江": ["哈尔滨", "大庆", "齐齐哈尔"],
    "云南": ["昆明", "大理", "丽江"],
    "贵州": ["贵阳", "遵义"],
    "广西": ["南宁", "桂林", "柳州"],
    "甘肃": ["兰州"],
    "内蒙古": ["呼和浩特", "包头"],
    "海南": ["海口", "三亚"],
    "新疆": ["乌鲁木齐"],
    "宁夏": ["银川"],
    "青海": ["西宁"],
    "西藏": ["拉萨"],
    "重庆": ["重庆"],
    "天津": ["天津"],
    "北京": ["北京"],
    "上海": ["上海"],
    "香港": ["香港"],
    "澳门": ["澳门"],
    "台湾": ["台北", "高雄"],
}


def expand_place(token: str) -> list[str]:
    """Expand a city or province into the list of city names to match."""
    if not token:
        return []
    if token in PROVINCE_CITIES:
        return [token] + PROVINCE_CITIES[token]
    return [token]


'''
if "PROVINCE_CITIES" not in s:
    s = s.replace("PROVINCES = [", mapping + "PROVINCES = [", 1)
    print("province map added")

# render_city 用 expand_place 过滤
old = '''    now = time.time()
    hits = [e for e in events if city in (str(e.get("city", "")) + str(e.get("region", "")))]'''
new = '''    now = time.time()
    tokens = expand_place(city)
    hits = [
        e
        for e in events
        if any(t in (str(e.get("city", "")) + str(e.get("region", ""))) for t in tokens)
    ]'''
if old in s:
    s = s.replace(old, new, 1)
    print("render_city expanded")

p.write_text(s, encoding="utf-8")
