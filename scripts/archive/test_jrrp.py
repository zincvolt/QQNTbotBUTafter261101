import hashlib, sys, types
from pathlib import Path
# 直接复制算法验证分布，避免依赖 astrbot
def fortune_of(uid, day):
    d = hashlib.sha256(f"{uid}|{day}".encode()).hexdigest()
    v = int(d[:8], 16) % 101
    return v
day = "20261118"
vals = [fortune_of(str(1000000000+i), day) for i in range(2000)]
print("样本 2000，最小值", min(vals), "最大值", max(vals), "平均", round(sum(vals)/len(vals),1))
same = {fortune_of("1154487120", day) for _ in range(20)}
print("同一账号同一天 20 次结果集合:", same)
print("不同日期:", fortune_of("1154487120","20261118"), fortune_of("1154487120","20261119"))
buckets = {"大吉":0,"中吉":0,"小吉":0,"平":0,"小凶":0,"凶":0}
for v in vals:
    if v>=90: buckets["大吉"]+=1
    elif v>=75: buckets["中吉"]+=1
    elif v>=60: buckets["小吉"]+=1
    elif v>=40: buckets["平"]+=1
    elif v>=25: buckets["小凶"]+=1
    else: buckets["凶"]+=1
print({k: f"{v/20:.1f}%" for k,v in buckets.items()})
