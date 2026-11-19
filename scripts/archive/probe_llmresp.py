import sys
sys.path.insert(0, r"D:\QQNTBOT\apps\AstrBot")
from astrbot.core.provider.entities import LLMResponse
import dataclasses
try:
    print([f.name for f in dataclasses.fields(LLMResponse)])
except Exception as e:
    print("fields err", e)
    print([a for a in dir(LLMResponse) if not a.startswith("_")])
