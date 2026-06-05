"""Tests for share card metadata."""
from digital_nutrition.report.share import get_share_card_metadata


def test_get_share_card_metadata_basic_structure():
    """metadata 必须包含所有展示所需字段"""
    report = {
        "by_category": {"code": 18000, "learning": 7200, "entertainment": 3600},
        "period_start": "2026-05-30T00:00:00",
        "period_end": "2026-06-05T23:59:59",
        "total_seconds": 28800,
    }
    meta = get_share_card_metadata(report, "🧱 代码机器人", ["i1", "i2"])

    # 必需字段
    for key in [
        "title", "persona", "persona_color", "period", "total_human",
        "top_categories", "highlight_insight", "footer",
    ]:
        assert key in meta, f"missing {key}"

    assert meta["persona"] == "🧱 代码机器人"
    assert meta["period"] == "2026-05-30 至 2026-06-05"
    assert meta["highlight_insight"] == "i1"  # 取第一条


def test_top_categories_sorted_by_duration():
    """top_categories 应按时长降序"""
    report = {
        "by_category": {
            "code": 18000,         # 5h
            "learning": 7200,      # 2h
            "entertainment": 3600, # 1h
            "news": 1800,          # 30m
        },
        "period_start": "2026-05-30T00:00:00",
        "period_end": "2026-06-05T23:59:59",
        "total_seconds": 30600,
    }
    meta = get_share_card_metadata(report, "⚖️ 平衡大师", [])
    cats = meta["top_categories"]
    assert len(cats) == 3
    assert cats[0]["name"] == "写代码"  # 最高
    assert cats[0]["pct"] > cats[1]["pct"] > cats[2]["pct"]


def test_top_n_respected():
    """top_n 参数应限制返回数量"""
    report = {
        "by_category": {f"cat{i}": 100 * i for i in range(10)},
        "period_start": "2026-05-30T00:00:00",
        "period_end": "2026-06-05T23:59:59",
        "total_seconds": sum(100 * i for i in range(10)),
    }
    meta = get_share_card_metadata(report, "🌐 多元探索者", [], top_n=2)
    assert len(meta["top_categories"]) == 2


def test_highlight_insight_truncated():
    """过长 insight 应被截断到 27 字 + ..."""
    long = "x" * 100
    report = {
        "by_category": {"code": 100},
        "period_start": "2026-05-30T00:00:00",
        "period_end": "2026-06-05T23:59:59",
        "total_seconds": 100,
    }
    meta = get_share_card_metadata(report, "🧱 代码机器人", [long])
    assert len(meta["highlight_insight"]) <= 30
    assert meta["highlight_insight"].endswith("...")


def test_empty_insights():
    """无 insights 时 highlight_insight 应为空字符串"""
    report = {
        "by_category": {"code": 100},
        "period_start": "2026-05-30T00:00:00",
        "period_end": "2026-06-05T23:59:59",
        "total_seconds": 100,
    }
    meta = get_share_card_metadata(report, "🧱 代码机器人", [])
    assert meta["highlight_insight"] == ""


def test_unknown_persona_uses_fallback_color():
    """未知 persona 不应崩溃，使用灰色 fallback"""
    report = {
        "by_category": {"code": 100},
        "period_start": "2026-05-30T00:00:00",
        "period_end": "2026-06-05T23:59:59",
        "total_seconds": 100,
    }
    meta = get_share_card_metadata(report, "🤖 外星人", [])
    assert meta["persona_color"] == "#9ca3af"


def test_github_url_in_metadata():
    """PM 视角：分享卡应带 GitHub URL 引导传播（v0.5.6）"""
    report = {
        "by_category": {"code": 100},
        "period_start": "2026-05-30T00:00:00",
        "period_end": "2026-06-05T23:59:59",
        "total_seconds": 100,
    }
    meta = get_share_card_metadata(report, "🧱 代码机器人", [])
    assert "github_url" in meta
    assert meta["github_url"].startswith("https://github.com/")
