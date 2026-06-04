"""
洞察生成器 - 基于数据生成自然语言洞察
"""
from typing import Dict, List, Optional


def format_duration(seconds: int) -> str:
    """格式化时长为人类可读字符串"""
    if seconds == 0:
        return "0m"
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m"
    hours = minutes // 60
    mins = minutes % 60
    if mins == 0:
        return f"{hours}h"
    return f"{hours}h {mins}m"


CATEGORY_NAMES = {
    "code": "写代码",
    "learning": "技术学习",
    "work": "工作/邮件",
    "social": "社交",
    "entertainment": "娱乐",
    "shopping": "购物",
    "news": "资讯",
    "other": "其他",
}


def generate_extreme_insight(by_category: Dict[str, int]) -> Optional[str]:
    """极端型洞察：Top 1 类别"""
    if not by_category:
        return None
    top_cat = max(by_category, key=by_category.get)
    duration = by_category[top_cat]
    cat_name = CATEGORY_NAMES.get(top_cat, top_cat)
    return f"你本周投入最多的是「{cat_name}」，共 {format_duration(duration)}"


def generate_peak_hour_insight(by_hour: Dict[int, int]) -> Optional[str]:
    """模式型洞察：时段高峰"""
    if not by_hour:
        return None

    total = sum(by_hour.values())
    if total == 0:
        return None

    # 找高峰时段
    peak_hour = max(by_hour, key=by_hour.get)
    peak_value = by_hour[peak_hour]

    # 计算平均（基于所有 24 小时）
    avg = total / 24

    # 高峰是否明显（> 平均的 2 倍）
    if peak_value > avg * 2 and peak_value > 0:
        return f"你在 {peak_hour}:00 左右最活跃，时间占比是平均水平的 {peak_value/avg:.1f} 倍"

    return None


def generate_balance_insight(by_category: Dict[str, int]) -> Optional[str]:
    """平衡型洞察：评估时间分配"""
    total = sum(by_category.values())
    if total == 0:
        return None

    # 计算非零类别数量
    non_zero = {k: v for k, v in by_category.items() if v > 0}
    if len(non_zero) < 3:
        return None

    # 评估最大类别占比
    max_pct = max(non_zero.values()) / total
    if max_pct < 0.4:
        return "你的时间分配较为均衡，跨多个领域"

    return None


def generate_insights(by_category: Dict[str, int], by_hour: Dict[int, int]) -> List[str]:
    """
    生成洞察列表（最多 5 条）。
    按优先级：极端型 > 模式型 > 平衡型
    """
    insights = []

    # 1. 极端型（必出）
    extreme = generate_extreme_insight(by_category)
    if extreme:
        insights.append(extreme)

    # 2. 模式型
    peak = generate_peak_hour_insight(by_hour)
    if peak:
        insights.append(peak)

    # 3. 平衡型
    balance = generate_balance_insight(by_category)
    if balance:
        insights.append(balance)

    return insights[:5]
