"""
分享卡 metadata - 把报告数据压缩成适合社交分享的紧凑格式
PNG 分享卡在浏览器端用 canvas 绘制，metadata 注入到 window.__SHARE_CARD_DATA__
"""
from typing import Dict, List, Optional

from digital_nutrition import __version__
from digital_nutrition.insight import format_duration
from digital_nutrition.models import CATEGORY_META
from digital_nutrition.persona import PERSONAS


def get_share_card_metadata(
    report_data: Dict,
    persona: str,
    insights: List[str],
    top_n: int = 3,
) -> Dict:
    """
    把完整报告压缩成分享卡 metadata。

    Returns:
        {
            "title": "我的开发者人格",
            "persona": "🌐 多元探索者",
            "persona_color": "#06b6d4",
            "period": "2026-05-30 至 2026-06-05",
            "total_human": "12h 34m",
            "top_categories": [
                {"name": "代码", "icon": "💻", "color": "#3b82f6",
                 "duration_human": "5h 12m", "pct": 41.5},
                ...
            ],
            "highlight_insight": "代码时间比上周 +20%（洞察第一条）",
            "footer": "数字营养标签 · v0.5"
        }
    """
    by_category: Dict[str, int] = report_data.get("by_category", {})
    total = sum(by_category.values())
    total = total or 1  # 避免除零

    # Top N 类别
    top = sorted(by_category.items(), key=lambda x: -x[1])[:top_n]
    top_categories = []
    for cat, seconds in top:
        meta = CATEGORY_META.get(cat, {})
        top_categories.append({
            "name": meta.get("name", cat),
            "icon": meta.get("icon", "❓"),
            "color": meta.get("color", "#9ca3af"),
            "duration_human": format_duration(seconds),
            "pct": round(seconds / total * 100, 1),
        })

    # 取第一条 insight 作为高亮（如果太长截断到 30 字）
    highlight = ""
    if insights:
        first = insights[0]
        highlight = first if len(first) <= 30 else first[:27] + "..."

    return {
        "title": "我的开发者人格",
        "persona": persona,
        "persona_color": PERSONAS.get(persona, {}).get("color", "#9ca3af"),
        "period": f"{report_data.get('period_start', '')[:10]} 至 {report_data.get('period_end', '')[:10]}",
        "total_human": format_duration(report_data.get("total_seconds", 0)),
        "top_categories": top_categories,
        "highlight_insight": highlight,
        "footer": f"数字营养标签 · v{__version__}",
    }
