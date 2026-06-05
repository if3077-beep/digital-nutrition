"""
趋势分析 - 每日聚合 + 周期间对比
"""
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent))

from models import Event


def build_daily_aggregates(events: List[Event]) -> Dict[str, Dict[str, int]]:
    """
    按天聚合每个类别的总时长。
    返回 {date_str: {category: seconds}}，按日期升序。
    """
    result: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for e in events:
        day_key = e.timestamp.strftime("%Y-%m-%d")
        result[day_key][e.category] += e.duration_seconds
    return {k: dict(v) for k, v in sorted(result.items())}


def compute_category_deltas(
    current: Dict[str, int],
    previous: Dict[str, int],
) -> Dict[str, Dict]:
    """
    计算每个类别的变化量和变化百分比。
    返回 {category: {current, previous, delta, delta_pct}}
    """
    all_keys = set(current.keys()) | set(previous.keys())
    result = {}
    for cat in all_keys:
        cur = current.get(cat, 0)
        prev = previous.get(cat, 0)
        delta = cur - prev
        delta_pct = round(delta / prev * 100, 1) if prev > 0 else None
        result[cat] = {
            "current": cur,
            "previous": prev,
            "delta": delta,
            "delta_pct": delta_pct,
        }
    return result
