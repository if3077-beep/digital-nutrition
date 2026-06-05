"""Tests for history storage."""
import json
from datetime import datetime
from pathlib import Path
from digital_nutrition.history.store import save_report, load_history, list_reports, get_history_dir


def test_save_and_load_roundtrip(tmp_path):
    """保存和读取往返一致"""
    save_report({"by_category": {"code": 1000}}, "🧱", ["i1"], history_dir=tmp_path)
    history = load_history(history_dir=tmp_path)
    assert history[0]["by_category"]["code"] == 1000
    assert history[0]["persona"] == "🧱"
    assert history[0]["insights"] == ["i1"]


def test_load_history_respects_limit(tmp_path):
    """limit 限制返回数量"""
    for i in range(5):
        save_report({"i": i}, f"p{i}", [], history_dir=tmp_path)
    # 先验证 5 个文件都写进去了
    files = list(tmp_path.glob("*.json"))
    assert len(files) == 5
    history = load_history(limit=2, history_dir=tmp_path)
    assert len(history) == 2


def test_list_reports_sorted_newest_first(tmp_path):
    """倒序排列"""
    import os
    p1 = save_report({"a": 1}, "p1", [], history_dir=tmp_path)
    p2 = save_report({"a": 2}, "p2", [], history_dir=tmp_path)
    # 强制让 p2 的 mtime 晚于 p1（Windows mtime 精度可能 1s+，两次 save 同一秒会相等）
    s1 = p1.stat().st_mtime
    os.utime(p2, (s1 + 2, s1 + 2))
    files = list(tmp_path.glob("*.json"))
    assert len(files) == 2
    listed = list_reports(history_dir=tmp_path)
    # p2 时间晚，应排第一
    assert listed[0] == p2
    assert listed[1] == p1


def test_get_history_dir_creates_dir():
    """get_history_dir 自动创建目录"""
    import digital_nutrition.history.store as h
    # 不污染真实 home，用 monkeypatch 思路：直接调用应不抛错
    d = h.get_history_dir()
    assert d.exists()
    assert d.name == "history"
