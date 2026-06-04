"""
端到端测试 - 完整流程
"""
import subprocess
import sys
from pathlib import Path


def test_cli_help():
    """测试 CLI 帮助信息"""
    result = subprocess.run(
        [sys.executable, "-m", "scripts.main", "--help"],
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
        [sys.executable, "-m", "scripts.main", "weekly", "--help"],
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
