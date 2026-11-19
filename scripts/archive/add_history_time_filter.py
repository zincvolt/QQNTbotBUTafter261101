from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\astrbot\builtin_stars\astrbot\group_chat_context.py")
s = p.read_text(encoding="utf-8")

# 1) 初始化并行时间戳队列
old = "        self._record_ids: dict[str, deque] = defaultdict(deque)"
new = ("        self._record_ids: dict[str, deque] = defaultdict(deque)\n"
       "        self._record_times: dict[str, deque] = defaultdict(deque)")
if old in s and "_record_times" not in s:
    s = s.replace(old, new, 1)
    print("init added")

# 2) handle_message 里记时间戳
old2 = """            records.append(final_message)
            record_ids.append(record_id)
            _trim_left(records, cfg["group_message_max_cnt"], record_ids)"""
new2 = """            records.append(final_message)
            record_ids.append(record_id)
            times = self._record_times[umo]
            times.append(time.time())
            _trim_left(records, cfg["group_message_max_cnt"], record_ids)
            while len(times) > cfg["group_message_max_cnt"]:
                times.popleft()"""
if old2 in s:
    s = s.replace(old2, new2, 1)
    print("append time")

# 3) on_req_llm 里按时间窗过滤
old3 = """            records_to_inject = raw_list[:prompt_idx]
            remaining = raw_list[prompt_idx + 1 :]
            remaining_ids = id_list[prompt_idx + 1 :] if id_list else []
            records.clear()
            records.extend(remaining)
            if id_list:
                record_ids = self._record_ids[umo]
                record_ids.clear()
                record_ids.extend(remaining_ids)"""
new3 = """            times = list(self._record_times.get(umo, deque()))
            times_to_inject = times[:prompt_idx]
            records_to_inject = raw_list[:prompt_idx]
            remaining = raw_list[prompt_idx + 1 :]
            remaining_ids = id_list[prompt_idx + 1 :] if id_list else []
            remaining_times = times[prompt_idx + 1 :]
            records.clear()
            records.extend(remaining)
            if id_list:
                record_ids = self._record_ids[umo]
                record_ids.clear()
                record_ids.extend(remaining_ids)
            time_deque = self._record_times[umo]
            time_deque.clear()
            time_deque.extend(remaining_times)

            # 只注入时间窗内的消息，太老的直接丢
            window = load_history_window()
            cutoff = time.time() - window
            kept = [
                rec
                for rec, ts in zip(records_to_inject, times_to_inject, strict=False)
                if ts >= cutoff
            ]
            if len(kept) != len(records_to_inject):
                logger.info(
                    f"group history window: kept {len(kept)}/{len(records_to_inject)} "
                    f"(window {int(window/60)}min)"
                )
            records_to_inject = kept"""
if old3 in s:
    s = s.replace(old3, new3, 1)
    print("time filter added")

p.write_text(s, encoding="utf-8")
