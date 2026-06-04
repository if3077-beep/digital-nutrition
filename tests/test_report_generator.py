"""Tests for HTML report generator."""
import pytest
from pathlib import Path
from scripts.report_generator import (
    render_report,
    build_chart_data,
    build_category_details,
)


def test_build_chart_data():
    """构建图表数据"""
    by_category = {"code": 5000, "learning": 2000, "other": 1000}
    data = build_chart_data(by_category)
    assert isinstance(data, list)
    assert len(data) == 3
    for item in data:
        assert "name" in item
        assert "value" in item


def test_build_chart_data_empty():
    """空数据"""
    data = build_chart_data({})
    assert data == []


def test_build_chart_data_sorted():
    """按值降序排列"""
    by_category = {"code": 1000, "learning": 5000, "other": 2000}
    data = build_chart_data(by_category)
    assert data[0]["name"] == "技术学习"  # learning 5000 排第一
    assert data[0]["value"] == 5000


def test_build_category_details():
    """构建类别详情列表"""
    by_category = {"code": 5000, "learning": 2000}
    details = build_category_details(by_category)
    assert len(details) == 2
    for d in details:
        assert "name" in d
        assert "color" in d
        assert "icon" in d
        assert "duration_human" in d
        assert "pct" in d


def test_build_category_details_percentage():
    """百分比正确计算"""
    by_category = {"code": 5000, "learning": 5000}
    details = build_category_details(by_category)
    total_pct = sum(d["pct"] for d in details)
    assert abs(total_pct - 100.0) < 0.1


def test_render_report(tmp_path):
    """渲染完整报告"""
    report_data = {
        "by_category": {"code": 5000, "learning": 2000, "other": 1000},
        "by_day": {},
        "by_hour": {10: 3000, 14: 2000},
        "total_seconds": 8000,
        "top_sources": [],
        "event_count": 10,
        "period_start": "2024-05-27T00:00:00",
        "period_end": "2024-06-02T23:59:59",
    }
    persona = "🧱 代码机器人"
    insights = ["你的代码时间集中在上午"]

    output_dir = tmp_path / "report"
    html_path = render_report(
        report_data, persona, insights, output_dir
    )
    assert html_path.exists()
    assert html_path.suffix == ".html"
    content = html_path.read_text(encoding="utf-8")
    assert "代码机器人" in content
    assert "echarts" in content.lower()
    assert "assets/echarts.min.js" in content


def test_render_report_copies_echarts(tmp_path):
    """渲染报告时复制 ECharts 到输出目录"""
    report_data = {
        "by_category": {"code": 5000},
        "by_day": {},
        "by_hour": {10: 5000},
        "total_seconds": 5000,
        "top_sources": [],
        "event_count": 5,
        "period_start": "2024-01-01T00:00:00",
        "period_end": "2024-01-07T23:59:59",
    }
    output_dir = tmp_path / "report2"
    render_report(report_data, "🧱 代码机器人", [], output_dir)
    assets_dir = output_dir / "assets"
    assert assets_dir.exists()
    assert (assets_dir / "echarts.min.js").exists()
