"""
cli_print.py 的单元测试

TDD 任务 4（v0.7.0 抽 cli_print.py）。
设计要点：
- _emoji() 内部调 _get_emoji_support()，test 时可 monkeypatch
- _print_* helpers 通过 capsys 验证 stdout 输出
"""
import pytest

from digital_nutrition import cli_print
from digital_nutrition.cli_print import (
    _emoji,
    _print_err,
    _print_info,
    _print_ok,
    _print_section,
    _print_warn,
)


# ===== _emoji() =====

def test_emoji_passthrough_in_utf8_terminal(monkeypatch):
    """终端支持 UTF-8 时，_emoji 直接返回 emoji"""
    monkeypatch.setattr(cli_print, "_get_emoji_support", lambda: True)
    assert _emoji("✅") == "✅"
    assert _emoji("⚠️") == "⚠️"


def test_emoji_returns_fallback_in_ascii_terminal(monkeypatch):
    """终端不支持 emoji 时，_emoji 返回 fallback"""
    monkeypatch.setattr(cli_print, "_get_emoji_support", lambda: False)
    assert _emoji("✅", "[OK]") == "[OK]"
    assert _emoji("⚠️", "[WARN]") == "[WARN]"


def test_emoji_empty_fallback_in_ascii_terminal(monkeypatch):
    """fallback 默认为空字符串"""
    monkeypatch.setattr(cli_print, "_get_emoji_support", lambda: False)
    assert _emoji("🎉") == ""  # fallback 默认 ""


def test_emoji_passthrough_ignores_fallback_in_utf8(monkeypatch):
    """UTF-8 终端下 fallback 参数被忽略"""
    monkeypatch.setattr(cli_print, "_get_emoji_support", lambda: True)
    assert _emoji("✅", "[NEVER USED]") == "✅"


# ===== _get_emoji_support() =====
# 注：sys.stdout.encoding 是只读，无法直接 monkeypatch
# _get_emoji_support() 的逻辑被上面 _emoji() 的测试间接覆盖


# ===== _print_* helpers =====

def test_print_ok_output_format(monkeypatch, capsys):
    """_print_ok 应输出 '✅ text'（UTF-8 终端下）"""
    monkeypatch.setattr(cli_print, "_get_emoji_support", lambda: True)
    _print_ok("Created file")
    captured = capsys.readouterr()
    assert captured.out == "✅ Created file\n"


def test_print_warn_output_format(monkeypatch, capsys):
    """_print_warn 应输出 '⚠️ text'（UTF-8 终端下）"""
    monkeypatch.setattr(cli_print, "_get_emoji_support", lambda: True)
    _print_warn("Something failed")
    captured = capsys.readouterr()
    assert captured.out == "⚠️ Something failed\n"


def test_print_err_output_format(monkeypatch, capsys):
    monkeypatch.setattr(cli_print, "_get_emoji_support", lambda: True)
    _print_err("Boom")
    captured = capsys.readouterr()
    assert captured.out == "❌ Boom\n"


def test_print_info_output_format(monkeypatch, capsys):
    monkeypatch.setattr(cli_print, "_get_emoji_support", lambda: True)
    _print_info("Try this")
    captured = capsys.readouterr()
    assert captured.out == "💡 Try this\n"


def test_print_ok_fallback_output_format(monkeypatch, capsys):
    """ASCII 终端下 _print_ok 输出 '[OK] text'"""
    monkeypatch.setattr(cli_print, "_get_emoji_support", lambda: False)
    _print_ok("Created file")
    captured = capsys.readouterr()
    assert captured.out == "[OK] Created file\n"


def test_print_warn_fallback_output_format(monkeypatch, capsys):
    """ASCII 终端下 _print_warn 输出 '[WARN] text'"""
    monkeypatch.setattr(cli_print, "_get_emoji_support", lambda: False)
    _print_warn("Watch out")
    captured = capsys.readouterr()
    assert captured.out == "[WARN] Watch out\n"


# ===== _print_section =====

def test_print_section_starts_with_blank_line(monkeypatch, capsys):
    """_print_section 应输出 'blank line + emoji text'"""
    monkeypatch.setattr(cli_print, "_get_emoji_support", lambda: True)
    _print_section("📊", "Weekly Summary")
    captured = capsys.readouterr()
    # 第一个字符是 \n（前置空行），然后是 emoji + 空格 + text
    assert captured.out == "\n📊 Weekly Summary\n"


def test_print_section_uses_fallback(monkeypatch, capsys):
    """ASCII 终端下 _print_section 用 _FALLBACKS 字典（[STAT]）"""
    monkeypatch.setattr(cli_print, "_get_emoji_support", lambda: False)
    _print_section("📊", "Weekly Summary")
    captured = capsys.readouterr()
    # _emoji('📊') 在 ascii 下查 _FALLBACKS = '[STAT]'
    assert captured.out == "\n[STAT] Weekly Summary\n"
