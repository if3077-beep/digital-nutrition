"""Tests for CLI helpers."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from digital_nutrition.cli import (
    _read_report_for_html,
    _top_category_label,
    format_human,
    _maybe_welcome_first_run,
)
from digital_nutrition.history.store import save_report


# ===== format_human =====

def test_format_human_seconds_under_minute():
    assert format_human(0) == "<1m"
    assert format_human(30) == "<1m"
    assert format_human(59) == "<1m"


def test_format_human_minutes():
    assert format_human(60) == "1m"
    assert format_human(45 * 60) == "45m"
    assert format_human(59 * 60) == "59m"


def test_format_human_hours_only():
    assert format_human(60 * 60) == "1h"
    assert format_human(2 * 60 * 60) == "2h"


def test_format_human_hours_and_minutes():
    assert format_human(60 * 60 + 30 * 60) == "1h 30m"
    assert format_human(2 * 60 * 60 + 34 * 60) == "2h 34m"


# ===== _top_category_label =====

def test_top_category_label_returns_chinese_name():
    assert _top_category_label({"code": 100, "learning": 50}) == "💻写代码"


def test_top_category_label_picks_max():
    by_cat = {"code": 100, "entertainment": 500, "learning": 200}
    # entertainment 最大
    assert "🎬" in _top_category_label(by_cat)


def test_top_category_label_empty():
    assert _top_category_label({}) == "—"


# ===== _read_report_for_html =====

def test_read_report_for_html_returns_dict(tmp_path):
    """从 HTML 同 stem 的 JSON 读完整报告"""
    html = tmp_path / "2026-06-05_xxx.html"
    json_path = tmp_path / "2026-06-05_xxx.json"
    json_path.write_text(
        json.dumps({"persona": "🧱", "saved_at": "2026-06-05T12:00:00", "by_category": {"code": 100}}),
        encoding="utf-8",
    )
    data = _read_report_for_html(html)
    assert data["persona"] == "🧱"
    assert data["by_category"]["code"] == 100


def test_read_report_for_html_missing_json(tmp_path):
    """无 JSON 时返回空 dict 而非崩溃"""
    html = tmp_path / "nope.html"
    assert _read_report_for_html(html) == {}


def test_read_report_for_html_corrupt_json(tmp_path):
    """坏 JSON 时返回空 dict"""
    html = tmp_path / "bad.html"
    (tmp_path / "bad.json").write_text("{not json", encoding="utf-8")
    assert _read_report_for_html(html) == {}


# ===== _maybe_welcome_first_run =====

def test_welcome_first_run_creates_marker(tmp_path, monkeypatch, capsys):
    """首次运行应打印欢迎信息 + 写标记"""
    # 重定向 history_dir / config_path 到 tmp_path
    from digital_nutrition.history import store as h
    from digital_nutrition import classify as c_mod
    monkeypatch.setattr(h, "get_history_dir", lambda: tmp_path)
    # 把分类规则路径也重定向到 tmp_path 子目录
    fake_config = tmp_path / "user_rules.json"
    monkeypatch.setattr(c_mod, "get_user_rules_path", lambda: fake_config)

    _maybe_welcome_first_run()
    captured = capsys.readouterr()
    assert "欢迎" in captured.out
    assert "init" in captured.out
    assert (tmp_path / ".first-run-shown").exists()


def test_welcome_first_run_skips_after_marker(tmp_path, monkeypatch, capsys):
    """第二次跑不再打印欢迎"""
    from digital_nutrition.history import store as h
    monkeypatch.setattr(h, "get_history_dir", lambda: tmp_path)
    (tmp_path / ".first-run-shown").write_text("2026-06-05", encoding="utf-8")

    _maybe_welcome_first_run()
    captured = capsys.readouterr()
    assert "欢迎" not in captured.out


def test_welcome_skipped_when_history_exists(tmp_path, monkeypatch, capsys):
    """已有历史报告时不视为首次"""
    from digital_nutrition.history import store as h
    from digital_nutrition import classify as c_mod
    monkeypatch.setattr(h, "get_history_dir", lambda: tmp_path)
    fake_config = tmp_path / "user_rules.json"
    monkeypatch.setattr(c_mod, "get_user_rules_path", lambda: fake_config)
    # 写一个历史报告
    save_report({"by_category": {"code": 100}}, "🧱", [], history_dir=tmp_path)

    _maybe_welcome_first_run()
    captured = capsys.readouterr()
    assert "欢迎" not in captured.out
    # 标记仍写
    assert (tmp_path / ".first-run-shown").exists()


# ===== CLI --version =====

def test_cli_version_flag():
    """--version 输出版本号并退出"""
    result = subprocess.run(
        [sys.executable, "-m", "digital_nutrition.cli", "--version"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )
    assert result.returncode == 0
    assert "0.5.5" in result.stdout
    assert "digital-nutrition" in result.stdout
