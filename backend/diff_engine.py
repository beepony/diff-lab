"""核心对比算法：3 种模式 + 标准化函数。

输出统一格式：{
    "rows": [{"a": str|None, "b": str|None, "status": "match"|"diff_a"|"diff_b"|"intersect"}],
    "summary": {"match": int, "diff_a": int, "diff_b": int, "intersect": int, "total": int}
}
"""
import time
from collections import defaultdict, deque


def normalize(value: str, options: dict) -> str | None:
    """根据选项标准化单个值。返回 None 表示应跳过。"""
    if value is None:
        return None
    s = str(value)
    if options.get("trim"):
        s = s.strip()
    if options.get("ignore_case"):
        s = s.lower()
    if options.get("skip_empty", True) and s == "":
        return None
    return s


def parse_column(text: str) -> list[str]:
    """把多行文本拆成列表（保留原始值，不在这里标准化）。"""
    return [line for line in text.splitlines()]


def diff(text_a: str, text_b: str, mode: str, options: dict) -> dict:
    """
    主入口：执行对比并返回结构化结果。

    mode:
      - find_diff: 找差异（A 有 B 没有 + B 有 A 没有 + 共同）
      - vlookup: 以 A 列为 key，查 B 列
      - intersect: 只显示交集
    """
    start = time.perf_counter()

    list_a = parse_column(text_a)
    list_b = parse_column(text_b)

    norm_a = [normalize(v, options) for v in list_a]
    norm_b = [normalize(v, options) for v in list_b]

    # 过滤空值（标准化后为 None 的）
    filtered_a = [(idx, raw, norm) for idx, (raw, norm) in enumerate(zip(list_a, norm_a)) if norm is not None]
    filtered_b = [(idx, raw, norm) for idx, (raw, norm) in enumerate(zip(list_b, norm_b)) if norm is not None]

    set_a_norm = {n for _, _, n in filtered_a}
    set_b_norm = {n for _, _, n in filtered_b}

    if mode == "find_diff":
        rows, summary = _find_diff(filtered_a, filtered_b)
    elif mode == "vlookup":
        rows, summary = _vlookup(filtered_a, filtered_b, set_b_norm)
    elif mode == "intersect":
        rows, summary = _intersect(filtered_a, filtered_b, set_a_norm, set_b_norm)
    else:
        raise ValueError(f"Unknown mode: {mode}")

    summary["duration_ms"] = round((time.perf_counter() - start) * 1000, 2)
    return {"rows": rows, "summary": summary}


def _find_diff(filtered_a, filtered_b):
    """找差异：按出现次数匹配，保留两列各自的输入顺序。"""
    rows = []
    summary = {"match": 0, "diff_a": 0, "diff_b": 0, "intersect": 0, "total": 0}

    remaining_b = defaultdict(deque)
    for _, raw, norm in filtered_b:
        remaining_b[norm].append(raw)

    for _, raw, norm in filtered_a:
        if remaining_b[norm]:
            rows.append({"a": raw, "b": remaining_b[norm].popleft(), "status": "match"})
            summary["match"] += 1
        else:
            rows.append({"a": raw, "b": None, "status": "diff_a"})
            summary["diff_a"] += 1

    # B 列中未被消耗的值保持 B 的输入顺序。
    for _, raw, norm in filtered_b:
        if remaining_b[norm] and remaining_b[norm][0] == raw:
            remaining_b[norm].popleft()
            rows.append({"a": None, "b": raw, "status": "diff_b"})
            summary["diff_b"] += 1

    summary["total"] = len(rows)
    return rows, summary


def _vlookup(filtered_a, filtered_b, set_b_norm):
    """VLOOKUP：以 A 为 key，查 B。"""
    rows = []
    summary = {"match": 0, "diff_a": 0, "diff_b": 0, "intersect": 0, "total": 0}

    for orig_idx, raw, norm in filtered_a:
        is_match = norm in set_b_norm
        b_match = _find_first_match(norm, filtered_b) if is_match else None
        status = "match" if is_match else "diff_a"
        rows.append({"a": raw, "b": b_match, "status": status})
        summary[status] += 1

    summary["total"] = len(rows)
    return rows, summary


def _intersect(filtered_a, filtered_b, set_a_norm, set_b_norm):
    """找交集：去重后按 A 列首次出现顺序输出。"""
    rows = []
    summary = {"match": 0, "diff_a": 0, "diff_b": 0, "intersect": 0, "total": 0}
    first_a = {}
    first_b = {}
    for _, raw, norm in filtered_a:
        first_a.setdefault(norm, raw)
    for _, raw, norm in filtered_b:
        first_b.setdefault(norm, raw)

    for norm, a_raw in first_a.items():
        if norm in first_b:
            rows.append({"a": a_raw, "b": first_b[norm], "status": "intersect"})
            summary["intersect"] += 1

    summary["total"] = len(rows)
    return rows, summary


def _find_first_match(norm: str, filtered_b: list) -> str | None:
    """在 B 列里找第一个匹配标准化值的原始值。"""
    for _, raw, n in filtered_b:
        if n == norm:
            return raw
    return None
