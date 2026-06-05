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
        print(f"Warning: Browser history read failed: {e}")
        return []


def collect_git_events(since: Optional[datetime] = None, repo_dir: Optional[Path] = None) -> List[Event]:
    """采集 Git 活动"""
    if repo_dir is None:
        repo_dir = Path.cwd()

    if not (repo_dir / ".git").exists():
        return []

    source = GitSource(repo_dir=repo_dir)
    if not source.is_available():
        return []
    try:
        return source.collect(since=since)
    except Exception as e:
        print(f"Warning: Git read failed: {e}")
        return []


def generate_report(
    period: str = "weekly",
    output_dir: Optional[Path] = None,
    open_browser: bool = True,
    repo_dir: Optional[Path] = None,
    auto_export: Optional[Path] = None,
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
        period_start = now - timedelta(days=1)
    else:  # weekly
        period_start = now - timedelta(days=7)
    period_end = now

    # 采集数据
    browser_events = collect_browser_events(since=period_start)
    git_events = collect_git_events(since=period_start, repo_dir=repo_dir)
    all_events = browser_events + git_events
    print(f"📥 Collected {len(browser_events)} browser + {len(git_events)} git events")

    # 加载规则
    rules = merge_rules(load_default_rules(), load_user_rules())

    # ===== Pipeline =====
    # 1) 采集 + 分类（apply_classification 内部对 browser 事件做域名分类）
    classified = apply_classification(all_events, rules)

    # 2) 聚合（按类别/天/小时）
    report_data = build_report_data(all_events, rules, period_start, period_end)
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

    # 5) 渲染报告
    if output_dir is None:
        output_dir = Path.cwd() / ".digital-nutrition-report"
    html_path = render_report(
        report_data, persona, insights, output_dir,
        daily_aggregates=daily_aggregates,
    )

    # 6) 保存到历史（放在 render 之后，避免影响当前报告的 by_category）
    #    顺便把 HTML 存一份，方便 `show` 子命令直接打开历史报告
    save_report(report_data, persona, insights, html_path=html_path)

    print(f"✅ Report generated: {html_path}")
    print(f"📊 Persona: {persona}")
    print(f"💡 {len(insights)} insights")
    if deltas:
        print(f"📈 Trend comparison loaded from {len(prev_history)} previous report")

    # 可选：自动导出所有历史为 JSON
    if auto_export is not None:
        out = export_all_reports(auto_export)
        print(f"💾 Auto-exported all history → {out}")

    if open_browser:
        # 启动 server 并打开浏览器
        port = find_free_port()
        server_thread = threading.Thread(
            target=serve_directory,
            args=(output_dir, port),
            daemon=True,
        )
        server_thread.start()
        time.sleep(0.5)
        url = f"http://127.0.0.1:{port}/report.html"
        print(f"🌐 Opening {url}")
        webbrowser.open(url)

    return html_path


def main():
    """CLI 入口"""
    parser = argparse.ArgumentParser(
        prog="digital-nutrition",
        description="生成你的开发者数字人格报告 (v{})".format(__version__),
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

    # daily 子命令
    daily = subparsers.add_parser("daily", help="生成今日报告")
    daily.add_argument("--repo", type=Path, help="Git 仓库路径")
    daily.add_argument("--output", type=Path, help="输出目录")
    daily.add_argument("--no-open", action="store_true", help="不自动打开浏览器")
    daily.add_argument(
        "--export", type=Path, default=None, metavar="PATH",
        help="跑完自动 export 所有历史到 PATH",
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

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # 跳过：version flag、init/export/show 子命令不触发 first-run
    if args.command not in ("init", "export", "show"):
        _maybe_welcome_first_run()

    if args.command == "export":
        out = export_all_reports(args.output)
        print(f"✅ Exported to {out}")
        return

    if args.command == "show":
        _cmd_show(args)
        return

    if args.command == "init":
        _cmd_init(args)
        return

    repo_dir = getattr(args, "repo", None)
    output_dir = getattr(args, "output", None)
    open_browser = not getattr(args, "no_open", False)
    auto_export = getattr(args, "export", None)

    generate_report(
        period=args.command,
        output_dir=output_dir,
        open_browser=open_browser,
        repo_dir=repo_dir,
        auto_export=auto_export,
    )


def _cmd_show(args):
    """`show` 子命令：列出 / 打开历史报告"""
    reports = list_html_reports()
    if not reports:
        print("📭 暂无历史报告。先跑一次 `digital-nutrition weekly`。")
        return

    if args.no_open:
        # 打印列表（persona + 日期 + 简要统计）
        print(f"📚 找到 {len(reports)} 份历史报告（最新在前）：")
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
        print(f"❌ --index 超出范围（0-{len(reports) - 1}）")
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
    print(f"📊 Opening [{args.index}] {persona}  →  {url}")
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
        print(f"✅ Created user rules template: {path}")
        print()
        print("📝 接下来：")
        print(f"  1. 编辑文件，添加你想分类的域名（按 learning/work/... 分类）")
        print(f"  2. 跑 `digital-nutrition weekly` 自动应用")
    else:
        print(f"ℹ️  Rules file already exists: {path}")
        print(f"   用 --force 强制覆盖")


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
    print("👋 欢迎使用 数字营养标签 (Digital Nutrition Label)！")
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
    print("   💡 配置文件位置：{}".format(config_path))
    print("   📂 历史报告位置：{}".format(history_dir))
    print()

    # 写标记
    try:
        marker.write_text(datetime.now().isoformat(), encoding="utf-8")
    except OSError:
        pass  # best-effort


if __name__ == "__main__":
    main()
