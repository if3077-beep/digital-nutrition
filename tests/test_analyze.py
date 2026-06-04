import pytest
from datetime import datetime, timedelta
from scripts.models import Event
from scripts.analyze import (
    apply_classification,
    aggregate_by_category,
    aggregate_by_day,
    aggregate_by_hour,
    build_report_data,
)


def make_event(category, duration, days_ago=0, hour=10, source="browser"):
    return Event(
        timestamp=datetime(2024, 6, 1, hour, 0) - timedelta(days=days_ago),
        duration_seconds=duration,
        source=source,
        category=category,
        subcategory=None,
        title="test",
        url_or_path="https://test.com" if source == "browser" else "/repo",
    )


def test_apply_classification_browser():
    """浏览器事件根据 URL 分类"""
    events = [
        make_event("other", 100, source="browser"),
    ]
    events[0].url_or_path = "https://github.com/user"
    rules = {"learning": ["github.com"]}
    classified = apply_classification(events, rules)
    assert classified[0].category == "learning"


def test_apply_classification_keeps_git():
    """Git 事件保留原类别，不重新分类"""
    events = [
        make_event("code", 100, source="git"),
    ]
    rules = {"learning": ["repo"]}
    classified = apply_classification(events, rules)
    assert classified[0].category == "code"


def test_apply_classification_empty_rules():
    """空规则下浏览器归为 other"""
    events = [make_event("other", 100, source="browser")]
    classified = apply_classification(events, {})
    assert classified[0].category == "other"


def test_aggregate_by_category_basic():
    """按类别聚合时长"""
    events = [
        make_event("learning", 100),
        make_event("learning", 200),
        make_event("social", 50),
    ]
    result = aggregate_by_category(events)
    assert result["learning"] == 300
    assert result["social"] == 50


def test_aggregate_by_category_empty():
    """空列表"""
    assert aggregate_by_category([]) == {}


def test_aggregate_by_day():
    """按天聚合"""
    events = [
        make_event("learning", 100, days_ago=0),
        make_event("learning", 200, days_ago=0),
        make_event("social", 50, days_ago=1),
    ]
    result = aggregate_by_day(events)
    assert len(result) == 2
    today_key = "2024-06-01"
    assert result[today_key]["learning"] == 300
    yesterday_key = "2024-05-31"
    assert result[yesterday_key]["social"] == 50


def test_aggregate_by_hour():
    """按时段聚合"""
    events = [
        make_event("learning", 100, hour=10),
        make_event("learning", 200, hour=10),
        make_event("social", 50, hour=14),
    ]
    result = aggregate_by_hour(events)
    assert result[10] == 300
    assert result[14] == 50


def test_build_report_data():
    """构建完整报告数据"""
    events = [
        Event(
            timestamp=datetime(2024, 6, 1, 10, 0),
            duration_seconds=1800,
            source="git",
            category="code",
            subcategory=None,
            title="feat: x",
            url_or_path="/repo",
        ),
        Event(
            timestamp=datetime(2024, 6, 1, 11, 0),
            duration_seconds=600,
            source="browser",
            category="other",
            subcategory=None,
            title="GH",
            url_or_path="https://github.com",
        ),
    ]
    rules = {"learning": ["github.com"]}
    data = build_report_data(
        events, rules,
        period_start=datetime(2024, 5, 27),
        period_end=datetime(2024, 6, 2)
    )
    assert "by_category" in data
    assert "by_day" in data
    assert "by_hour" in data
    assert "total_seconds" in data
    assert data["total_seconds"] == 2400
    # github 事件被分类为 learning
    assert data["by_category"]["learning"] == 600
    # code 保持原类别
    assert data["by_category"]["code"] == 1800


def test_build_report_data_top_sources():
    """Top sources 聚合"""
    events = [
        Event(
            timestamp=datetime(2024, 6, 1, 10, 0),
            duration_seconds=600,
            source="browser",
            category="other",
            subcategory=None,
            title="a",
            url_or_path="https://a.com",
        ),
        Event(
            timestamp=datetime(2024, 6, 1, 11, 0),
            duration_seconds=300,
            source="browser",
            category="other",
            subcategory=None,
            title="b",
            url_or_path="https://b.com",
        ),
    ]
    data = build_report_data(
        events, {},
        period_start=datetime(2024, 5, 27),
        period_end=datetime(2024, 6, 2)
    )
    assert len(data["top_sources"]) == 2
    # 第一个是时长最长的
    assert data["top_sources"][0][0] == "https://a.com"
    assert data["top_sources"][0][1] == 600
