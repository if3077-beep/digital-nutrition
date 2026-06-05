"""
CLI 输出 helpers（v0.7.0 抽离自 cli.py）

职责：
- emoji 兼容层（Windows GBK 终端降级为 ASCII）
- 统一 _print_* 输出 helpers

抽离动机：cli.py 700+ 行 → 减少 80 行，子命令文件不关心 emoji 细节。
"""
import sys


# === 模块顶层副作用（仅 import 时执行一次） ===
# Windows GBK 终端下 emoji 报 UnicodeEncodeError → 降级为 ASCII
# 优先尝试把 stdout reconfigure 到 utf-8（Windows Terminal / 新 PowerShell 都能）
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass


# === Fallback 映射：emoji → ASCII 文本 ===
# 终端不支持 emoji 时用这些 ASCII 字符串替代
_FALLBACKS = {
    "✅": "[OK]",
    "❌": "[ERR]",
    "⚠️": "[WARN]",
    "💾": "[SAVE]",
    "📊": "[STAT]",
    "📅": "[DATE]",
    "💡": "[TIP]",
    "🔥": "[HOT]",
    "🏷️": "[TAG]",
    "🩺": "[CHECK]",
    "📈": "[TREND]",
    "📥": "[IN]",
    "💭": "[NOTE]",
    "ℹ️": "[INFO]",
}


def _get_emoji_support() -> bool:
    """检测 stdout 是否支持 emoji（可被 monkeypatch 用于测试）"""
    return bool(
        sys.stdout.encoding
        and sys.stdout.encoding.lower().replace("-", "").replace("_", "") in ("utf8", "utf16", "utf32")
    )


def _emoji(e: str, fallback: str = "") -> str:
    """emoji 安全降级：终端支持 UTF-8 时返回 emoji，否则返回 fallback / _FALLBACKS 字典值"""
    if _get_emoji_support():
        return e
    # 优先用显式 fallback，否则查 _FALLBACKS 字典
    if fallback:
        return fallback
    return _FALLBACKS.get(e, "")


# === 统一输出 helpers（资深码农视角：减少重复） ===

def _print_ok(text: str) -> None:
    """✅ 成功"""
    print(f"{_emoji('✅')} {text}")


def _print_err(text: str) -> None:
    """❌ 错误"""
    print(f"{_emoji('❌')} {text}")


def _print_warn(text: str) -> None:
    """⚠️ 警告"""
    print(f"{_emoji('⚠️')} {text}")


def _print_info(text: str) -> None:
    """💡 提示"""
    print(f"{_emoji('💡')} {text}")


def _print_section(emoji_key: str, text: str) -> None:
    """📊/🔥/🩺 等 section header（自带前置空行）"""
    print()
    print(f"{_emoji(emoji_key)} {text}")
