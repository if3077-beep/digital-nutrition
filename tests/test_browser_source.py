"""
BrowserSource 测试 - 1 个 happy + 1 个 since filter + 1 个 empty
"""
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from digital_nutrition.models import Event
from digital_nutrition.sources.browser import BrowserSource


def test_browser_source_collects_from_browser_history(tmp_path, monkeypatch):
    """BrowserSource 应能从 browser-history 拿到事件并转为 Event"""
    fake_entries = [
        (datetime(2026, 6, 5, 10, 0), "https://github.com/foo/bar", "GitHub - foo/bar"),
        (datetime(2026, 6, 5, 11, 0), "https://news.ycombinator.com", "Hacker News"),
    ]

    class FakeOutputs:
        histories = fake_entries

    def fake_get_history():
        return FakeOutputs()

    monkeypatch.setattr("browser_history.get_history", fake_get_history)

    source = BrowserSource()
    assert source.is_available() is True
    events = source.collect()
    assert len(events) == 2
    assert all(isinstance(e, Event) for e in events)
    assert events[0].source == "browser"
    assert events[0].url_or_path == "https://github.com/foo/bar"
    assert events[0].title == "GitHub - foo/bar"
    assert events[0].category == "other"  # 待分类


def test_browser_source_filters_by_since(monkeypatch):
    """BrowserSource 应能根据 since 过滤旧事件"""
    base = datetime(2026, 6, 5, 12, 0)
    fake_entries = [
        (base - timedelta(days=3), "https://old.com", "old"),
        (base - timedelta(hours=1), "https://recent.com", "recent"),
        (base, "https://now.com", "now"),
    ]

    class FakeOutputs:
        histories = fake_entries

    monkeypatch.setattr(
        "browser_history.get_history",
        lambda: FakeOutputs(),
    )

    source = BrowserSource()
    events = source.collect(since=base - timedelta(days=2))
    # 只有 recent 和 now 留下
    assert len(events) == 2
    assert all(e.timestamp >= base - timedelta(days=2) for e in events)


def test_browser_source_handles_empty_history(monkeypatch):
    """BrowserSource 应对空历史返回空列表"""
    class FakeOutputs:
        histories = []

    monkeypatch.setattr(
        "browser_history.get_history",
        lambda: FakeOutputs(),
    )

    source = BrowserSource()
    events = source.collect()
    assert events == []
