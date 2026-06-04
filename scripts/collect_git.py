"""
Git 活动采集 - 解析 git log 输出
"""
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

sys.path.insert(0, str(Path(__file__).parent))

from models import Event


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

    # 构建 git log 命令
    cmd = [
        "git", "-C", str(repo_path),
        "log",
        "--pretty=format:%H|%an|%ai|%s",
        "--no-merges",
    ]

    if since:
        # 转为 naive datetime（git log 接受 ISO 格式）
        since_str = since.replace(tzinfo=None).isoformat()
        cmd.append(f"--since={since_str}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []

    commits = parse_git_log_output(result.stdout)

    events = []
    for commit in commits:
        try:
            # git date format: "2024-06-01 10:00:00 +0800"
            ts = datetime.fromisoformat(commit["timestamp"])
        except ValueError:
            continue

        category = classify_commit(commit["message"])

        # 时长估算：每个 commit 算 30 分钟
        # 周末 commit 算 1 小时（强度更高）
        is_weekend = ts.weekday() >= 5
        duration_sec = 3600 if is_weekend else 1800

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
