"""
HTML 报告生成器 - Jinja2 渲染 + 数据格式化
"""
import json
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional

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


def build_daily_chart(daily_aggregates: Dict[str, Dict[str, int]]):
    """
    构建每日趋势图数据（ECharts 堆叠柱状图）。
    返回 (dates_json, series_json) 元组。
    """
    if not daily_aggregates:
        return None, None
    dates = sorted(daily_aggregates.keys())
    # 按总时长排序类别
    all_cats = set()
    for d in daily_aggregates.values():
        all_cats.update(d.keys())
    cat_order = sorted(
        all_cats,
        key=lambda c: -sum(
            daily_aggregates.get(date, {}).get(c, 0) for date in dates
        ),
    )
    series = []
    for cat in cat_order:
        meta = CATEGORY_META.get(cat, {})
        series.append({
            "name": meta.get("name", cat),
            "type": "bar",
            "stack": "total",
            "itemStyle": {"color": meta.get("color", "#9ca3af")},
            "data": [
                int(daily_aggregates.get(date, {}).get(cat, 0) / 60)
                for date in dates
            ],
        })
    return json.dumps(dates, ensure_ascii=False), json.dumps(series, ensure_ascii=False)


def render_report(
    report_data: Dict,
    persona: str,
    insights: List[str],
    output_dir: Path,
    daily_aggregates: Optional[Dict[str, Dict[str, int]]] = None,
) -> Path:
    """
    渲染完整 HTML 报告。

    Args:
        report_data: 来自 analyze.build_report_data 的数据
        persona: 人格名称
        insights: 洞察列表
        output_dir: 输出目录
        daily_aggregates: 每日聚合数据（v0.2 新增）

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
    daily_chart_dates, daily_chart_data = build_daily_chart(daily_aggregates or {})

    html = template.render(
        period_start=report_data["period_start"][:10],
        period_end=report_data["period_end"][:10],
        total_human=format_duration(report_data["total_seconds"]),
        persona=persona,
        persona_description=persona_desc,
        chart_data=json.dumps(chart_data, ensure_ascii=False),
        category_details=category_details,
        insights=insights,
        daily_chart_data=daily_chart_data,
        daily_chart_dates=daily_chart_dates,
    )

    output_file = output_dir / "report.html"
    output_file.write_text(html, encoding="utf-8")
    return output_file
