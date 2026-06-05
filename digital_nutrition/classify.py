"""
域名分类引擎 - 将 URL 分类到预定义类别
"""
import json
import os
import re
from pathlib import Path
from typing import Dict
from urllib.parse import urlparse


# 内置规则文件路径
DEFAULT_RULES_PATH = Path(__file__).parent.parent / "data" / "domain_rules.json"


def get_user_rules_path() -> Path:
    """跨平台获取用户规则文件路径"""
    if os.name == "nt":  # Windows
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:  # macOS / Linux
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "digital-nutrition" / "user_rules.json"


def load_default_rules() -> Dict[str, list]:
    """加载内置域名规则"""
    with open(DEFAULT_RULES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_user_rules() -> Dict[str, list]:
    """加载用户自定义规则（如不存在则返回空字典）"""
    path = get_user_rules_path()
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def merge_rules(default: Dict[str, list], user: Dict[str, list]) -> Dict[str, list]:
    """合并用户规则和默认规则（用户规则覆盖默认）"""
    merged = {k: list(v) for k, v in default.items()}
    for category, domains in user.items():
        if category in merged:
            merged[category] = list(set(merged[category] + domains))
        else:
            merged[category] = list(domains)
    return merged


def extract_host(url: str) -> str:
    """从 URL 提取 host，去掉 www. 前缀和端口号"""
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    parsed = urlparse(url)
    host = parsed.netloc
    if host.startswith("www."):
        host = host[4:]
    # 去掉端口号
    host = re.split(r":\d+$", host)[0]
    return host


def classify_url(url: str, rules: Dict[str, list]) -> str:
    """
    将 URL 分类到预定义类别。
    使用最长后缀优先匹配策略，避免子域名误匹配。
    """
    host = extract_host(url)

    # 收集所有 (域名长度, 类别, 域名) 三元组并按长度倒序排列
    candidates = []
    for category, domains in rules.items():
        for domain in domains:
            candidates.append((len(domain), category, domain))
    candidates.sort(key=lambda x: x[0], reverse=True)

    # 最长后缀优先匹配
    for _, category, domain in candidates:
        if host == domain or host.endswith("." + domain):
            return category

    return "other"
