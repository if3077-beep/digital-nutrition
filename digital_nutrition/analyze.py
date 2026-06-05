"""
数据聚合分析 - 按类别/天/小时统计
"""
from collections import defaultdict
from dataclasses import replace
from datetime import datetime
from typing import Dict, List, Optional, Set

from digital_nutrition.classify import classify_url, is_domain_ignored
from digital_nutrition.models import Event


def apply_classification(
    events: List[Event],
    rules: Dict[str, list],
    ignored_domains: Optional[Set[str]] = None,
) -> List[Event]:
    """对浏览器事件应用域名分类 + 隐私过滤（Git 事件保留原类别）

    v0.6.0:
      - 用 dataclasses.replace 简化（资深码农视角：避免手动重建对象）
      - 过滤 ignored_domains 中的 URL（review Phase 4 #9 隐私场景）
    """
    classified = []
    for event in events:
        if event.source == "browser":
            if is_domain_ignored(event.url_or_path, ignored_domains or set()):
                # 隐私场景：直接丢弃，不进入统计
                continue
            new_category = classify_url(event.url_or_path, rules)
            classified.append(replace(event, category=new_category))
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


def aggregate_by_day_of_week(events: List[Event]) -> Dict[int, int]:
    """
    按星期几聚合（0=Monday, 6=Sunday）。
    用于"周末模式"洞察。
    """
    result = defaultdict(int)
    for event in events:
        result[event.timestamp.weekday()] += event.duration_seconds
    return dict(result)


def build_report_data(
    events: List[Event],
    rules: Dict[str, list],
    period_start: datetime,
    period_end: datetime,
    ignored_domains: Optional[Set[str]] = None,
) -> Dict:
    """构建完整报告数据

    v0.6.0: 接受 ignored_domains 参数并过滤（review Phase 4 #9）。
    之前 cli.py 误传 all_events（未过滤）→ 报告数据与 classified 不一致。
    现在 build_report_data 内部应用 ignored_domains 过滤，与 apply_classification 行为一致。
    """
    classified = apply_classification(events, rules, ignored_domains)

    by_category = aggregate_by_category(classified)
    by_day = aggregate_by_day(classified)
    by_hour = aggregate_by_hour(classified)
    by_day_of_week = aggregate_by_day_of_week(classified)
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
        "by_day_of_week": by_day_of_week,
        "total_seconds": total,
        "top_sources": top_sources,
        "event_count": len(classified),
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
    }
