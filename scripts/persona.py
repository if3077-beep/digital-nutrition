"""
开发者人格分类器 - 基于时间分配判断开发者类型
"""
from typing import Dict


# 人格描述字典
PERSONAS = {
    "🧱 代码机器人": {
        "description": "你是一台不知疲倦的代码生成器",
        "color": "#3b82f6",
    },
    "📚 学习永动机": {
        "description": "你每天都在学习，但代码产出呢？",
        "color": "#34d399",
    },
    "🎬 娱乐至上": {
        "description": "你看的视频比写的代码多",
        "color": "#f87171",
    },
    "📰 资讯焦虑": {
        "description": "你被信息流裹挟，难以静心",
        "color": "#fbbf24",
    },
    "🔍 观察者": {
        "description": "你了解所有人的动态",
        "color": "#a78bfa",
    },
    "⚖️ 平衡大师": {
        "description": "你的时间分配堪称教科书",
        "color": "#10b981",
    },
    "🌐 多元探索者": {
        "description": "你的兴趣广泛，难以定义",
        "color": "#06b6d4",
    },
    "❓ 数据不足": {
        "description": "数据太少，无法判断",
        "color": "#9ca3af",
    },
}


def classify_persona(by_category: Dict[str, int]) -> str:
    """
    根据各类别时长分布判断开发者人格。
    返回人格名称字符串。
    """
    total = sum(by_category.values())
    if total == 0:
        return "❓ 数据不足"

    pct = {k: v / total for k, v in by_category.items()}

    # 优先级从高到低判断
    if pct.get("code", 0) > 0.5:
        return "🧱 代码机器人"
    if pct.get("learning", 0) > 0.4:
        return "📚 学习永动机"
    if pct.get("entertainment", 0) > 0.3:
        return "🎬 娱乐至上"
    if pct.get("news", 0) > 0.4:
        return "📰 资讯焦虑"
    if pct.get("social", 0) > 0.3:
        return "🔍 观察者"

    # 平衡大师：code/learning/work 各占 15-30%
    core_categories = ["code", "learning", "work"]
    if all(0.15 <= pct.get(c, 0) <= 0.3 for c in core_categories):
        return "⚖️ 平衡大师"

    return "🌐 多元探索者"
