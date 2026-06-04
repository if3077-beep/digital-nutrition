"""Tests for main entry point."""
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from scripts.main import generate_report
from scripts.models import Event


def test_generate_report_creates_html(tmp_path):
    """端到端：生成报告并验证 HTML 文件"""
    output_dir = tmp_path / "report"

    # Mock 数据采集以避免真实读取浏览器/Git
    with patch("scripts.main.collect_browser_events") as mock_browser, \
         patch("scripts.main.collect_git_events") as mock_git:
        mock_browser.return_value = [
            Event(
                timestamp=datetime(2024, 6, 1, 10, 0),
                duration_seconds=1800,
                source="browser",
                category="other",
                subcategory=None,
                title="GH",
                url_or_path="https://github.com",
            ),
        ]
        mock_git.return_value = [
            Event(
                timestamp=datetime(2024, 6, 1, 11, 0),
                duration_seconds=1800,
                source="git",
                category="code",
                subcategory=None,
                title="feat: x",
                url_or_path="/r",
            ),
        ]

        html_path = generate_report(
            period="weekly",
            output_dir=output_dir,
            open_browser=False,
        )

        assert html_path.exists()
        content = html_path.read_text(encoding="utf-8")
        # 报告必须包含分类名称或人格图标
        assert "github" in content.lower() or "学习" in content


def test_generate_report_with_insights(tmp_path):
    """生成包含洞察的报告"""
    output_dir = tmp_path / "report"

    with patch("scripts.main.collect_browser_events") as mock_browser, \
         patch("scripts.main.collect_git_events") as mock_git:
        mock_browser.return_value = []
        mock_git.return_value = [
            Event(
                timestamp=datetime(2024, 6, 1, 11, 0),
                duration_seconds=36000,  # 10h
                source="git",
                category="code",
                subcategory=None,
                title="feat: x",
                url_or_path="/r",
            ),
        ]

        html_path = generate_report(
            period="weekly",
            output_dir=output_dir,
            open_browser=False,
        )

        content = html_path.read_text(encoding="utf-8")
        # 应该有代码机器人人格
        assert "代码机器人" in content
        # 应该有洞察文案
        assert "投入最多" in content
