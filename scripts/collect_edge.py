"""
Edge 浏览器历史采集
Edge 基于 Chromium，schema 与 Chrome 相同，可复用读取逻辑。
"""
import os
import sys
import shutil
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

sys.path.insert(0, str(Path(__file__).parent))

from models import Event


def get_edge_user_data_dir() -> Optional[Path]:
    """跨平台获取 Edge User Data 目录"""
    if sys.platform == "win32":
        local = os.environ.get("LOCALAPPDATA", "")
        return Path(local) / "Microsoft" / "Edge" / "User Data"
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Microsoft Edge"
    elif sys.platform.startswith("linux"):
        # Linux 上的 Edge 不常见，但支持
        candidates = [
            Path.home() / ".config" / "microsoft-edge",
            Path.home() / ".config" / "microsoft-edge-dev",
        ]
        for c in candidates:
            if c.exists():
                return c
        return candidates[0]  # 返回默认路径
    return None


def get_edge_history_path(profile: str = "Default") -> Path:
    """获取 Edge History 数据库路径"""
    return get_edge_user_data_dir() / profile / "History"


def find_edge_profiles() -> List[Path]:
    """查找所有 Edge profile 目录"""
    user_data = get_edge_user_data_dir()
    if not user_data or not user_data.exists():
        return []
    profiles = []
    for item in user_data.iterdir():
        if item.is_dir() and (item / "History").exists():
            profiles.append(item)
    return profiles


def read_edge_history(db_path: Path, since: Optional[datetime] = None) -> List[Event]:
    """
    从 Edge History 数据库读取访问记录。
    Edge schema 与 Chrome 相同，复用相同读取逻辑。
    """
    # 复用 Chrome 读取逻辑
    from collect_chrome import read_chrome_history
    return read_chrome_history(db_path, since=since)
