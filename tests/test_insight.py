"""Tests for insight generator."""
import pytest
from datetime import datetime
from scripts.models import Event
from scripts.insight import (
    generate_extreme_insight,
    generate_peak_hour_insight,
    generate_balance_insight,
    generate_insights,
    format_duration,
)


def test_format_duration_hours():
    """格式化小时"""
    assert format_duration(3600) == "1h"
    assert format_duration(7200) == "2h"
    assert format_duration(5400) == "1h 30m"


def test_format_duration_minutes():
    """格式化分钟"""
    assert format_duration(60) == "1m"
    assert format_duration(1800) == "30m"


def test_format_duration_zero():
    """零时长"""
    assert format_duration(0) == "0m"


def test_format_duration_seconds():
    """小于 1 分钟"""
    assert format_duration(30) == "30s"


def test_extreme_insight_top_category():
    """极端型：Top 1 类别"""
    by_category = {"code": 5000, "learning": 1000, "social": 500}
    insight = generate_extreme_insight(by_category)
    assert insight is not None
    assert "写代码" in insight
    assert "1h" in insight


def test_extreme_insight_empty():
    """空数据返回 None"""
    assert generate_extreme_insight({}) is None


def test_peak_hour_insight_clear_peak():
    """模式型：明显高峰"""
    by_hour = {10: 100, 11: 200, 12: 50, 13: 50, 14: 50, 15: 50, 16: 50, 17: 50}
    insight = generate_peak_hour_insight(by_hour)
    assert insight is not None
    assert "10" in insight or "11" in insight


def test_peak_hour_insight_no_peak():
    """模式型：无明显高峰"""
    by_hour = {h: 100 for h in range(24)}
    insight = generate_peak_hour_insight(by_hour)
    # 没有明显高峰则返回 None
    assert insight is None


def test_peak_hour_insight_empty():
    """空数据返回 None"""
    assert generate_peak_hour_insight({}) is None


def test_balance_insight_good():
    """平衡型：分配合理"""
    by_category = {
        "code": 3000,
        "learning": 2000,
        "work": 2000,
        "other": 1000,
    }
    insight = generate_balance_insight(by_category)
    assert insight is not None
    assert "均衡" in insight or "平衡" in insight


def test_balance_insight_skewed():
    """不平衡不输出"""
    by_category = {"code": 9000, "learning": 500}
    insight = generate_balance_insight(by_category)
    assert insight is None


def test_balance_insight_too_few_categories():
    """类别太少不输出"""
    by_category = {"code": 3000, "learning": 1000}
    insight = generate_balance_insight(by_category)
    assert insight is None


def test_generate_insights_returns_list():
    """生成洞察列表"""
    by_category = {"code": 5000, "learning": 1000, "social": 500}
    by_hour = {10: 500, 11: 200, 12: 50}
    insights = generate_insights(by_category, by_hour)
    assert isinstance(insights, list)
    assert len(insights) >= 1
    assert len(insights) <= 5


def test_generate_insights_max_five():
    """最多 5 条"""
    by_category = {f"cat{i}": 100 * (i + 1) for i in range(10)}
    by_hour = {h: 100 for h in range(24)}
    insights = generate_insights(by_category, by_hour)
    assert len(insights) <= 5


def test_generate_insights_empty_data():
    """空数据返回空列表"""
    insights = generate_insights({}, {})
    assert insights == []


# ===== v0.2 趋势洞察 =====

def test_trend_insight_increase():
    """上升趋势"""
    from scripts.insight import generate_trend_insight
    deltas = {"code": {"current": 5000, "previous": 4000, "delta": 1000, "delta_pct": 25.0}}
    insight = generate_trend_insight(deltas)
    assert insight is not None
    assert "写代码" in insight
    assert "25" in insight


def test_trend_insight_no_previous():
    """无基线时返回 None"""
    from scripts.insight import generate_trend_insight
    deltas = {"new": {"current": 1000, "previous": 0, "delta": 1000, "delta_pct": None}}
    assert generate_trend_insight(deltas) is None


def test_trend_insight_small_change_ignored():
    """变化 < 10% 不输出"""
    from scripts.insight import generate_trend_insight
    deltas = {"code": {"current": 5000, "previous": 4900, "delta": 100, "delta_pct": 2.0}}
    assert generate_trend_insight(deltas) is None


def test_generate_insights_includes_trend_when_provided():
    """generate_insights 接受 deltas 并插入趋势"""
    from scripts.insight import generate_insights
    by_cat = {"code": 5000, "learning": 1000}
    by_hour = {}
    deltas = {"code": {"current": 5000, "previous": 3000, "delta": 2000, "delta_pct": 66.7}}
    insights = generate_insights(by_cat, by_hour, deltas=deltas)
    # 应该有极端型 + 趋势型
    assert len(insights) >= 2
    assert any("相比上周" in i for i in insights)
