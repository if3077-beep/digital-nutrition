import pytest
from scripts.persona import classify_persona, PERSONAS


def test_classify_code_robot():
    """code 占比 > 50% → 代码机器人"""
    by_category = {"code": 6000, "learning": 2000, "work": 2000}
    assert classify_persona(by_category) == "🧱 代码机器人"


def test_classify_learning_machine():
    """learning > 40% → 学习永动机"""
    by_category = {"code": 1000, "learning": 5000, "work": 1000}
    assert classify_persona(by_category) == "📚 学习永动机"


def test_classify_entertainment_king():
    """entertainment > 30% → 娱乐至上"""
    by_category = {"code": 1000, "entertainment": 4000, "work": 1000}
    assert classify_persona(by_category) == "🎬 娱乐至上"


def test_classify_news_anxious():
    """news > 40% → 资讯焦虑"""
    by_category = {"news": 5000, "code": 1000, "work": 1000}
    assert classify_persona(by_category) == "📰 资讯焦虑"


def test_classify_observer():
    """social > 30% → 观察者"""
    by_category = {"social": 4000, "code": 1000, "work": 1000}
    assert classify_persona(by_category) == "🔍 观察者"


def test_classify_balanced():
    """code/learning/work 各 15-30% → 平衡大师"""
    by_category = {
        "code": 2000,
        "learning": 2000,
        "work": 2000,
        "entertainment": 1000,
    }
    assert classify_persona(by_category) == "⚖️ 平衡大师"


def test_classify_misc():
    """以上都不满足 → 多元探索者"""
    by_category = {"code": 1000, "shopping": 2000, "other": 1000}
    assert classify_persona(by_category) == "🌐 多元探索者"


def test_classify_empty():
    """空数据 → 数据不足"""
    assert classify_persona({}) == "❓ 数据不足"


def test_personas_dict_complete():
    """PERSONAS 字典包含所有描述"""
    expected_keys = ["🧱 代码机器人", "📚 学习永动机", "🎬 娱乐至上",
                     "📰 资讯焦虑", "🔍 观察者", "⚖️ 平衡大师", "🌐 多元探索者",
                     "❓ 数据不足"]
    for key in expected_keys:
        assert key in PERSONAS
        assert "description" in PERSONAS[key]


def test_classify_priority_code_beats_learning():
    """code 优先级高于 learning（code 严格 > 50%）"""
    # code 占 60%，learning 占 35%（< 40%），应该是代码机器人
    by_category = {"code": 6000, "learning": 3500, "work": 500}
    assert classify_persona(by_category) == "🧱 代码机器人"


def test_classify_balanced_just_outside_range():
    """平衡大师范围外的情况"""
    # code 占 35%，超出 15-30% 范围，不算平衡大师
    by_category = {
        "code": 3500,
        "learning": 2000,
        "work": 2000,
        "other": 500,
    }
    assert classify_persona(by_category) == "🌐 多元探索者"
