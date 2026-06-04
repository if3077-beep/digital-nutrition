"""
Chrome 浏览器历史采集
"""
import os
import shutil
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

# 添加 scripts 目录到路径以便导入
sys.path.insert(0, str(Path(__file__).parent))

from models import Event


def get_chrome_user_data_dir() -> Path:
    """跨平台获取 Chrome User Data 目录"""
    if sys.platform == "win32":
        local = os.environ.get("LOCALAPPDATA", "")
        return Path(local) / "Google" / "Chrome" / "User Data"
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Google" / "Chrome"
    else:  # Linux
        return Path.home() / ".config" / "google-chrome"


def get_chrome_history_path(profile: str = "Default") -> Path:
    """获取 Chrome History 数据库路径"""
    return get_chrome_user_data_dir() / profile / "History"


def find_chrome_profiles() -> List[Path]:
    """查找所有 Chrome profile 目录"""
    user_data = get_chrome_user_data_dir()
    if not user_data.exists():
        return []
    profiles = []
    for item in user_data.iterdir():
        if item.is_dir() and (item / "History").exists():
            profiles.append(item)
    return profiles
