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


def generate_weekend_insight(by_day_of_week: Dict[int, int]) -> Optional[str]:
    """
    周末模式洞察：比较周末 (Sat=5, Sun=6) vs 工作日 (Mon-Fri=0-4) 平均时长。

    - 周末均值明显 > 工作日（> 1.5x）→ "周末型"（你周末更活跃）
    - 周末均值明显 < 工作日（< 0.5x）→ "工作日型"（你周末摸鱼）
    - 差距不明显 → 不输出（噪声）
    """
    if not by_day_of_week:
        return None

    weekday_total = sum(by_day_of_week.get(d, 0) for d in range(0, 5))  # Mon-Fri
    weekend_total = sum(by_day_of_week.get(d, 0) for d in [5, 6])       # Sat-Sun

    # 计算日均（避免某天数据缺失造成偏差）
    weekday_days = sum(1 for d in range(0, 5) if by_day_of_week.get(d, 0) > 0)
    weekend_days = sum(1 for d in [5, 6] if by_day_of_week.get(d, 0) > 0)

    # 至少需要 3 个工作日 + 1 个周末日才有统计意义
    if weekday_days < 3 or weekend_days < 1:
        return None

    weekday_avg = weekday_total / weekday_days
    weekend_avg = weekend_total / weekend_days

    if weekday_avg == 0:
        return None

    ratio = weekend_avg / weekday_avg

    if ratio > 1.5:
        return f"你周末更活跃（周末日均是工作日的 {ratio:.1f} 倍）"
    if ratio < 0.5:
        return f"你周末明显放松（周末日均只有工作日的 {ratio:.0%}）"

    return None


def generate_insights(
    by_category: Dict[str, int],
    by_hour: Dict[int, int],
    deltas: Optional[Dict[str, Dict]] = None,
    by_day_of_week: Optional[Dict[int, int]] = None,
) -> List[str]:
    """
    生成洞察列表（最多 5 条）。
    按优先级：极端型 > 趋势型 > 模式型 > 平衡型 > 周末型
    """
    insights = []

    # 1. 极端型（必出）
    extreme = generate_extreme_insight(by_category)
    if extreme:
        insights.append(extreme)

    # 2. 趋势型（v0.2：如果有 deltas）
    if deltas:
        trend = generate_trend_insight(deltas)
        if trend:
            insights.append(trend)

    # 3. 模式型
    peak = generate_peak_hour_insight(by_hour)
    if peak:
        insights.append(peak)

    # 4. 平衡型
    balance = generate_balance_insight(by_category)
    if balance:
        insights.append(balance)

    # 5. 周末型（v0.5.x）
    if by_day_of_week:
        weekend = generate_weekend_insight(by_day_of_week)
        if weekend:
            insights.append(weekend)

    return insights[:5]


def generate_trend_insight(deltas: Dict[str, Dict]) -> Optional[str]:
    """
    趋势型洞察：对比上一周期，挑选绝对变化最大的类别。
    变化 < 10% 不输出（噪声）。
    """
    candidates = [
        (cat, d) for cat, d in deltas.items()
        if d.get("delta_pct") is not None and abs(d["delta_pct"]) >= 10
    ]
    if not candidates:
        return None

    cat, d = max(candidates, key=lambda x: abs(x[1]["delta_pct"]))
    cat_name = CATEGORY_NAMES.get(cat, cat)
    pct = d["delta_pct"]
    arrow = "↑" if pct > 0 else "↓"
    sign = "+" if pct > 0 else ""
    return f"相比上周，{cat_name}{arrow}{sign}{pct}%"
