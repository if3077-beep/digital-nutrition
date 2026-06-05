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
from digital_nutrition import __version__
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
    assert __version__ in result.stdout
    assert "digital-nutrition" in result.stdout


# ===== doctor 子命令 =====

def test_doctor_subcommand_exists():
    """doctor 子命令应在 --help 中列出"""
    result = subprocess.run(
        [sys.executable, "-m", "digital_nutrition.cli", "--help"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )
    assert result.returncode == 0
    assert "doctor" in result.stdout


def test_doctor_runs_and_prints_summary(tmp_path, monkeypatch, capsys):
    """doctor 子命令：能跑起来 + 打印总结（5 项检查）"""
    from digital_nutrition.cli import _cmd_doctor
    from argparse import Namespace

    # 1) 模拟空 history_dir（写到 tmp_path）
    from digital_nutrition.history import store as h
    monkeypatch.setattr(h, "get_history_dir", lambda: tmp_path)

    # 2) 模拟 Git 仓库不存在（cwd 是 tmp_path）
    monkeypatch.chdir(tmp_path)

    # 3) 模拟 user_rules.json 路径
    from digital_nutrition import classify as c_mod
    fake_rules = tmp_path / "user_rules.json"
    monkeypatch.setattr(c_mod, "get_user_rules_path", lambda: fake_rules)

    args = Namespace(repo=None)
    # doctor 会在 err 时 sys.exit(1)。用 try/except 捕获 SystemExit。
    import pytest as _pytest
    with _pytest.raises(SystemExit) as exc:
        _cmd_doctor(args)
    # 没有 git 仓库 → 至少 1 个 err → exit code 1
    assert exc.value.code == 1

    out = capsys.readouterr().out
    assert "🩺" in out
    assert "环境自检" in out
    assert "总结" in out
    assert "browser-history" in out
    # 没有 .git → 报 ❌
    assert "❌" in out
    # 总结行
    assert "✅" in out


def test_doctor_passes_with_git_repo_and_rules(tmp_path, monkeypatch, capsys):
    """doctor 在 Git 仓库存在 + 规则文件存在时通过所有检查"""
    from digital_nutrition.cli import _cmd_doctor
    from argparse import Namespace
    from digital_nutrition.history import store as h
    from digital_nutrition import classify as c_mod

    # 模拟 .git 目录
    (tmp_path / ".git").mkdir()

    monkeypatch.setattr(h, "get_history_dir", lambda: tmp_path)

    # 模拟 user_rules.json
    fake_rules = tmp_path / "user_rules.json"
    fake_rules.write_text(json.dumps({"learning": ["myblog.com"]}), encoding="utf-8")
    monkeypatch.setattr(c_mod, "get_user_rules_path", lambda: fake_rules)

    args = Namespace(repo=None)
    # 改 cwd 到 tmp_path（这样 .git 存在能被检测到）
    monkeypatch.chdir(tmp_path)

    import pytest as _pytest
    with _pytest.raises(SystemExit) as exc:
        _cmd_doctor(args)
    # 现在 Git 仓库存在 → 0 err → exit code 0
    assert exc.value.code == 0

    out = capsys.readouterr().out
    # 3 个 ✅ 至少：browser-history、Git 仓库、history 目录
    # （浏览器历史可能为空 → ⚠️，user_rules 已配置 → ✅）
    assert out.count("✅") >= 3
    assert "建议" not in out  # 没 err → 没建议


# ===== v0.7.0 rules CLI 子命令（任务 2） =====

def test_cmd_rules_list_prints_user_rules(tmp_path, monkeypatch, capsys):
    """rules list: 打印当前 user_rules.json 内容"""
    from argparse import Namespace
    from digital_nutrition.cli import _cmd_rules
    from digital_nutrition import classify as c_mod

    fake_rules = tmp_path / "user_rules.json"
    fake_rules.write_text(
        '{"learning": ["foo.com"], "work": ["bar.com"]}', encoding="utf-8"
    )
    monkeypatch.setattr(c_mod, "get_user_rules_path", lambda: fake_rules)

    args = Namespace(rules_command="list")
    _cmd_rules(args)

    out = capsys.readouterr().out
    assert "foo.com" in out
    assert "bar.com" in out
    assert "learning" in out
    assert "work" in out


def test_cmd_rules_list_empty_file(tmp_path, monkeypatch, capsys):
    """rules list: 文件不存在时友好提示"""
    from argparse import Namespace
    from digital_nutrition.cli import _cmd_rules
    from digital_nutrition import classify as c_mod

    fake_rules = tmp_path / "user_rules.json"
    monkeypatch.setattr(c_mod, "get_user_rules_path", lambda: fake_rules)

    args = Namespace(rules_command="list")
    _cmd_rules(args)

    out = capsys.readouterr().out
    # 空规则时友好提示
    assert ("空" in out) or ("empty" in out.lower()) or ("[WARN]" in out) or ("💡" in out)


def test_cmd_rules_add_writes_file(tmp_path, monkeypatch, capsys):
    """rules add: 写文件 + 提示成功"""
    import json
    from argparse import Namespace
    from digital_nutrition.cli import _cmd_rules
    from digital_nutrition import classify as c_mod

    fake_rules = tmp_path / "user_rules.json"
    monkeypatch.setattr(c_mod, "get_user_rules_path", lambda: fake_rules)

    args = Namespace(rules_command="add", domain="bilibili.com", category="entertainment")
    _cmd_rules(args)

    data = json.loads(fake_rules.read_text(encoding="utf-8"))
    assert data == {"entertainment": ["bilibili.com"]}
    out = capsys.readouterr().out
    assert "bilibili.com" in out
    assert "entertainment" in out


def test_cmd_rules_add_rejects_duplicate(tmp_path, monkeypatch, capsys):
    """rules add 重复 domain → 友好错误提示，不写文件"""
    from argparse import Namespace
    from digital_nutrition.cli import _cmd_rules
    from digital_nutrition import classify as c_mod

    fake_rules = tmp_path / "user_rules.json"
    fake_rules.write_text('{"entertainment": ["bilibili.com"]}', encoding="utf-8")
    monkeypatch.setattr(c_mod, "get_user_rules_path", lambda: fake_rules)

    args = Namespace(rules_command="add", domain="bilibili.com", category="work")
    _cmd_rules(args)  # 不应抛异常（友好处理）

    out = capsys.readouterr().out
    # 提示用户已存在（❌ 或 [ERR] 或 警告）
    assert "已" in out or "err" in out.lower() or "❌" in out or "exists" in out.lower() or "[ERR]" in out


def test_cmd_rules_remove_existing(tmp_path, monkeypatch, capsys):
    """rules remove 已存在 → 提示已删除"""
    from argparse import Namespace
    from digital_nutrition.cli import _cmd_rules
    from digital_nutrition import classify as c_mod

    fake_rules = tmp_path / "user_rules.json"
    fake_rules.write_text(
        '{"entertainment": ["bilibili.com", "twitch.tv"]}', encoding="utf-8"
    )
    monkeypatch.setattr(c_mod, "get_user_rules_path", lambda: fake_rules)

    args = Namespace(rules_command="remove", domain="bilibili.com")
    _cmd_rules(args)

    out = capsys.readouterr().out
    assert "bilibili.com" in out
    # 删除提示（✅ 或 [OK] 或"已删"）
    assert "✅" in out or "[OK]" in out or "删" in out or "removed" in out.lower()


def test_cmd_rules_remove_not_found(tmp_path, monkeypatch, capsys):
    """rules remove 不存在 → 提示未找到"""
    from argparse import Namespace
    from digital_nutrition.cli import _cmd_rules
    from digital_nutrition import classify as c_mod

    fake_rules = tmp_path / "user_rules.json"
    fake_rules.write_text('{"entertainment": ["twitch.tv"]}', encoding="utf-8")
    monkeypatch.setattr(c_mod, "get_user_rules_path", lambda: fake_rules)

    args = Namespace(rules_command="remove", domain="nonexistent.com")
    _cmd_rules(args)

    out = capsys.readouterr().out
    assert "nonexistent.com" in out


def test_cmd_rules_test_classifies_url(tmp_path, monkeypatch, capsys):
    """rules test: 用合并后的规则测试 URL 分类"""
    from argparse import Namespace
    from digital_nutrition.cli import _cmd_rules
    from digital_nutrition import classify as c_mod

    fake_rules = tmp_path / "user_rules.json"
    fake_rules.write_text('{"learning": ["bilibili.com"]}', encoding="utf-8")
    monkeypatch.setattr(c_mod, "get_user_rules_path", lambda: fake_rules)

    args = Namespace(rules_command="test", url="https://www.bilibili.com/video/xxx")
    _cmd_rules(args)

    out = capsys.readouterr().out
    # 应输出分类结果（learning 或 entertainment 等）
    assert "bilibili.com" in out
    # 至少包含一个分类关键词
    assert any(
        cat in out for cat in
        ["code", "learning", "work", "entertainment", "news", "social", "shopping", "other"]
    )


def test_cmd_rules_list_separates_ignored_domains(tmp_path, monkeypatch, capsys):
    """rules list 应把 ignored_domains 单独分区显示（不混在类别里）"""
    from argparse import Namespace
    from digital_nutrition.cli import _cmd_rules
    from digital_nutrition import classify as c_mod

    fake_rules = tmp_path / "user_rules.json"
    fake_rules.write_text(
        json.dumps({
            "learning": ["foo.com"],
            "ignored_domains": ["bank.com", "hr.com"],
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(c_mod, "get_user_rules_path", lambda: fake_rules)

    args = Namespace(rules_command="list")
    _cmd_rules(args)

    out = capsys.readouterr().out
    # foo.com 应显示在 learning 类别
    assert "foo.com" in out
    # ignored 域名应显示在隐私列表区（不带 → ignored_domains）
    assert "bank.com" in out
    assert "→ ignored_domains" not in out  # 关键断言
    # 隐私列表提示
    assert "隐私" in out or "忽略" in out or "🚫" in out
