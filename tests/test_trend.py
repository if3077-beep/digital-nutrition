"""Tests for trend analysis."""
from datetime import datetime
from digital_nutrition.models import Event
from digital_nutrition.trend import build_daily_aggregates, compute_category_deltas


def test_build_daily_aggregates_groups_by_day():
    """按天+类别聚合"""
    events = [
        Event(datetime(2024, 6, 1, 10, 0), 1800, "browser", "code", None, "", ""),
        Event(datetime(2024, 6, 1, 14, 0), 3600, "browser", "learning", None, "", ""),
        Event(datetime(2024, 6, 2, 10, 0), 1800, "browser", "code", None, "", ""),
    ]
    daily = build_daily_aggregates(events)
    assert daily["2024-06-01"]["code"] == 1800
    assert daily["2024-06-01"]["learning"] == 3600
    assert daily["2024-06-02"]["code"] == 1800


def test_build_daily_aggregates_empty():
    """空事件返回空字典"""
    assert build_daily_aggregates([]) == {}


def test_compute_category_deltas_basic():
    """对比计算百分比变化"""
    current = {"code": 5000, "learning": 3000}
    previous = {"code": 4000, "learning": 3500}
    deltas = compute_category_deltas(current, previous)
    assert deltas["code"]["delta_pct"] == 25.0
    assert deltas["learning"]["delta_pct"] < 0
    assert deltas["code"]["delta"] == 1000


def test_compute_category_deltas_zero_previous():
    """之前为 0 时 delta_pct 为 None"""
    deltas = compute_category_deltas({"new": 1000}, {})
    assert deltas["new"]["delta_pct"] is None
    assert deltas["new"]["delta"] == 1000
