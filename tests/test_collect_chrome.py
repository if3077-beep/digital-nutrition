import os
import sys
import pytest
from pathlib import Path
from scripts.collect_chrome import get_chrome_history_path, get_chrome_user_data_dir, find_chrome_profiles


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
