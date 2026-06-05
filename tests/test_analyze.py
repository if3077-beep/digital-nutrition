import pytest
from datetime import datetime, timedelta
from digital_nutrition.models import Event
from digital_nutrition.analyze import (
    apply_classification,
    aggregate_by_category,
    aggregate_by_day,
    aggregate_by_day_of_week,
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


# ===== v0.5.x aggregate_by_day_of_week =====

def test_aggregate_by_day_of_week_monday_is_zero():
    """Monday = 0 (Python weekday())"""
    events = [
        make_event("code", 100, days_ago=0, hour=10),
    ]
    # 2024-06-01 是 Saturday
    # 把 days_ago 改到 5 得到 2024-05-27 = Monday
    by_dow = aggregate_by_day_of_week([make_event("code", 100, days_ago=5, hour=10)])
    assert by_dow.get(0) == 100


def test_aggregate_by_day_of_week_sunday_is_six():
    """Sunday = 6"""
    # 2024-06-01 是 Saturday，days_ago=6 → 2024-05-26 = Sunday
    by_dow = aggregate_by_day_of_week([make_event("code", 100, days_ago=6, hour=10)])
    assert by_dow.get(6) == 100


def test_build_report_data_includes_by_day_of_week():
    """build_report_data 应输出 by_day_of_week 字段"""
    events = [make_event("code", 100, days_ago=0, hour=10)]
    data = build_report_data(
        events, {},
        period_start=datetime(2024, 5, 27),
        period_end=datetime(2024, 6, 2)
    )
    assert "by_day_of_week" in data
    assert isinstance(data["by_day_of_week"], dict)


# ===== v0.6.0 ignored_domains 隐私过滤（review Phase 4 #9） =====

def test_apply_classification_filters_ignored_domain():
    """ignored_domains 里的 URL 应被丢弃，不进入统计"""
    events = [
        Event(
            timestamp=datetime(2024, 6, 1, 10, 0),
            duration_seconds=600,
            source="browser",
            category="other",
            subcategory=None,
            title="secret bank",
            url_or_path="https://bank.example.com/accounts",
        ),
        Event(
            timestamp=datetime(2024, 6, 1, 11, 0),
            duration_seconds=300,
            source="browser",
            category="other",
            subcategory=None,
            title="github",
            url_or_path="https://github.com/user",
        ),
    ]
    rules = {"learning": ["github.com"]}
    classified = apply_classification(events, rules, ignored_domains={"bank.example.com"})
    # 银行事件被过滤
    assert len(classified) == 1
    # github 事件保留并被分类为 learning
    assert classified[0].url_or_path == "https://github.com/user"
    assert classified[0].category == "learning"


def test_apply_classification_ignored_domain_with_subdomain():
    """子域名也应被过滤（最长后缀优先）"""
    events = [
        Event(
            timestamp=datetime(2024, 6, 1, 10, 0),
            duration_seconds=600,
            source="browser",
            category="other",
            subcategory=None,
            title="",
            url_or_path="https://hr.internal.mycompany.com/personal",
        ),
    ]
    classified = apply_classification(
        events, {}, ignored_domains={"mycompany.com"}
    )
    assert classified == []


def test_apply_classification_ignored_does_not_affect_git():
    """Git 事件不被 ignored_domains 影响（隐私过滤只针对浏览器）"""
    events = [
        make_event("code", 100, source="git"),
    ]
    classified = apply_classification(
        events, {}, ignored_domains={"github.com"}
    )
    assert len(classified) == 1
    assert classified[0].category == "code"


def test_apply_classification_ignored_empty_noop():
    """ignored_domains 为空时不过滤任何事件"""
    events = [
        Event(
            timestamp=datetime(2024, 6, 1, 10, 0),
            duration_seconds=600,
            source="browser",
            category="other",
            subcategory=None,
            title="",
            url_or_path="https://bank.example.com/",
        ),
    ]
    classified = apply_classification(events, {}, ignored_domains=set())
    assert len(classified) == 1


def test_apply_classification_ignored_default_none():
    """ignored_domains 默认 None 时不过滤（向后兼容）"""
    events = [
        Event(
            timestamp=datetime(2024, 6, 1, 10, 0),
            duration_seconds=600,
            source="browser",
            category="other",
            subcategory=None,
            title="",
            url_or_path="https://bank.example.com/",
        ),
    ]
    # 不传 ignored_domains
    classified = apply_classification(events, {})
    assert len(classified) == 1

