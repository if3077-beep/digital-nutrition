"""Tests for history storage."""
import json
from datetime import datetime
from pathlib import Path
from digital_nutrition.history.store import (
    list_html_reports, save_report, load_history, list_reports, get_history_dir
)


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


def test_save_report_with_html_copies_to_history(tmp_path):
    """提供 html_path 时应把 HTML 复制到 history_dir（同名 stem）"""
    # 准备 HTML 和 assets
    html_src = tmp_path / "report_src"
    html_src.mkdir()
    html_file = html_src / "report.html"
    html_file.write_text('<script src="assets/echarts.min.js"></script>', encoding="utf-8")
    assets_src = html_src / "assets"
    assets_src.mkdir()
    (assets_src / "echarts.min.js").write_text("dummy", encoding="utf-8")

    history_dir = tmp_path / "history"
    save_report(
        {"by_category": {"code": 100}}, "🧱", ["i1"],
        history_dir=history_dir, html_path=html_file,
    )

    # 找到 HTML
    htmls = list(history_dir.glob("*.html"))
    assert len(htmls) == 1
    html_dest = htmls[0]

    # 资源引用被改写
    assert f'src="{html_dest.stem}_assets/' in html_dest.read_text(encoding="utf-8")

    # assets 目录被复制
    assets_dest = history_dir / f"{html_dest.stem}_assets"
    assert assets_dest.exists()
    assert (assets_dest / "echarts.min.js").exists()


def test_save_report_without_html_does_not_create_html(tmp_path):
    """不提供 html_path 时不应创建 HTML 文件"""
    history_dir = tmp_path / "history"
    save_report({"by_category": {"code": 100}}, "🧱", ["i1"], history_dir=history_dir)
    assert not list(history_dir.glob("*.html"))


def test_save_report_html_path_missing_does_not_raise(tmp_path):
    """html_path 不存在时应优雅处理（不抛错）"""
    history_dir = tmp_path / "history"
    save_report(
        {"by_category": {"code": 100}}, "🧱", ["i1"],
        history_dir=history_dir, html_path=tmp_path / "nope.html",
    )
    assert not list(history_dir.glob("*.html"))


def test_list_html_reports_returns_only_html(tmp_path):
    """list_html_reports 只返回 HTML，按 mtime 倒序"""
    history_dir = tmp_path / "history"
    history_dir.mkdir()
    # 创建 2 个 HTML 和 1 个 JSON
    (history_dir / "a.html").write_text("a", encoding="utf-8")
    import time
    time.sleep(0.05)
    (history_dir / "b.html").write_text("b", encoding="utf-8")
    (history_dir / "c.json").write_text("{}", encoding="utf-8")

    htmls = list_html_reports(history_dir=history_dir)
    assert len(htmls) == 2
    # b 较新，排第一
    assert htmls[0].name == "b.html"
    assert htmls[1].name == "a.html"


def test_list_html_reports_empty(tmp_path):
    """无 HTML 时返回空列表"""
    assert list_html_reports(history_dir=tmp_path) == []
