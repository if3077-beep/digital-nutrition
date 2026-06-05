"""
Git 活动采集 - 解析 git log 输出
"""
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from digital_nutrition.models import Event
from digital_nutrition.sources.base import Source


# Commit message 前缀到类别的映射
COMMIT_PREFIX_MAP = {
    "feat": "code",
    "feature": "code",
    "fix": "code",
    "bugfix": "code",
    "refactor": "code",
    "perf": "code",
    "test": "code",
    "docs": "learning",
    "documentation": "learning",
    "chore": "work",
    "build": "work",
    "ci": "work",
    "style": "code",
}


# v0.5.8 新增：commit diff 行数 → 时长映射
# 比硬编码 30/60 min 准一个数量级（review 建议方案 1）
def _estimate_duration_from_diff(insertions: int, deletions: int) -> int:
    """
    根据 commit 改动的行数估算编码时长（秒）。

    启发式：
      - < 10 lines  → 10 min（小幅修改/typo）
      - 10-100 lines → 30 min（正常功能）
      - > 100 lines → 60 min（大功能/refactor）
      - 周末 commit 会被额外加成（在 read_git_activity 里）
    """
    total = insertions + deletions
    if total < 10:
        return 10 * 60
    elif total <= 100:
        return 30 * 60
    else:
        return 60 * 60


def find_git_repos(base_dir: Path) -> List[Path]:
    """查找目录下的所有 git 仓库"""
    if not base_dir.exists():
        return []
    repos = []
    for git_dir in base_dir.rglob(".git"):
        if git_dir.is_dir():
            repos.append(git_dir.parent)
    return repos


def parse_git_log_output(output: str) -> List[dict]:
    """
    解析 git log 输出（自定义格式：hash|author|date|message）。
    """
    if not output.strip():
        return []

    commits = []
    for line in output.split("\n"):
        if not line.strip():
            continue
        # 自定义格式：hash|author|date|message
        parts = line.split("|", 3)
        if len(parts) < 4:
            continue
        hash_, author, date_str, message = parts
        commits.append({
            "hash": hash_,
            "author": author,
            "timestamp": date_str.strip(),
            "message": message.strip(),
        })
    return commits


def parse_git_shortstat(output: str) -> dict:
    """
    解析 `git log --shortstat` 输出，返回 {hash: (insertions, deletions)}。

    输出格式：
        HASHSTAT:abc123
         1 file changed, 5 insertions(+), 2 deletions(-)

        HASHSTAT:def456
         3 files changed, 50 insertions(+), 10 deletions(-)
    """
    result = {}
    if not output.strip():
        return result

    # 匹配 HASHSTAT 行后跟随的 shortstat 行
    pattern = re.compile(
        r"HASHSTAT:(\w+)\s*\n\s*(\d+)\s+files?\s+changed"
        r"(?:,\s+(\d+)\s+insertions?\(\+\))?"
        r"(?:,\s+(\d+)\s+deletions?\(-\))?"
    )
    for match in pattern.finditer(output):
        hash_ = match.group(1)
        ins = int(match.group(3)) if match.group(3) else 0
        dele = int(match.group(4)) if match.group(4) else 0
        result[hash_] = (ins, dele)
    return result


def classify_commit(message: str) -> str:
    """
    根据 commit message 推断类别。
    规则：检查消息前缀（支持 `type:` 和 `type(scope):` 两种格式）。
    """
    msg = message.strip().lower()

    # 匹配 conventional commits 前缀
    match = re.match(r"^(\w+)(?:\([^)]+\))?\s*:?\s*", msg)
    if match:
        prefix = match.group(1)
        if prefix in COMMIT_PREFIX_MAP:
            return COMMIT_PREFIX_MAP[prefix]

    # 关键词兜底
    if "doc" in msg or "readme" in msg:
        return "learning"
    if "build" in msg or "ci" in msg or "deploy" in msg:
        return "work"
    if "test" in msg:
        return "code"

    # 默认归为 code（写代码）
    return "code"


def read_git_activity(repo_path: Path, since: Optional[datetime] = None) -> List[Event]:
    """
    从 git 仓库读取 commit 活动。

    Args:
        repo_path: .git 目录的父目录
        since: 只读取此时间之后的 commit

    Returns:
        Event 列表
    """
    if not (repo_path / ".git").exists():
        return []

    # 构建 git log 命令：基本信息
    base_cmd = [
        "git", "-C", str(repo_path),
        "log",
        "--pretty=format:%H|%an|%ai|%s",
        "--no-merges",
    ]
    if since:
        since_str = since.replace(tzinfo=None).isoformat()
        base_cmd.append(f"--since={since_str}")

    try:
        # 1) 拿基本信息
        result_info = subprocess.run(
            base_cmd, capture_output=True, text=True, check=True, encoding="utf-8",
        )
        # 2) 拿 shortstat（用 HASHSTAT 前缀标识每个 commit 的 hash）
        result_stat = subprocess.run(
            base_cmd + ["--shortstat", "--pretty=format:HASHSTAT:%H"],
            capture_output=True, text=True, check=True, encoding="utf-8",
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []

    commits = parse_git_log_output(result_info.stdout)
    diff_stats = parse_git_shortstat(result_stat.stdout)

    events = []
    for commit in commits:
        try:
            # git date format: "2024-06-01 10:00:00 +0800"
            ts = datetime.fromisoformat(commit["timestamp"])
        except ValueError:
            continue

        category = classify_commit(commit["message"])

        # v0.5.8：用 diff 行数估算时长（取代硬编码 30/60 min）
        ins, dele = diff_stats.get(commit["hash"], (0, 0))
        duration_sec = _estimate_duration_from_diff(ins, dele)

        events.append(Event(
            timestamp=ts,
            duration_seconds=duration_sec,
            source="git",
            category=category,
            subcategory=None,
            title=commit["message"],
            url_or_path=str(repo_path),
        ))

    return events


class GitSource(Source):
    """Git 仓库 commit 数据源

    实现 Source 协议。init 时指定 repo_path（默认 cwd）。
    """
    name = "git"

    def __init__(self, repo_dir: Optional[Path] = None):
        self.repo_dir = Path(repo_dir) if repo_dir else Path.cwd()

    def is_available(self) -> bool:
        return (self.repo_dir / ".git").exists()

    def collect(self, since: Optional[datetime] = None) -> List[Event]:
        return read_git_activity(self.repo_dir, since=since)
