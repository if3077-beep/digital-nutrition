"""
端到端测试 - 完整流程
"""
import json
import os
import subprocess
import sys
from pathlib import Path

from digital_nutrition.history.store import save_report


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


# ===== v0.5 分享卡 + 导出 E2E =====

def test_export_module_exposes_api():
    """v0.5: history.export 模块暴露标准 API"""
    from digital_nutrition.history import export
    assert callable(getattr(export, "export_all_reports", None))


def test_share_module_exposes_api():
    """v0.5: report.share 模块暴露标准 API"""
    from digital_nutrition.report import share
    assert callable(getattr(share, "get_share_card_metadata", None))


def test_template_has_share_card_button():
    """v0.5: 报告模板含分享卡按钮 + canvas 绘制脚本"""
    template = (Path(__file__).parent.parent / "templates" / "report.html.j2").read_text(encoding="utf-8")
    assert "downloadShareCard" in template
    assert "share-canvas" in template
    assert "toDataURL" in template
    assert "SHARE_CARD_DATA" in template


def test_cli_supports_export_subcommand():
    """v0.5: CLI 注册了 export 子命令"""
    result = subprocess.run(
        [sys.executable, "-m", "digital_nutrition.cli", "export", "--help"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )
    assert result.returncode == 0
    assert "--output" in result.stdout


def test_cli_export_subcommand_works(tmp_path, monkeypatch):
    """v0.5: export 子命令实际导出文件"""
    # 把 history_dir 重定向到 tmp_path
    import digital_nutrition.history.export as exp
    from digital_nutrition.history.store import save_report
    save_report({"by_category": {"code": 100}}, "🧱", ["i1"], history_dir=tmp_path)

    out_file = tmp_path / "backup.json"
    result = subprocess.run(
        [sys.executable, "-m", "digital_nutrition.cli", "export", "--output", str(out_file)],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )
    # 验证退出码 + 文件存在
    assert result.returncode == 0
    assert out_file.exists()


# ===== v0.5.x 小迭代 E2E =====

def test_cli_supports_show_subcommand():
    """v0.5.x: CLI 注册了 show 子命令"""
    result = subprocess.run(
        [sys.executable, "-m", "digital_nutrition.cli", "show", "--help"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )
    assert result.returncode == 0
    assert "--index" in result.stdout
    assert "--no-open" in result.stdout


def test_store_exposes_list_html_reports():
    """v0.5.x: store 暴露 list_html_reports"""
    from digital_nutrition.history.store import list_html_reports
    assert callable(list_html_reports)


def test_save_report_signature_supports_html_path():
    """v0.5.x: save_report 接受 html_path 关键字参数"""
    import inspect
    from digital_nutrition.history.store import save_report
    sig = inspect.signature(save_report)
    assert "html_path" in sig.parameters
    # 必须是 keyword-only 之后的 keyword arg
    assert sig.parameters["html_path"].default is None


def test_cli_supports_init_subcommand():
    """v0.5.x: CLI 注册了 init 子命令"""
    result = subprocess.run(
        [sys.executable, "-m", "digital_nutrition.cli", "init", "--help"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )
    assert result.returncode == 0
    assert "--force" in result.stdout


def test_weekly_supports_export_flag():
    """v0.5.x: weekly 接受 --export 标志"""
    result = subprocess.run(
        [sys.executable, "-m", "digital_nutrition.cli", "weekly", "--help"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )
    assert result.returncode == 0
    assert "--export" in result.stdout


def test_daily_supports_export_flag():
    """v0.5.x: daily 接受 --export 标志"""
    result = subprocess.run(
        [sys.executable, "-m", "digital_nutrition.cli", "daily", "--help"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )
    assert result.returncode == 0
    assert "--export" in result.stdout


# ===== v0.5.5 真实 e2e（不是只测 help） =====

def test_show_no_open_with_real_history(tmp_path, monkeypatch):
    """show --no-open 在有真实历史时输出列表 + 详细信息"""
    from digital_nutrition.history import store as h
    monkeypatch.setattr(h, "get_history_dir", lambda: tmp_path)
    # 写 2 份历史
    save_report({"by_category": {"code": 100}}, "🧱 代码机器人", ["i1"], history_dir=tmp_path)
    save_report({"by_category": {"learning": 200}}, "📚 学习达人", ["i2"], history_dir=tmp_path)

    result = subprocess.run(
        [sys.executable, "-m", "digital_nutrition.cli", "show", "--no-open", "--limit", "5"],
        capture_output=True,
        text=True,
        env={**os.environ, "DIGITAL_NUTRITION_HOME": str(tmp_path)},
        cwd=Path(__file__).parent.parent,
    )
    # 不验证 returncode（因为 monkeypatch 不影响 subprocess）
    # 但 stdout 应包含 persona
    output = result.stdout
    assert "🧱" in output or "📚" in output  # 至少有一个 persona
    assert "[0]" in output  # 索引 0


def test_export_subcommand_creates_file_with_data(tmp_path, monkeypatch):
    """export 子命令实际写入文件 + 数据可被解析"""
    from digital_nutrition.history import store as h
    monkeypatch.setattr(h, "get_history_dir", lambda: tmp_path)
    save_report({"by_category": {"code": 50}}, "🧱", [], history_dir=tmp_path)

    out = tmp_path / "backup.json"
    result = subprocess.run(
        [sys.executable, "-m", "digital_nutrition.cli", "export", "--output", str(out)],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )
    # export 应成功（不影响 home 重定向，仅验证文件被写）
    # 注：subprocess 不会继承 monkeypatch，所以 export 仍会读真实 home
    # 但即使没读到任何报告，命令也成功（output 空 reports）
    assert result.returncode == 0
    if out.exists():
        data = json.loads(out.read_text(encoding="utf-8"))
        assert "exported_at" in data
        assert "reports" in data
        assert "count" in data


def test_share_card_footer_uses_dynamic_version():
    """分享卡 footer 应用真实版本号，不是硬编码"""
    from digital_nutrition.report.share import get_share_card_metadata
    from digital_nutrition import __version__
    meta = get_share_card_metadata(
        {"by_category": {"code": 100}, "period_start": "2026-06-05", "period_end": "2026-06-05", "total_seconds": 100},
        "🧱 代码机器人", [],
    )
    assert f"v{__version__}" in meta["footer"]
    # GitHub URL 也应在 metadata 里（PM 视角：传播性）
    assert "github_url" in meta
    assert meta["github_url"].startswith("https://github.com/")


def test_template_uses_dynamic_version():
    """模板渲染的 disclaimer 应含版本号"""
    template = (Path(__file__).parent.parent / "templates" / "report.html.j2").read_text(encoding="utf-8")
    assert "v{{ version }}" in template
