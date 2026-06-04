"""
数据模型定义 - 统一事件结构
"""
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Optional, Literal


class Category(str, Enum):
    """类别枚举"""
    NEWS = "news"
    LEARNING = "learning"
    WORK = "work"
    CODE = "code"
    SOCIAL = "social"
    ENTERTAINMENT = "entertainment"
    SHOPPING = "shopping"
    OTHER = "other"


@dataclass
class Event:
    """统一事件结构 - 所有数据源最终转换为此结构"""
    timestamp: datetime
    duration_seconds: int
    source: Literal["browser", "git"]
    category: str
    subcategory: Optional[str]
    title: str
    url_or_path: str

    def to_dict(self) -> dict:
        """序列化为字典"""
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        return d


# 类别元数据：颜色和显示名称
CATEGORY_META = {
    Category.NEWS.value: {"name": "资讯/八卦", "color": "#fbbf24", "icon": "📰"},
    Category.LEARNING.value: {"name": "技术学习", "color": "#34d399", "icon": "📚"},
    Category.WORK.value: {"name": "工作/邮件", "color": "#60a5fa", "icon": "💼"},
    Category.CODE.value: {"name": "写代码", "color": "#3b82f6", "icon": "💻"},
    Category.SOCIAL.value: {"name": "社交", "color": "#a78bfa", "icon": "💬"},
    Category.ENTERTAINMENT.value: {"name": "娱乐", "color": "#f87171", "icon": "🎬"},
    Category.SHOPPING.value: {"name": "购物", "color": "#c084fc", "icon": "🛒"},
    Category.OTHER.value: {"name": "其他", "color": "#9ca3af", "icon": "❓"},
}
