import os
import sys
import pytest
from datetime import datetime
from pathlib import Path
from scripts.collect_chrome import get_chrome_history_path, get_chrome_user_data_dir, find_chrome_profiles, read_chrome_history, _webkit_to_datetime


def test_get_user_data_dir_windows(monkeypatch):
    """测试 Windows 路径"""
    monkeypatch.setattr("sys.platform", "win32")
    monkeypatch.setenv("LOCALAPPDATA", "C:\\Users\\test\\AppData\\Local")
    path = get_chrome_user_data_dir()
    assert "Google" in str(path)
    assert "Chrome" in str(path)
    assert "User Data" in str(path)


def test_get_user_data_dir_mac(monkeypatch):
    """测试 macOS 路径"""
    monkeypatch.setattr("sys.platform", "darwin")
    monkeypatch.setattr("pathlib.Path.home", lambda: Path("/Users/test"))
    path = get_chrome_user_data_dir()
    assert "Chrome" in str(path)
    assert "Application Support" in str(path)


def test_get_user_data_dir_linux(monkeypatch):
    """测试 Linux 路径"""
    monkeypatch.setattr("sys.platform", "linux")
    monkeypatch.setattr("pathlib.Path.home", lambda: Path("/home/test"))
    path = get_chrome_user_data_dir()
    assert ".config" in str(path)
    assert "google-chrome" in str(path)


def test_get_chrome_history_path_default(monkeypatch):
    """测试默认 profile 路径"""
    monkeypatch.setattr("sys.platform", "linux")
    monkeypatch.setattr("pathlib.Path.home", lambda: Path("/home/test"))
    path = get_chrome_history_path()
    assert path.name == "History"
    assert "Default" in str(path)


def test_find_chrome_profiles_empty(tmp_path, monkeypatch):
    """测试不存在的 Chrome 目录"""
    monkeypatch.setattr("scripts.collect_chrome.get_chrome_user_data_dir", lambda: tmp_path / "nonexistent")
    profiles = find_chrome_profiles()
    assert profiles == []


def test_find_chrome_profiles_finds_default(tmp_path, monkeypatch):
    """测试能找到 Default profile"""
    chrome_dir = tmp_path / "chrome"
    default_dir = chrome_dir / "Default"
    default_dir.mkdir(parents=True)
    (default_dir / "History").touch()

    monkeypatch.setattr("scripts.collect_chrome.get_chrome_user_data_dir", lambda: chrome_dir)
    profiles = find_chrome_profiles()
    assert len(profiles) == 1
    assert profiles[0] == default_dir


# === Task 5: Chrome 历史读取 ===

def test_webkit_to_datetime():
    """测试 WebKit 时间戳转换（WebKit 时间戳基于 UTC）"""
    # WebKit 时间戳基于 UTC，所以我们用 UTC datetime 构造测试输入
    # 2024-06-01 10:00:00 UTC
    from datetime import timezone
    test_dt_utc = datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc)
    webkit_us = int((test_dt_utc.timestamp() + 11644473600) * 1_000_000)
    dt = _webkit_to_datetime(webkit_us)
    # 返回的 datetime 应是 UTC 时间，hour=10
    assert dt.hour == 10
    assert dt.tzinfo is not None  # 应该是带时区的


def test_read_chrome_history_basic():
    """从 fixture 读取历史并验证结果"""
    fixture_db = Path(__file__).parent / "fixtures" / "chrome_history_sample.db"
    if not fixture_db.exists():
        pytest.skip("Fixture not created. Run: python -m tests.fixtures.create_fixture")

    events = read_chrome_history(fixture_db, since=None)
    assert len(events) == 6
    # 所有事件都标记为 source="browser"
    assert all(e.source == "browser" for e in events)
    # 包含已知 URL
    urls = {e.url_or_path for e in events}
    assert "https://github.com/user/repo" in urls
    assert "https://youtube.com/watch?v=abc" in urls


def test_read_chrome_history_with_since_filter():
    """测试时间过滤"""
    fixture_db = Path(__file__).parent / "fixtures" / "chrome_history_sample.db"
    if not fixture_db.exists():
        pytest.skip("Fixture not created. Run: python -m tests.fixtures.create_fixture")

    # 只取 2024-06-01 13:00 之后的事件
    since = datetime(2024, 6, 1, 13, 0)
    events = read_chrome_history(fixture_db, since=since)
    # 应该包含 youtube, weibo, unknown (3 条)
    assert len(events) == 3


def test_read_chrome_history_nonexistent_file(tmp_path):
    """读取不存在的文件返回空列表"""
    events = read_chrome_history(tmp_path / "nonexistent.db", since=None)
    assert events == []


def test_read_chrome_history_event_structure():
    """验证 Event 字段正确性"""
    fixture_db = Path(__file__).parent / "fixtures" / "chrome_history_sample.db"
    if not fixture_db.exists():
        pytest.skip("Fixture not created. Run: python -m tests.fixtures.create_fixture")

    events = read_chrome_history(fixture_db, since=None)
    github_event = next(e for e in events if "github" in e.url_or_path)
    # duration_us=5_000_000 → 5 秒
    assert github_event.duration_seconds == 5
    assert github_event.category == "other"  # 还没分类
    assert github_event.title == "GitHub Repo"
