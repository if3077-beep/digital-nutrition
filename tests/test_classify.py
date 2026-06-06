import json
import pytest
from digital_nutrition.classify import (
    add_user_rule,
    extract_host,
    classify_url,
    init_user_rules,
    is_domain_ignored,
    list_user_rules,
    load_default_rules,
    load_ignored_domains,
    load_user_rules,
    merge_rules,
    remove_user_rule,
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


# ===== v0.5.x init_user_rules =====

def test_init_user_rules_creates_template(tmp_path, monkeypatch):
    """init_user_rules 应在指定目录创建模板"""
    monkeypatch.setattr(
        "digital_nutrition.classify.get_user_rules_path",
        lambda: tmp_path / "user_rules.json",
    )
    path, created = init_user_rules(force=False)
    assert created is True
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "learning" in data
    assert "work" in data
    assert "entertainment" in data


def test_init_user_rules_respects_existing(tmp_path, monkeypatch):
    """已存在时不应覆盖（除非 force=True）"""
    target = tmp_path / "user_rules.json"
    target.write_text('{"existing": true}', encoding="utf-8")
    monkeypatch.setattr(
        "digital_nutrition.classify.get_user_rules_path",
        lambda: target,
    )
    path, created = init_user_rules(force=False)
    assert created is False
    assert json.loads(path.read_text(encoding="utf-8")) == {"existing": True}

    # force=True 应覆盖
    path2, created2 = init_user_rules(force=True)
    assert created2 is True
    data = json.loads(path2.read_text(encoding="utf-8"))
    assert "learning" in data


def test_init_user_rules_creates_parent_dir(tmp_path, monkeypatch):
    """父目录不存在时应自动创建"""
    target = tmp_path / "nested" / "user_rules.json"
    monkeypatch.setattr(
        "digital_nutrition.classify.get_user_rules_path",
        lambda: target,
    )
    path, created = init_user_rules(force=False)
    assert created is True
    assert path.parent.exists()


# ===== v0.6.0 ignored_domains 隐私列表（review Phase 4 #9） =====

def test_load_ignored_domains_empty_when_no_file(tmp_path, monkeypatch):
    """user_rules.json 不存在时应返回空集"""
    monkeypatch.setattr(
        "digital_nutrition.classify.get_user_rules_path",
        lambda: tmp_path / "user_rules.json",
    )
    assert load_ignored_domains() == set()


def test_load_ignored_domains_reads_field(tmp_path, monkeypatch):
    """应从 user_rules.json 读 ignored_domains 字段并转小写"""
    target = tmp_path / "user_rules.json"
    target.write_text(json.dumps({
        "learning": ["foo.com"],
        "ignored_domains": ["Bank.example.com", "internal-hr.MyCompany.com", ""],
    }), encoding="utf-8")
    monkeypatch.setattr(
        "digital_nutrition.classify.get_user_rules_path",
        lambda: target,
    )
    result = load_ignored_domains()
    # 全部小写、空字符串被过滤
    assert result == {"bank.example.com", "internal-hr.mycompany.com"}


def test_load_ignored_domains_handles_malformed(tmp_path, monkeypatch):
    """ignored_domains 不是 list 时返回空集（不抛异常）"""
    target = tmp_path / "user_rules.json"
    target.write_text(json.dumps({"ignored_domains": "not a list"}), encoding="utf-8")
    monkeypatch.setattr(
        "digital_nutrition.classify.get_user_rules_path",
        lambda: target,
    )
    assert load_ignored_domains() == set()


def test_is_domain_ignored_basic():
    """完全匹配应命中"""
    assert is_domain_ignored("https://bank.com/accounts", {"bank.com"}) is True
    # 子域名后缀命中
    assert is_domain_ignored("https://www.bank.com/", {"bank.com"}) is True
    # 不同域名不命中
    assert is_domain_ignored("https://other.com/", {"bank.com"}) is False


def test_is_domain_ignored_empty_set():
    """空集合应始终返回 False（避免不必要的解析）"""
    assert is_domain_ignored("https://bank.com/", set()) is False


def test_is_domain_ignored_longest_suffix_first():
    """最长后缀优先（避免被短后缀吃掉）"""
    # bank.com 应该优先于 com
    assert is_domain_ignored(
        "https://bank.com/", {"com", "bank.com"}
    ) is True
    # github.io 应该优先于 io
    assert is_domain_ignored(
        "https://x.github.io/", {"io", "github.io"}
    ) is True


def test_init_user_rules_template_includes_ignored_domains(tmp_path, monkeypatch):
    """init 创建的模板应包含 ignored_domains 字段（引导用户发现）"""
    target = tmp_path / "user_rules.json"
    monkeypatch.setattr(
        "digital_nutrition.classify.get_user_rules_path",
        lambda: target,
    )
    path, created = init_user_rules(force=False)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "ignored_domains" in data
    assert isinstance(data["ignored_domains"], list)


# ===== v0.7.0 rules CLI：classify.py +3 helper（任务 2） =====

def test_add_user_rule_to_empty_file(tmp_path, monkeypatch):
    """空文件 → 创建新类别并添加"""
    target = tmp_path / "user_rules.json"
    monkeypatch.setattr(
        "digital_nutrition.classify.get_user_rules_path",
        lambda: target,
    )
    add_user_rule("bilibili.com", "entertainment")
    data = json.loads(target.read_text(encoding="utf-8"))
    assert data == {"entertainment": ["bilibili.com"]}


def test_add_user_rule_appends_to_existing_category(tmp_path, monkeypatch):
    """已存在类别 → 追加 domain"""
    target = tmp_path / "user_rules.json"
    target.write_text(json.dumps({"entertainment": ["twitch.tv"]}), encoding="utf-8")
    monkeypatch.setattr(
        "digital_nutrition.classify.get_user_rules_path",
        lambda: target,
    )
    add_user_rule("bilibili.com", "entertainment")
    data = json.loads(target.read_text(encoding="utf-8"))
    assert "bilibili.com" in data["entertainment"]
    assert "twitch.tv" in data["entertainment"]


def test_add_user_rule_creates_new_category(tmp_path, monkeypatch):
    """不存在的类别 → 创建新类别"""
    target = tmp_path / "user_rules.json"
    target.write_text(json.dumps({"learning": ["foo.com"]}), encoding="utf-8")
    monkeypatch.setattr(
        "digital_nutrition.classify.get_user_rules_path",
        lambda: target,
    )
    add_user_rule("internal-hr.com", "work")
    data = json.loads(target.read_text(encoding="utf-8"))
    assert data["learning"] == ["foo.com"]
    assert data["work"] == ["internal-hr.com"]


def test_add_user_rule_rejects_duplicate_domain(tmp_path, monkeypatch):
    """v3 决策：重复 domain 拒绝（抛 ValueError），避免误覆盖"""
    target = tmp_path / "user_rules.json"
    target.write_text(json.dumps({"entertainment": ["bilibili.com"]}), encoding="utf-8")
    monkeypatch.setattr(
        "digital_nutrition.classify.get_user_rules_path",
        lambda: target,
    )
    with pytest.raises(ValueError, match="bilibili.com"):
        add_user_rule("bilibili.com", "work")  # 重复 domain


def test_add_user_rule_rejects_duplicate_across_categories(tmp_path, monkeypatch):
    """重复 domain 即使在不同类别也应拒绝（一个域名只属于一个类别）"""
    target = tmp_path / "user_rules.json"
    target.write_text(json.dumps({"learning": ["foo.com"]}), encoding="utf-8")
    monkeypatch.setattr(
        "digital_nutrition.classify.get_user_rules_path",
        lambda: target,
    )
    with pytest.raises(ValueError, match="foo.com"):
        add_user_rule("foo.com", "work")


def test_add_user_rule_creates_parent_dir(tmp_path, monkeypatch):
    """父目录不存在时应自动创建"""
    target = tmp_path / "nested" / "user_rules.json"
    monkeypatch.setattr(
        "digital_nutrition.classify.get_user_rules_path",
        lambda: target,
    )
    add_user_rule("x.com", "other")
    assert target.exists()


def test_remove_user_rule_returns_true_when_removed(tmp_path, monkeypatch):
    """已存在的 domain → 返回 True"""
    target = tmp_path / "user_rules.json"
    target.write_text(json.dumps({"entertainment": ["bilibili.com", "twitch.tv"]}), encoding="utf-8")
    monkeypatch.setattr(
        "digital_nutrition.classify.get_user_rules_path",
        lambda: target,
    )
    assert remove_user_rule("bilibili.com") is True
    data = json.loads(target.read_text(encoding="utf-8"))
    assert "bilibili.com" not in data["entertainment"]
    assert "twitch.tv" in data["entertainment"]


def test_remove_user_rule_returns_false_when_not_found(tmp_path, monkeypatch):
    """不存在的 domain → 返回 False，文件不动"""
    target = tmp_path / "user_rules.json"
    original = {"entertainment": ["twitch.tv"]}
    target.write_text(json.dumps(original), encoding="utf-8")
    monkeypatch.setattr(
        "digital_nutrition.classify.get_user_rules_path",
        lambda: target,
    )
    assert remove_user_rule("nonexistent.com") is False
    data = json.loads(target.read_text(encoding="utf-8"))
    assert data == original  # 文件未变


def test_remove_user_rule_removes_empty_category(tmp_path, monkeypatch):
    """删除最后一个 domain 后，类别键应一并删除（保持整洁）"""
    target = tmp_path / "user_rules.json"
    target.write_text(json.dumps({"entertainment": ["bilibili.com"]}), encoding="utf-8")
    monkeypatch.setattr(
        "digital_nutrition.classify.get_user_rules_path",
        lambda: target,
    )
    remove_user_rule("bilibili.com")
    data = json.loads(target.read_text(encoding="utf-8"))
    assert "entertainment" not in data  # 空类别应删除


def test_list_user_rules_empty_when_no_file(tmp_path, monkeypatch):
    """文件不存在时返回空 dict"""
    target = tmp_path / "user_rules.json"
    monkeypatch.setattr(
        "digital_nutrition.classify.get_user_rules_path",
        lambda: target,
    )
    assert list_user_rules() == {}


def test_list_user_rules_returns_dict(tmp_path, monkeypatch):
    """文件存在时返回 dict（不合并默认）"""
    target = tmp_path / "user_rules.json"
    target.write_text(
        json.dumps({"learning": ["foo.com"], "work": ["bar.com"]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "digital_nutrition.classify.get_user_rules_path",
        lambda: target,
    )
    result = list_user_rules()
    assert result == {"learning": ["foo.com"], "work": ["bar.com"]}
