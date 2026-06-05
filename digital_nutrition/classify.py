"""
域名分类引擎 - 将 URL 分类到预定义类别
"""
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Set
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


def load_ignored_domains() -> Set[str]:
    """从 user_rules.json 加载 ignored_domains（v0.6.0 review Phase 4 #9）

    用途：隐私场景下不想被报告记录的域名（如银行、内部工具等）。
    返回小写集合；文件不存在或字段缺失时返回空集。
    """
    user = load_user_rules()
    raw = user.get("ignored_domains", [])
    if not isinstance(raw, list):
        return set()
    return {str(d).strip().lower() for d in raw if str(d).strip()}


def is_domain_ignored(url: str, ignored_domains: Set[str]) -> bool:
    """判断 URL 是否在忽略列表（最长后缀优先，借鉴 classify_url）"""
    if not ignored_domains:
        return False
    host = extract_host(url).lower()
    if not host:
        return False
    # 按域名长度倒序，避免短后缀误命中
    for domain in sorted(ignored_domains, key=len, reverse=True):
        if host == domain or host.endswith("." + domain):
            return True
    return False


def merge_rules(default: Dict[str, list], user: Dict[str, list]) -> Dict[str, list]:
    """合并用户规则和默认规则（用户规则覆盖默认）"""
    merged = {k: list(v) for k, v in default.items()}
    for category, domains in user.items():
        if category in merged:
            merged[category] = list(set(merged[category] + domains))
        else:
            merged[category] = list(domains)
    return merged


# init 子命令用的模板：示例自定义规则，用户可基于此扩展
INIT_RULES_TEMPLATE = {
    "_comment": "数字营养标签 - 自定义配置。在下方添加你想归类的域名（不带协议、www. 前缀），或在 ignored_domains 列出不想被记录的域名（如银行、内部工具）。下次 weekly/daily 会自动应用。",
    "learning": [
        "my-tech-blog.com",
        "internal-wiki.mycompany.com",
    ],
    "work": [
        "jira.mycompany.com",
        "confluence.mycompany.com",
    ],
    "entertainment": [
        "twitch.tv",
        "tiktok.com",
    ],
    "ignored_domains": [
        "example-bank.com",
        "internal-hr.mycompany.com",
    ],
    "_tips": [
        "支持 8 个类别: code / learning / work / entertainment / news / social / shopping / other",
        "改完保存后，下次 `digital-nutrition weekly` 自动应用",
        "ignored_domains：列出不想被报告记录的域名（最常用于隐私场景）",
    ],
}


def init_user_rules(force: bool = False) -> tuple:
    """
    在用户配置目录创建 user_rules.json 模板。

    Returns:
        (path, created) 元组
        - path: 写入的文件路径
        - created: True=新建, False=已存在（未覆盖除非 force=True）
    """
    path = get_user_rules_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists() and not force:
        return path, False

    with open(path, "w", encoding="utf-8") as f:
        json.dump(INIT_RULES_TEMPLATE, f, ensure_ascii=False, indent=2)
    return path, True


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
