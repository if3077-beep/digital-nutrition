"""
端到端测试 - 完整流程
"""
import subprocess
import sys
from pathlib import Path


def test_cli_help():
    """测试 CLI 帮助信息"""
    result = subprocess.run(
        [sys.executable, "-m", "digital_nutrition.cli", "--help"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )
    assert result.returncode == 0
    assert "weekly" in result.stdout
    assert "daily" in result.stdout


def test_weekly_subcommand_help():
    """测试 weekly 子命令帮助"""
    result = subprocess.run(
        [sys.executable, "-m", "digital_nutrition.cli", "weekly", "--help"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )
    assert result.returncode == 0
    assert "--no-open" in result.stdout


def test_assets_dir_has_echarts():
    """ECharts 资源已下载"""
    assets = Path(__file__).parent.parent / "assets"
    assert assets.exists()
    assert (assets / "echarts.min.js").exists()
    size_kb = (assets / "echarts.min.js").stat().st_size / 1024
    assert size_kb > 500  # ECharts 至少 500KB


def test_templates_dir_has_template():
    """HTML 模板存在"""
    templates = Path(__file__).parent.parent / "templates"
    assert templates.exists()
    assert (templates / "report.html.j2").exists()


def test_skill_md_exists():
    """SKILL.md 入口存在"""
    skill_md = Path(__file__).parent.parent / "SKILL.md"
    assert skill_md.exists()
    content = skill_md.read_text(encoding="utf-8")
    assert "name: digital-nutrition" in content
    assert "weekly" in content


# ===== v0.2 趋势功能 E2E =====

def test_history_module_exposes_api():
    """v0.2: history 模块暴露标准 API"""
    from digital_nutrition.history import store as history
    assert callable(getattr(history, "save_report", None))
    assert callable(getattr(history, "load_history", None))
    assert callable(getattr(history, "list_reports", None))
    assert callable(getattr(history, "get_history_dir", None))


def test_trend_module_exposes_api():
    """v0.2: trend 模块暴露标准 API"""
    from digital_nutrition import trend
    assert callable(getattr(trend, "build_daily_aggregates", None))
    assert callable(getattr(trend, "compute_category_deltas", None))


def test_report_template_supports_daily_chart():
    """v0.2: 报告模板支持每日趋势图"""
    template = (Path(__file__).parent.parent / "templates" / "report.html.j2").read_text(encoding="utf-8")
    assert "daily_chart_data" in template
    assert "daily_chart_dates" in template
    assert "daily-chart" in template  # ECharts 容器 ID


def test_main_uses_pipeline_integration():
    """v0.2: cli.py 集成 history + trend"""
    main_src = (Path(__file__).parent.parent / "digital_nutrition" / "cli.py").read_text(encoding="utf-8")
    assert "from digital_nutrition.history.store import" in main_src
    assert "from digital_nutrition.trend import" in main_src
    assert "save_report" in main_src
    assert "load_history" in main_src
    assert "build_daily_aggregates" in main_src
    assert "compute_category_deltas" in main_src


def test_skill_md_documents_v02_features():
    """v0.2: SKILL.md 反映新功能"""
    skill_md = (Path(__file__).parent.parent / "SKILL.md").read_text(encoding="utf-8")
    # v0.2 应提及历史/趋势
    assert "v0.2" in skill_md or "趋势" in skill_md or "历史" in skill_md
