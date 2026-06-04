"""
HTML 报告生成器 - Jinja2 渲染 + 数据格式化
"""
import json
import shutil
import sys
from pathlib import Path
from typing import Dict, List

from jinja2 import Environment, FileSystemLoader, select_autoescape

sys.path.insert(0, str(Path(__file__).parent))

from models import CATEGORY_META
from insight import format_duration
from persona import PERSONAS


TEMPLATE_DIR = Path(__file__).parent.parent / "templates"
ASSETS_DIR = Path(__file__).parent.parent / "assets"


def build_chart_data(by_category: Dict[str, int]) -> List[dict]:
    """构建 ECharts 饼图数据"""
    return [
        {
            "name": CATEGORY_META.get(cat, {}).get("name", cat),
            "value": duration,
        }
        for cat, duration in sorted(
            by_category.items(), key=lambda x: -x[1]
        )
    ]


def build_category_details(by_category: Dict[str, int]) -> List[dict]:
    """构建类别详情列表（用于卡片展示）"""
    total = sum(by_category.values()) or 1
    details = []
    for cat, duration in sorted(by_category.items(), key=lambda x: -x[1]):
        meta = CATEGORY_META.get(cat, {})
        details.append({
            "name": meta.get("name", cat),
            "color": meta.get("color", "#9ca3af"),
            "icon": meta.get("icon", "❓"),
            "duration_human": format_duration(duration),
            "pct": round(duration / total * 100, 1),
        })
    return details


def render_report(
    report_data: Dict,
    persona: str,
    insights: List[str],
    output_dir: Path,
) -> Path:
    """
    渲染完整 HTML 报告。

    Args:
        report_data: 来自 analyze.build_report_data 的数据
        persona: 人格名称
        insights: 洞察列表
        output_dir: 输出目录

    Returns:
        HTML 文件路径
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # 复制 ECharts 到输出目录
    if ASSETS_DIR.exists():
        assets_out = output_dir / "assets"
        assets_out.mkdir(exist_ok=True)
        for f in ASSETS_DIR.iterdir():
            if f.suffix == ".js":
                shutil.copy(f, assets_out / f.name)

    # 配置 Jinja2
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("report.html.j2")

    # 准备数据
    by_category = report_data["by_category"]
    chart_data = build_chart_data(by_category)
    category_details = build_category_details(by_category)
    persona_desc = PERSONAS.get(persona, {}).get("description", "")

    html = template.render(
        period_start=report_data["period_start"][:10],
        period_end=report_data["period_end"][:10],
        total_human=format_duration(report_data["total_seconds"]),
        persona=persona,
        persona_description=persona_desc,
        chart_data=json.dumps(chart_data, ensure_ascii=False),
        category_details=category_details,
        insights=insights,
    )

    output_file = output_dir / "report.html"
    output_file.write_text(html, encoding="utf-8")
    return output_file
