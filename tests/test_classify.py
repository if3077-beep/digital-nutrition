import pytest
from digital_nutrition.classify import (
    extract_host,
    classify_url,
    load_default_rules,
    load_user_rules,
    merge_rules,
)


def test_extract_host_basic():
    """测试 host 提取（只去掉 www. 前缀，子域名保留）"""
    assert extract_host("https://www.github.com/user") == "github.com"
    assert extract_host("http://stackoverflow.com/questions") == "stackoverflow.com"
    # 子域名（如 m.bilibili.com）保留，由 classify_url 处理匹配
    assert extract_host("https://m.bilibili.com/video/BV1") == "m.bilibili.com"


def test_extract_host_no_scheme():
    """测试无 scheme 的 URL"""
    assert extract_host("github.com/user") == "github.com"


def test_extract_host_with_port():
    """测试带端口的 URL"""
    assert extract_host("https://github.com:443/user") == "github.com"


def test_classify_url_known():
    """测试已知域名分类"""
    rules = load_default_rules()
    assert classify_url("https://github.com/user", rules) == "learning"
    assert classify_url("https://twitter.com/home", rules) == "social"
    assert classify_url("https://youtube.com/watch?v=1", rules) == "entertainment"
    assert classify_url("https://taobao.com/item", rules) == "shopping"


def test_classify_url_unknown():
    """测试未知域名归为 other"""
    rules = load_default_rules()
    assert classify_url("https://unknown-site.com/page", rules) == "other"


def test_classify_url_subdomain():
    """测试子域名匹配"""
    rules = load_default_rules()
    assert classify_url("https://docs.github.com/en", rules) == "learning"
    assert classify_url("https://api.twitter.com/1.1", rules) == "social"
    # m.bilibili.com 是 bilibili.com 的子域名
    assert classify_url("https://m.bilibili.com/video/BV1", rules) == "entertainment"


def test_classify_url_longest_suffix_first():
    """测试最长后缀优先匹配"""
    rules = {
        "news": ["news.com"],
        "learning": ["github.com", "github.io"],
    }
    # github.io 应该匹配 learning (更长后缀) 而非 github.com
    assert classify_url("https://username.github.io", rules) == "learning"


def test_merge_rules():
    """测试用户规则覆盖默认规则"""
    default = load_default_rules()
    user = {"learning": ["example.com"]}
    merged = merge_rules(default, user)
    assert "example.com" in merged["learning"]
    # 默认规则仍保留
    assert "github.com" in merged["learning"]


def test_load_default_rules_has_all_categories():
    """测试默认规则包含所有 6 个类别（不含 other）"""
    rules = load_default_rules()
    expected_categories = {"news", "learning", "work", "social", "entertainment", "shopping"}
    assert set(rules.keys()) == expected_categories
