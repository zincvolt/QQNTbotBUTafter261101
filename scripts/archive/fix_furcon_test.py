from pathlib import Path
p = Path(r"D:\QQNTBOT\scripts\archive\test_furcon_card.py")
s = p.read_text(encoding="utf-8")
s = s.replace(
    'event_mod.filter = type("F", (), {"EventMessageType": type("E", (), {"GROUP_MESSAGE": 1})})()',
    '_F = _Filter()\n_F.EventMessageType = type("E", (), {"GROUP_MESSAGE": 1})()\nevent_mod.filter = _F',
)
p.write_text(s, encoding="utf-8")
print("stub fixed")
