"""
数据聚合分析 - 按类别/天/小时统计
"""
from collections import defaultdict
from datetime import datetime
from typing import Dict, List

from digital_nutrition.classify import classify_url
from digital_nutrition.models import Event


def apply_classification(events: List[Event], rules: Dict[str, list]) -> List[Event]:
    """对浏览器事件应用域名分类（Git 事件保留原类别）"""
    classified = []
    for event in events:
        if event.source == "browser":
            new_category = classify_url(event.url_or_path, rules)
            classified.append(Event(
                timestamp=event.timestamp,
                duration_seconds=event.duration_seconds,
                source=event.source,
                category=new_category,
                subcategory=event.subcategory,
                title=event.title,
                url_or_path=event.url_or_path,
            ))
        else:
            # Git 事件保留原类别
            classified.append(event)
    return classified


def aggregate_by_category(events: List[Event]) -> Dict[str, int]:
    """按类别聚合总时长（秒）"""
    result = defaultdict(int)
    for event in events:
        result[event.category] += event.duration_seconds
    return dict(result)


def aggregate_by_day(events: List[Event]) -> Dict[str, Dict[str, int]]:
    """按天+类别聚合"""
    result = defaultdict(lambda: defaultdict(int))
    for event in events:
        day_key = event.timestamp.strftime("%Y-%m-%d")
        result[day_key][event.category] += event.duration_seconds
    return {k: dict(v) for k, v in result.items()}


def aggregate_by_hour(events: List[Event]) -> Dict[int, int]:
    """按时段聚合"""
    result = defaultdict(int)
    for event in events:
        result[event.timestamp.hour] += event.duration_seconds
    return dict(result)


def build_report_data(
    events: List[Event],
    rules: Dict[str, list],
    period_start: datetime,
    period_end: datetime,
) -> Dict:
    """构建完整报告数据"""
    classified = apply_classification(events, rules)

    by_category = aggregate_by_category(classified)
    by_day = aggregate_by_day(classified)
    by_hour = aggregate_by_hour(classified)
    total = sum(e.duration_seconds for e in classified)

    # 按 URL/路径聚合（Top 10）
    by_source = defaultdict(int)
    for e in classified:
        by_source[e.url_or_path] += e.duration_seconds
    top_sources = sorted(by_source.items(), key=lambda x: -x[1])[:10]

    return {
        "by_category": by_category,
        "by_day": by_day,
        "by_hour": by_hour,
        "total_seconds": total,
        "top_sources": top_sources,
        "event_count": len(classified),
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
    }
