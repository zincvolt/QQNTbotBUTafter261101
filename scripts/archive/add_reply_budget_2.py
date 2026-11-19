from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\astrbot\builtin_stars\astrbot\group_chat_context.py")
s = p.read_text(encoding="utf-8")

# 召唤词直通：记录一次回复再返回 True
old = '''        for word in judge_cfg.get("summon", []):
            if word and word in text:
                logger.info(f"group judge | 召唤词({word})直通 | {text[:30]}")
                return True'''
new = '''        for word in judge_cfg.get("summon", []):
            if word and word in text:
                self._note_reply(event.unified_msg_origin)
                logger.info(f"group judge | 召唤词({word})直通 | {text[:30]}")
                return True'''
if old in s:
    s = s.replace(old, new, 1)
    print("summon counted")

# 概率闸：先看预算，超了就跳过
old2 = '''            case "judge":
                if not await self._judge_reply(event, cfg):
                    return False
                # 判官说接，再按概率收一次频率
                chance = load_reply_chance()
                if chance >= 1.0:
                    return True
                if random.random() < chance:
                    return True
                logger.info(f"group judge | 概率闸拦截 (chance={chance:.2f}) | {event.message_str[:30]}")
                return False'''
new2 = '''            case "judge":
                if not await self._judge_reply(event, cfg):
                    return False
                over, used = self._over_budget(event.unified_msg_origin)
                if over:
                    logger.info(f"group judge | 超出预算({used} 条)跳过 | {event.message_str[:30]}")
                    return False
                # 判官说接，再按概率收一次频率
                chance = load_reply_chance()
                if chance >= 1.0 or random.random() < chance:
                    self._note_reply(event.unified_msg_origin)
                    return True
                logger.info(f"group judge | 概率闸拦截 (chance={chance:.2f}) | {event.message_str[:30]}")
                return False'''
if old2 in s:
    s = s.replace(old2, new2, 1)
    print("budget gate added")

p.write_text(s, encoding="utf-8")
