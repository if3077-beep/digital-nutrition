"""
Digital Nutrition Label - CLI 入口
"""
import argparse
import sys
import threading
import time
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from digital_nutrition.analyze import apply_classification, build_report_data
from digital_nutrition.classify import load_default_rules, load_user_rules, merge_rules
from digital_nutrition.history.export import export_all_reports
from digital_nutrition.history.store import load_history, save_report
from digital_nutrition.insight import generate_insights
from digital_nutrition.models import Event
from digital_nutrition.persona import classify_persona
from digital_nutrition.report.generator import render_report
from digital_nutrition.serve import find_free_port, serve_directory
from digital_nutrition.sources.browser import BrowserSource
from digital_nutrition.sources.git import GitSource
from digital_nutrition.trend import build_daily_aggregates, compute_category_deltas


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
    )

    # 5) 渲染报告
    if output_dir is None:
        output_dir = Path.cwd() / ".digital-nutrition-report"
    html_path = render_report(
        report_data, persona, insights, output_dir,
        daily_aggregates=daily_aggregates,
    )

    # 6) 保存到历史（放在 render 之后，避免影响当前报告的 by_category）
    save_report(report_data, persona, insights)

    print(f"✅ Report generated: {html_path}")
    print(f"📊 Persona: {persona}")
    print(f"💡 {len(insights)} insights")
    if deltas:
        print(f"📈 Trend comparison loaded from {len(prev_history)} previous report")

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
        description="生成你的开发者数字人格报告"
    )
    subparsers = parser.add_subparsers(dest="command")

    # weekly 子命令
    weekly = subparsers.add_parser("weekly", help="生成本周报告")
    weekly.add_argument("--repo", type=Path, help="Git 仓库路径")
    weekly.add_argument("--output", type=Path, help="输出目录")
    weekly.add_argument("--no-open", action="store_true", help="不自动打开浏览器")

    # daily 子命令
    daily = subparsers.add_parser("daily", help="生成今日报告")
    daily.add_argument("--repo", type=Path, help="Git 仓库路径")
    daily.add_argument("--output", type=Path, help="输出目录")
    daily.add_argument("--no-open", action="store_true", help="不自动打开浏览器")

    # export 子命令
    export_p = subparsers.add_parser("export", help="导出所有历史报告为 JSON")
    export_p.add_argument(
        "--output", type=Path, required=True, help="输出文件路径（如 backup.json）"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "export":
        out = export_all_reports(args.output)
        print(f"✅ Exported to {out}")
        return

    repo_dir = getattr(args, "repo", None)
    output_dir = getattr(args, "output", None)
    open_browser = not getattr(args, "no_open", False)

    generate_report(
        period=args.command,
        output_dir=output_dir,
        open_browser=open_browser,
        repo_dir=repo_dir,
    )


if __name__ == "__main__":
    main()
