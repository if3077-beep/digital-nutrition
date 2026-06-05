"""
Digital Nutrition Label - CLI 入口
"""
import argparse
import json
import sys
import threading
import time
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from digital_nutrition import __version__
from digital_nutrition.analyze import apply_classification, build_report_data
from digital_nutrition.classify import (
    get_user_rules_path,
    init_user_rules,
    load_default_rules,
    load_ignored_domains,
    load_user_rules,
    merge_rules,
)
from digital_nutrition.history.export import export_all_reports
from digital_nutrition.history.store import (
    get_history_dir,
    list_html_reports,
    load_history,
    save_report,
)
from digital_nutrition.insight import generate_insights
from digital_nutrition.models import Event
from digital_nutrition.persona import classify_persona
from digital_nutrition.report.generator import render_report
from digital_nutrition.serve import find_free_port, serve_directory
from digital_nutrition.sources.browser import BrowserSource
from digital_nutrition.sources.git import GitSource
from digital_nutrition.trend import build_daily_aggregates, compute_category_deltas

# === v0.5.9: Windows emoji 兼容 ===
# Windows GBK 终端下 emoji 报 UnicodeEncodeError → 降级为 ASCII
# 优先尝试把 stdout reconfigure 到 utf-8（Windows Terminal / 新 PowerShell 都能）
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

_EMOJI_SUPPORT = bool(
    sys.stdout.encoding and sys.stdout.encoding.lower().replace("-", "") in ("utf8", "utf16", "utf32")
)


def _emoji(e: str, fallback: str = "") -> str:
    """emoji 安全降级：终端支持 UTF-8 时返回 emoji，否则返回 ASCII fallback"""
    return e if _EMOJI_SUPPORT else fallback


# 常用 emoji 的 fallback 映射
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


def _p(emoji_key: str, text: str) -> str:
    """组装带 emoji 的文本（不直接 print，方便测试）"""
    prefix = _FALLBACKS.get(emoji_key, emoji_key)
    if _EMOJI_SUPPORT:
        return f"{emoji_key} {text}"
    return f"{prefix} {text}"


# === v0.6.0: 统一输出 helpers（资深码农视角：减少重复） ===
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


# 首次运行标记文件
_FIRST_RUN_MARKER = ".first-run-shown"


def collect_browser_events(since: Optional[datetime] = None) -> List[Event]:
    """通过 BrowserSource 采集所有浏览器历史（Chrome/Edge/Firefox/Safari/Arc/Zen/Brave 等）"""
    source = BrowserSource()
    if not source.is_available():
        return []
    try:
        return source.collect(since=since)
    except Exception as e:
        # 友好提示：常见原因：Chrome 没关（锁住 History.db）/ 权限不够
        _print_warn(f"浏览器历史读取失败：{e}")
        print(f"    常见原因：Chrome 还在运行（会锁住 History 数据库），先关掉试试")
        return []


def collect_git_events(since: Optional[datetime] = None, repo_dir: Optional[Path] = None) -> List[Event]:
    """采集 Git 活动"""
    if repo_dir is None:
        repo_dir = Path.cwd()

    if not (repo_dir / ".git").exists():
        # 这是常见情况：用户在工作目录跑命令，不在 git 仓库
        # 静默跳过比 warning 更友好（不是错误）
        return []

    source = GitSource(repo_dir=repo_dir)
    if not source.is_available():
        return []
    try:
        return source.collect(since=since)
    except Exception as e:
        _print_warn(f"Git 活动读取失败：{e}")
        print(f"    试试指定 --repo 参数指向你的代码仓库")
        return []


def generate_report(
    period: str = "weekly",
    output_dir: Optional[Path] = None,
    open_browser: bool = True,
    repo_dir: Optional[Path] = None,
    auto_export: Optional[Path] = None,
    since: Optional[str] = None,
    output_json: bool = False,
) -> Path:
    """
    生成完整报告。

    Args:
        period: "daily" 或 "weekly"
        output_dir: 输出目录
        open_browser: 是否自动打开浏览器
        repo_dir: Git 仓库目录

    Returns:
        HTML 报告路径
    """
    # 计算时间范围
    now = datetime.now()
    if period == "daily":
        default_start = now - timedelta(days=1)
    else:  # weekly
        default_start = now - timedelta(days=7)
    period_end = now

    # v0.6.0: --since 参数覆盖默认起始日期（review Phase 4 #10）
    period_start = default_start
    if since is not None:
        try:
            period_start = datetime.fromisoformat(since)
        except ValueError:
            _print_warn(f"--since 格式错误：{since}（期望 YYYY-MM-DD），用默认 {default_start:%Y-%m-%d}")

    # ===== 📊 收集阶段 =====
    print()
    print(f"{_emoji('📊')} [1/3] 收集数据（{period}：{period_start:%Y-%m-%d} → {period_end:%Y-%m-%d}）...")
    browser_events = collect_browser_events(since=period_start)
    git_events = collect_git_events(since=period_start, repo_dir=repo_dir)
    all_events = browser_events + git_events
    print(f"   {_emoji('📥')} {len(browser_events)} browser + {len(git_events)} git = {len(all_events)} 事件")

    # 加载规则
    rules = merge_rules(load_default_rules(), load_user_rules())

    # v0.6.0: 加载隐私忽略列表（review Phase 4 #9）
    ignored_domains = load_ignored_domains()

    # ===== Pipeline =====
    # 1) 采集 + 分类（apply_classification 内部对 browser 事件做域名分类 + 过滤 ignore）
    classified = apply_classification(all_events, rules, ignored_domains)

    # 2) 聚合（按类别/天/小时）— 同一份 ignored_domains 传给 build_report_data 保持一致
    report_data = build_report_data(all_events, rules, period_start, period_end, ignored_domains)
    daily_aggregates = build_daily_aggregates(classified)

    # 3) 加载历史，计算趋势 deltas
    prev_history = load_history(limit=1)
    prev_by_cat = prev_history[0].get("by_category", {}) if prev_history else {}
    deltas = (
        compute_category_deltas(report_data["by_category"], prev_by_cat)
        if prev_by_cat else None
    )

    # 4) 人格 + 洞察
    persona = classify_persona(report_data["by_category"])
    insights = generate_insights(
        report_data["by_category"],
        report_data["by_hour"],
        deltas=deltas,
        by_day_of_week=report_data.get("by_day_of_week"),
    )

    # ===== ⚙️ 渲染阶段 =====
    print()
    print(f"{_emoji('⚙️')} [2/3] 渲染报告...")
    if output_dir is None:
        output_dir = Path.cwd() / ".digital-nutrition-report"
    html_path = render_report(
        report_data, persona, insights, output_dir,
        daily_aggregates=daily_aggregates,
    )

    # ===== 💾 持久化阶段 =====
    print(f"{_emoji('💾')} [3/3] 持久化历史...")
    save_report(report_data, persona, insights, html_path=html_path)

    # ===== 输出 summary（v0.6.0 拆出） =====
    _print_summary(html_path, persona, insights, deltas, prev_history, all_events, report_data)

    # 可选：自动导出所有历史为 JSON
    if auto_export is not None:
        out = export_all_reports(auto_export)
        print(f"{_emoji('💾')} Auto-exported all history → {out}")

    # v0.6.0: --json 输出模式（CI / 脚本友好）
    if output_json:
        import json as _json
        json_payload = {
            "persona": persona,
            "insights": list(insights),  # List[str]，直接序列化
            "report_data": report_data,
            "html_path": str(html_path),
        }
        print()  # 分离友好输出和机器可读
        print(_json.dumps(json_payload, default=str, ensure_ascii=False, indent=2))

    if open_browser:
        _open_browser(output_dir)

    return html_path


def _print_summary(
    html_path: Path,
    persona: str,
    insights: list,
    deltas,
    prev_history: list,
    all_events: list,
    report_data: dict,
) -> None:
    """v0.6.0 拆出：打印 report summary（persona / insights / Top 3 / 本周概况 / 试试）

    资深码农视角：原 generate_report 函数超过 120 行，难以维护。
    拆出后：
      - generate_report 只管 orchestration
      - _print_summary 只管输出（可独立单测 + 调换格式）
    """
    _print_ok(f"Report generated: {html_path}")
    _print_info(f"Persona: {persona}")
    _print_info(f"{len(insights)} insights")
    if deltas:
        _print_info(f"Trend comparison loaded from {len(prev_history)} previous report")

    # 1) 空数据引导
    if not all_events:
        _print_section("💭", "这次没采集到任何活动数据。常见原因：")
        print("   - Chrome/Edge 还在运行（锁住了 History.db）→ 关闭后重试")
        print("   - 当前目录不是 Git 仓库 → 用 --repo 参数指定")
        print("   - 想给常用域名加分类？ → 跑 `digital-nutrition init`")

    # 2) Top 3 域名
    top_sources = report_data.get("top_sources", [])
    url_sources = [
        (url, secs) for url, secs in top_sources
        if url.startswith(("http://", "https://", "ftp://"))
    ][:3]
    if url_sources:
        _print_section("🔥", "你访问最多的：")
        for url, secs in url_sources:
            display = url if len(url) <= 60 else url[:57] + "..."
            print(f"   • {display}  ({format_human(secs)})")

    # 3) 本周概况
    _print_weekly_snapshot(all_events, report_data)

    # 4) "💡 试试" 提示区块
    _print_try_hints()


def _print_weekly_snapshot(all_events: list, report_data: dict) -> None:
    """v0.6.0 拆出：本周概况区块（总时长/总事件/最忙日/高峰时段）"""
    total_sec = report_data.get("total_seconds", 0)
    n_events = len(all_events)
    by_day = report_data.get("by_day", {})
    by_hour = report_data.get("by_hour", {})
    _print_section("📊", "本周概况：")
    print(f"   • 总时长：{format_human(total_sec)}（估算）")
    print(f"   • 总事件：{n_events}")
    if by_day:
        busiest_day = max(by_day.items(), key=lambda x: sum(x[1].values()))[0]
        try:
            wd = datetime.strptime(busiest_day, "%Y-%m-%d").weekday()
            cn_wd = ["一", "二", "三", "四", "五", "六", "日"][wd]
            print(f"   • 最忙日：周{cn_wd}（{busiest_day}）")
        except ValueError:
            print(f"   • 最忙日：{busiest_day}")
    if by_hour:
        peak_hour = max(by_hour.items(), key=lambda x: x[1])[0]
        print(f"   • 高峰时段：{peak_hour:02d}:00（{format_human(by_hour[peak_hour])}）")


def _print_try_hints() -> None:
    """v0.6.0 拆出：'试试' 提示区块（引导发现后续操作）"""
    _print_section("💡", "试试：")
    print("   • `digital-nutrition show`  →  重新打开这份报告")
    print("   • `digital-nutrition init`  →  自定义域名分类（更准的洞察）")
    print("   • `digital-nutrition export --output backup.json`  →  备份历史")
    print("   • `digital-nutrition doctor`  →  自检环境")


def _open_browser(output_dir: Path) -> None:
    """v0.6.0 拆出：启动本地 server + 打开浏览器（带 try/except 兜底）"""
    port = find_free_port()
    server_thread = threading.Thread(
        target=serve_directory,
        args=(output_dir, port),
        daemon=True,
    )
    server_thread.start()
    time.sleep(0.5)
    url = f"http://127.0.0.1:{port}/report.html"
    print(f"{_emoji('🌐')} Opening {url}")
    try:
        if not webbrowser.open(url):
            _print_warn(f"浏览器未自动打开，请手动访问：{url}")
    except webbrowser.Error as e:
        _print_warn(f"打开浏览器失败：{e}")
        print(f"   手动访问：{url}")


def main():
    """CLI 入口"""
    parser = argparse.ArgumentParser(
        prog="digital-nutrition",
        description="生成你的开发者数字人格报告 (v{})".format(__version__),
        epilog=(
            "示例流程：\n"
            "  1. digital-nutrition init          首次：创建 user_rules.json 模板\n"
            "  2. digital-nutrition weekly        生成本周报告（自动开浏览器）\n"
            "  3. digital-nutrition show          重新打开 / 列出历史报告\n"
            "  4. digital-nutrition export -o bk.json  备份所有历史\n"
            "\n"
            "文档：https://github.com/if3077-beep/digital-nutrition"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version", action="version",
        version=f"digital-nutrition {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command")

    # weekly 子命令
    weekly = subparsers.add_parser("weekly", help="生成本周报告")
    weekly.add_argument("--repo", type=Path, help="Git 仓库路径")
    weekly.add_argument("--output", type=Path, help="输出目录")
    weekly.add_argument("--no-open", action="store_true", help="不自动打开浏览器")
    weekly.add_argument(
        "--export", type=Path, default=None, metavar="PATH",
        help="跑完自动 export 所有历史到 PATH（如 backup.json）",
    )
    weekly.add_argument(
        "--since", type=str, default=None, metavar="YYYY-MM-DD",
        help="覆盖默认 7 天，自定义起始日期（如 2026-05-01）",
    )

    # daily 子命令
    daily = subparsers.add_parser("daily", help="生成今日报告")
    daily.add_argument("--repo", type=Path, help="Git 仓库路径")
    daily.add_argument("--output", type=Path, help="输出目录")
    daily.add_argument("--no-open", action="store_true", help="不自动打开浏览器")
    daily.add_argument(
        "--export", type=Path, default=None, metavar="PATH",
        help="跑完自动 export 所有历史到 PATH",
    )
    daily.add_argument(
        "--since", type=str, default=None, metavar="YYYY-MM-DD",
        help="覆盖默认 1 天，自定义起始日期（如 2026-06-04）",
    )
    daily.add_argument(
        "--json", action="store_true",
        help="把 report data 额外 dump 为 JSON 到 stdout",
    )

    # export 子命令
    export_p = subparsers.add_parser("export", help="导出所有历史报告为 JSON")
    export_p.add_argument(
        "--output", type=Path, required=True, help="输出文件路径（如 backup.json）"
    )

    # show 子命令
    show = subparsers.add_parser("show", help="查看/打开历史报告")
    show.add_argument(
        "--index", type=int, default=0,
        help="要打开的报告索引（0=最新，1=次新...），默认 0",
    )
    show.add_argument(
        "--limit", type=int, default=10,
        help="列表显示数量（仅在 --no-open 时生效），默认 10",
    )
    show.add_argument(
        "--no-open", action="store_true",
        help="只列出报告，不打开浏览器",
    )

    # init 子命令
    init_p = subparsers.add_parser(
        "init", help="在用户配置目录创建 user_rules.json 模板",
    )
    init_p.add_argument(
        "--force", action="store_true",
        help="已存在时强制覆盖",
    )

    # doctor 子命令
    doctor = subparsers.add_parser(
        "doctor", help="自检环境（浏览器/Git/配置/历史目录）",
    )
    doctor.add_argument(
        "--repo", type=Path, default=None,
        help="Git 仓库路径（默认当前目录）",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # 跳过：version flag、init/export/show/doctor 子命令不触发 first-run
    if args.command not in ("init", "export", "show", "doctor"):
        _maybe_welcome_first_run()

    if args.command == "export":
        out = export_all_reports(args.output)
        print(f"{_emoji('✅')} Exported to {out}")
        return

    if args.command == "show":
        _cmd_show(args)
        return

    if args.command == "init":
        _cmd_init(args)
        return

    if args.command == "doctor":
        _cmd_doctor(args)
        return

    repo_dir = getattr(args, "repo", None)
    output_dir = getattr(args, "output", None)
    open_browser = not getattr(args, "no_open", False)
    auto_export = getattr(args, "export", None)
    since = getattr(args, "since", None)
    output_json = getattr(args, "json", False)

    generate_report(
        period=args.command,
        output_dir=output_dir,
        open_browser=open_browser,
        repo_dir=repo_dir,
        auto_export=auto_export,
        since=since,
        output_json=output_json,
    )


def _cmd_show(args):
    """`show` 子命令：列出 / 打开历史报告"""
    reports = list_html_reports()
    if not reports:
        print(f"{_emoji('📭')} 暂无历史报告。先跑一次 `digital-nutrition weekly`。")
        return

    if args.no_open:
        # 打印列表（persona + 日期 + 简要统计）
        print(f"{_emoji('📚')} 找到 {len(reports)} 份历史报告（最新在前）：")
        for i, p in enumerate(reports[:args.limit]):
            data = _read_report_for_html(p)
            persona = data.get("persona", "?")
            saved = data.get("saved_at", "")[:16].replace("T", " ")
            total = data.get("total_seconds", 0)
            top = _top_category_label(data.get("by_category", {}))
            print(f"  [{i}] {p.name}  {saved}  {persona}  {format_human(total)}  · {top}")
        return

    # 打开指定 index
    if args.index < 0 or args.index >= len(reports):
        print(f"{_emoji('❌')} --index 超出范围（0-{len(reports) - 1}）")
        sys.exit(1)
    target = reports[args.index]
    persona = _read_persona_for_html(target)

    # 启动 server 服务 history_dir（这样 assets 相对路径能解析）
    history_dir = target.parent
    port = find_free_port()
    server_thread = threading.Thread(
        target=serve_directory,
        args=(history_dir, port),
        daemon=True,
    )
    server_thread.start()
    time.sleep(0.5)
    url = f"http://127.0.0.1:{port}/{target.name}"
    print(f"{_emoji('📊')} Opening [{args.index}] {persona}  →  {url}")
    webbrowser.open(url)


def _read_persona_for_html(html_path: Path) -> str:
    """从与 HTML 同 stem 的 JSON 文件读 persona，失败则返回 '?'"""
    return _read_report_for_html(html_path).get("persona", "?")


def _read_report_for_html(html_path: Path) -> dict:
    """从与 HTML 同 stem 的 JSON 文件读完整报告，失败则返回空 dict"""
    json_path = html_path.with_suffix(".json")
    if not json_path.exists():
        return {}
    try:
        return json.loads(json_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _top_category_label(by_category: dict) -> str:
    """返回 by_category 中时长最大的类别名（中文），空时返回 '—'"""
    if not by_category:
        return "—"
    from digital_nutrition.models import CATEGORY_META
    top_cat = max(by_category.items(), key=lambda x: x[1])[0]
    meta = CATEGORY_META.get(top_cat, {})
    return f"{meta.get('icon', '❓')}{meta.get('name', top_cat)}"


def format_human(seconds: int) -> str:
    """秒 → 人类可读 (e.g. '2h 34m' / '45m' / '<1m')"""
    if seconds < 60:
        return "<1m"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m"
    hours = minutes // 60
    mins = minutes % 60
    if mins == 0:
        return f"{hours}h"
    return f"{hours}h {mins}m"


def _cmd_init(args):
    """`init` 子命令：创建 user_rules.json 模板"""
    path, created = init_user_rules(force=args.force)
    if created:
        _print_ok(f"Created user rules template: {path}")
        print()
        print("📝 接下来：")
        print(f"  1. 编辑文件，添加你想分类的域名（按 learning/work/... 分类）")
        print(f"  2. 跑 `digital-nutrition weekly` 自动应用")
    else:
        _print_info(f"Rules file already exists: {path}")
        print(f"   用 --force 强制覆盖")


def _cmd_doctor(args):
    """`doctor` 子命令：自检环境（PM 视角：发现性 + 错误预防）"""
    from digital_nutrition import classify as classify_mod
    from digital_nutrition.history import store as store_mod

    print()
    print(f"{_emoji('🩺')} Digital Nutrition Label - 环境自检")
    print("=" * 44)

    ok = warn = err = 0
    hints = []

    # 1) browser-history 库
    try:
        import browser_history
        ver = getattr(browser_history, "__version__", "?")
        print(f"{_emoji('✅')} browser-history {ver} 已安装")
        ok += 1
    except ImportError:
        print(f"{_emoji('❌')} browser-history 库未安装。`pip install browser-history`")
        err += 1
        hints.append("先 `pip install browser-history` 再重试")

    # 2) 浏览器扫描
    try:
        from browser_history import get_history
        # 静音 browser-history 库的 INFO 日志（库没提供 disable 机制，只能包一层）
        import logging
        logging.getLogger("browser-history").setLevel(logging.WARNING)
        outputs = get_history()
        n_histories = len(outputs.histories) if outputs.histories else 0
        if n_histories > 0:
            # 推断 host 多样性（粗略判断浏览器种类）
            from urllib.parse import urlparse
            hosts = set()
            for entry in outputs.histories[:200]:  # 抽 200 条够了
                try:
                    url = entry[1] if len(entry) > 1 else ""
                    if url:
                        host = urlparse(url).netloc
                        if host:
                            hosts.add(host)
                except (ValueError, IndexError):
                    pass
            print(f"{_emoji('✅')} 浏览器历史：{n_histories} 条（{len(hosts)} 个独立 host）")
            ok += 1
            # 提示 Chrome/Edge 在运行可能锁住 History.db
            # （用户经常忘记关 Chrome）
            print(f"{_emoji('💡')} 提示：跑 weekly 前关掉 Chrome/Edge 窗口（避免锁住 History.db）")
        else:
            _print_warn("没找到任何浏览器历史（访问几个网页再来）")
            warn += 1
    except Exception as e:
        print(f"{_emoji('❌')} 浏览器扫描失败：{e}")
        err += 1

    # 3) Git 仓库
    repo_dir = args.repo or Path.cwd()
    if (repo_dir / ".git").exists():
        print(f"{_emoji('✅')} Git 仓库：{repo_dir}")
        ok += 1
    else:
        print(f"{_emoji('❌')} 不是 Git 仓库：{repo_dir}（用 --repo 指定，或 cd 到仓库目录）")
        err += 1
        hints.append("cd 到你的代码仓库目录再跑 `weekly` / `doctor`")

    # 4) user_rules.json
    config_path = classify_mod.get_user_rules_path()
    if config_path.exists():
        try:
            rules = classify_mod.load_user_rules()
            n_rules = sum(len(v) for k, v in rules.items() if k != "_comment")
            print(f"{_emoji('✅')} 自定义规则：{config_path}（{n_rules} 条）")
            ok += 1
        except (json.JSONDecodeError, OSError) as e:
            _print_warn(f"规则文件存在但解析失败：{e}")
            warn += 1
            hints.append("删除或修复 `{}`".format(config_path))
    else:
        print(f"{_emoji('ℹ️')}  未配置自定义规则（用 `digital-nutrition init` 创建）")
        # 算 warn，因为建议配置
        warn += 1
        hints.append("跑 `digital-nutrition init` 自定义常用域名分类")

    # 5) history 目录
    history_dir = store_mod.get_history_dir()
    try:
        history_dir.mkdir(parents=True, exist_ok=True)
        # 测试可写
        test_file = history_dir / ".doctor-write-test"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink()
        n_history = len(list(history_dir.glob("*.json")))
        print(f"{_emoji('✅')} 历史目录可写：{history_dir}（{n_history} 份报告）")
        ok += 1
    except OSError as e:
        print(f"{_emoji('❌')} 历史目录不可写：{history_dir}（{e}）")
        err += 1

    # 总结
    print()
    print(f"{_emoji('📊')} 总结：{ok} ✅ / {warn} ⚠️ / {err} ❌")
    if hints:
        print()
        print(f"{_emoji('💡')} 建议：")
        for h in hints:
            print(f"   • {h}")
    print()
    sys.exit(0 if err == 0 else 1)


def _maybe_welcome_first_run():
    """
    首次运行 weekly/daily 时打印欢迎信息（只一次）。
    判断逻辑：
      1. 标记文件存在 → 已显示过，跳过
      2. history_dir 内有 *.json → 用户已经跑过 weekly/daily，老手，跳过
      3. 否则 → 首次使用，打印欢迎 + 写标记
    """
    from digital_nutrition import classify as classify_mod
    from digital_nutrition.history import store as store_mod

    history_dir = store_mod.get_history_dir()
    marker = history_dir / _FIRST_RUN_MARKER
    if marker.exists():
        return

    # 老手：已经有历史报告（说明 weekly/daily 跑过）
    has_history = bool(list(history_dir.glob("*.json")))
    if has_history:
        # 不显欢迎，但写标记避免重复判断
        try:
            marker.write_text(datetime.now().isoformat(), encoding="utf-8")
        except OSError:
            pass
        return

    config_path = classify_mod.get_user_rules_path()

    print()
    print(f"{_emoji('👋')} 欢迎使用 数字营养标签 (Digital Nutrition Label)！")
    print()
    print("   看起来这是你第一次跑。建议先做：")
    print()
    print("   1. `digital-nutrition init`  ← 创建自定义规则模板")
    print("      （按 learning / work / entertainment 等分类你的常用域名）")
    print()
    print("   2. `digital-nutrition weekly`  ← 生成本周人格报告")
    print()
    print("   3. `digital-nutrition show`    ← 之后可以打开历史报告")
    print()
    print(f"   {_emoji('💡')} 配置文件位置：{config_path}")
    print(f"   {_emoji('📂')} 历史报告位置：{history_dir}")
    print()

    # 写标记
    try:
        marker.write_text(datetime.now().isoformat(), encoding="utf-8")
    except OSError:
        pass  # best-effort


if __name__ == "__main__":
    main()
