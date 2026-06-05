"""
BrowserSource 测试 - 1 个 happy + 1 个 since filter + 1 个 empty
+ v0.5.8 时长估算测试
"""
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from digital_nutrition.models import Event
from digital_nutrition.sources.browser import (
    BrowserSource,
    _resolve_browsers,
    estimate_durations,
    _domain_of,
)


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
    # v0.5.8：duration 不再是 0
    assert all(e.duration_seconds > 0 for e in events)


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


# ===== v0.5.8: 时长估算 =====

def test_domain_of_strips_www_and_lowercases():
    assert _domain_of("https://www.GitHub.com/foo") == "github.com"
    assert _domain_of("https://api.github.com") == "api.github.com"
    assert _domain_of("https://github.com") == "github.com"
    assert _domain_of("not a url") == ""


def test_estimate_durations_empty():
    assert estimate_durations([]) == []


def test_estimate_durations_same_domain_gap_becomes_duration():
    """同域名相邻 visit 的时间差应作为在前一个页面的停留时长"""
    base = datetime(2026, 6, 5, 10, 0)
    visits = [
        (base, "https://github.com/a", "A"),
        (base + timedelta(minutes=5), "https://github.com/b", "B"),  # 5min gap
        (base + timedelta(minutes=20), "https://github.com/c", "C"),  # 15min gap
    ]
    enriched = estimate_durations(visits)
    assert len(enriched) == 3
    # 第一个：5min gap
    assert enriched[0][3] == 5 * 60
    # 第二个：15min gap
    assert enriched[1][3] == 15 * 60
    # 第三个：默认值 30s（最后一笔）
    assert enriched[2][3] == 30


def test_estimate_durations_caps_at_max():
    """时间差超过 30 分钟应被截断到 30 分钟"""
    base = datetime(2026, 6, 5, 10, 0)
    visits = [
        (base, "https://github.com/a", "A"),
        (base + timedelta(hours=5), "https://github.com/b", "B"),  # 5h gap → 截断到 30min
    ]
    enriched = estimate_durations(visits)
    assert enriched[0][3] == 30 * 60  # MAX = 30 min


def test_estimate_durations_floor_at_min():
    """时间差 < 5s 应被提升到 5s（避免 0 噪音）"""
    base = datetime(2026, 6, 5, 10, 0)
    visits = [
        (base, "https://github.com/a", "A"),
        (base + timedelta(seconds=1), "https://github.com/b", "B"),  # 1s gap
    ]
    enriched = estimate_durations(visits)
    assert enriched[0][3] == 5  # MIN = 5s


def test_estimate_durations_different_domains_independent():
    """不同域名的 visit 各自独立计算 duration"""
    base = datetime(2026, 6, 5, 10, 0)
    visits = [
        (base, "https://github.com/a", "A"),
        (base + timedelta(minutes=2), "https://news.ycombinator.com", "B"),  # 2min gap 但不同域
    ]
    enriched = estimate_durations(visits)
    # github 末尾 → 30s
    assert enriched[0][3] == 30
    # hackernews 末尾 → 30s
    assert enriched[1][3] == 30


# ===== v0.7.0 --browser 参数（任务 3） =====

def test_resolve_browsers_chromium_aliases():
    """chrome/edge/brave/arc 各自保留为独立类名（库具体类）"""
    assert _resolve_browsers(["chrome"]) == ["chrome"]
    assert _resolve_browsers(["edge"]) == ["edge"]
    assert _resolve_browsers(["brave"]) == ["brave"]
    assert _resolve_browsers(["arc"]) == ["arc"]
    assert _resolve_browsers(["chromium"]) == ["chromium"]


def test_resolve_browsers_firefox_aliases():
    """ff/firefox 都解析为 firefox"""
    assert _resolve_browsers(["ff"]) == ["firefox"]
    assert _resolve_browsers(["firefox"]) == ["firefox"]


def test_resolve_browsers_safari():
    assert _resolve_browsers(["safari"]) == ["safari"]


def test_resolve_browsers_dedup():
    """传多个同一族别名应去重（chrome/edge/brave 各自独立 → 都保留）"""
    assert _resolve_browsers(["chrome", "edge", "brave"]) == ["brave", "chrome", "edge"]


def test_resolve_browsers_multiple_canonical():
    """传多个不同族浏览器应保留多个（按字典序）"""
    assert _resolve_browsers(["chrome", "firefox"]) == ["chrome", "firefox"]


def test_resolve_browsers_unsupported_raises():
    """不支持的浏览器名应抛 ValueError"""
    with pytest.raises(ValueError, match="netscape"):
        _resolve_browsers(["netscape"])


def test_resolve_browsers_empty_returns_empty_list():
    """None 或 [] 返回 []（调用方负责用 get_history() 全扫）"""
    assert _resolve_browsers(None) == []
    assert _resolve_browsers([]) == []


def test_browser_source_collect_with_browsers_arg(monkeypatch):
    """传 browsers 应走具体 Browser 类（不走 get_history）"""
    from digital_nutrition.sources import browser as browser_mod
    from browser_history.browsers import ChromiumBasedBrowser, Firefox

    class FakeOutputs:
        def __init__(self, histories):
            self.histories = histories

    base = datetime(2026, 6, 5, 10, 0)
    fake_chromium_histories = [
        (base, "https://github.com/a", "A"),
    ]
    fake_firefox_histories = [
        (base + timedelta(hours=1), "https://news.ycombinator.com", "HN"),
    ]

    def fake_chromium_fetch(self):
        return FakeOutputs(fake_chromium_histories)

    def fake_firefox_fetch(self):
        return FakeOutputs(fake_firefox_histories)

    # 确保 get_history 没被调用
    def fail_get_history():
        raise AssertionError("get_history 不应被调用（已指定 browsers）")

    monkeypatch.setattr(ChromiumBasedBrowser, "fetch_history", fake_chromium_fetch)
    monkeypatch.setattr(Firefox, "fetch_history", fake_firefox_fetch)
    monkeypatch.setattr("browser_history.get_history", fail_get_history)

    source = BrowserSource()
    events = source.collect(browsers=["chromium", "firefox"])

    # 应合并两个浏览器的事件
    assert len(events) == 2
    urls = {e.url_or_path for e in events}
    assert "https://github.com/a" in urls
    assert "https://news.ycombinator.com" in urls


def test_browser_source_collect_with_browsers_none_uses_get_history(monkeypatch):
    """browsers=None（默认）应走 get_history() 库自动全扫"""
    fake_entries = [
        (datetime(2026, 6, 5, 10, 0), "https://github.com/a", "A"),
    ]

    class FakeOutputs:
        histories = fake_entries

    monkeypatch.setattr(
        "browser_history.get_history",
        lambda: FakeOutputs(),
    )

    # 走具体类的 fetch_history 应不被调用
    from browser_history.browsers import ChromiumBasedBrowser, Firefox
    monkeypatch.setattr(
        ChromiumBasedBrowser, "fetch_history",
        lambda self: (_ for _ in ()).throw(AssertionError("不应被调用")),
    )
    monkeypatch.setattr(
        Firefox, "fetch_history",
        lambda self: (_ for _ in ()).throw(AssertionError("不应被调用")),
    )

    source = BrowserSource()
    events = source.collect()
    assert len(events) == 1
    assert events[0].url_or_path == "https://github.com/a"
