import pytest
from datetime import datetime
from digital_nutrition.models import Event, Category


def test_event_creation():
    """测试 Event 基础创建"""
    event = Event(
        timestamp=datetime(2024, 6, 1, 10, 0),
        duration_seconds=300,
        source="browser",
        category="learning",
        subcategory=None,
        title="Test page",
        url_or_path="https://github.com",
    )
    assert event.source == "browser"
    assert event.category == "learning"


def test_event_to_dict():
    """测试 Event 序列化为字典"""
    event = Event(
        timestamp=datetime(2024, 6, 1, 10, 0),
        duration_seconds=300,
        source="browser",
        category="learning",
        subcategory=None,
        title="Test",
        url_or_path="https://github.com",
    )
    d = event.to_dict()
    assert d["source"] == "browser"
    assert d["duration_seconds"] == 300
    assert d["timestamp"] == "2024-06-01T10:00:00"


def test_category_enum():
    """测试 Category 枚举值"""
    assert Category.NEWS.value == "news"
    assert Category.LEARNING.value == "learning"
    assert Category.CODE.value == "code"
    assert Category.ENTERTAINMENT.value == "entertainment"
    assert Category.WORK.value == "work"
    assert Category.SOCIAL.value == "social"
    assert Category.SHOPPING.value == "shopping"
    assert Category.OTHER.value == "other"
