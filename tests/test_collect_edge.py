import sys
import pytest
from pathlib import Path
from scripts.collect_edge import get_edge_history_path, find_edge_profiles, get_edge_user_data_dir


def test_get_user_data_dir_windows(monkeypatch):
    """测试 Windows 路径"""
    monkeypatch.setattr("sys.platform", "win32")
    monkeypatch.setenv("LOCALAPPDATA", "C:\\Users\\test\\AppData\\Local")
    path = get_edge_user_data_dir()
    assert "Microsoft" in str(path)
    assert "Edge" in str(path)
    assert "User Data" in str(path)


def test_get_user_data_dir_mac(monkeypatch):
    """测试 macOS 路径"""
    monkeypatch.setattr("sys.platform", "darwin")
    monkeypatch.setattr("pathlib.Path.home", lambda: Path("/Users/test"))
    path = get_edge_user_data_dir()
    assert "Edge" in str(path)
    assert "Application Support" in str(path)


def test_get_user_data_dir_linux(monkeypatch):
    """测试 Linux 路径（仍返回路径对象，即使不存在）"""
    monkeypatch.setattr("sys.platform", "linux")
    monkeypatch.setattr("pathlib.Path.home", lambda: Path("/home/test"))
    path = get_edge_user_data_dir()
    assert path is not None
    assert "microsoft-edge" in str(path).lower() or "edge" in str(path).lower()


def test_get_edge_history_path_default(monkeypatch):
    """测试默认 profile 路径"""
    monkeypatch.setattr("sys.platform", "linux")
    monkeypatch.setattr("pathlib.Path.home", lambda: Path("/home/test"))
    path = get_edge_history_path()
    assert path.name == "History"
    assert "Default" in str(path)


def test_find_edge_profiles_empty(tmp_path, monkeypatch):
    """测试不存在的 Edge 目录"""
    monkeypatch.setattr("scripts.collect_edge.get_edge_user_data_dir", lambda: tmp_path / "nonexistent")
    profiles = find_edge_profiles()
    assert profiles == []
