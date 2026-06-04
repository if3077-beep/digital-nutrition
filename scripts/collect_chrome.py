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


# WebKit 时间戳基准（1601-01-01 到 1970-01-01 的秒数）
WEBKIT_EPOCH_SECONDS = 11644473600


def _webkit_to_datetime(webkit_us: int) -> datetime:
    """将 WebKit 微秒时间戳转为 datetime（带时区）"""
    timestamp_sec = webkit_us / 1_000_000 - WEBKIT_EPOCH_SECONDS
    return datetime.fromtimestamp(timestamp_sec, tz=timezone.utc)


def read_chrome_history(db_path: Path, since: Optional[datetime] = None) -> List[Event]:
    """
    从 Chrome History 数据库读取访问记录。

    Args:
        db_path: History 数据库路径
        since: 只读取此时间之后的记录

    Returns:
        Event 列表（未分类，category="other"）
    """
    if not db_path.exists():
        return []

    # 复制数据库到临时文件以避免文件锁问题
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = Path(tmp.name)
        shutil.copy(db_path, tmp_path)

    try:
        conn = sqlite3.connect(tmp_path)
        cur = conn.cursor()

        # 构建 WHERE 子句
        where = ""
        params = []
        if since:
            # 转为 WebKit 微秒
            webkit_since = int((since.timestamp() + WEBKIT_EPOCH_SECONDS) * 1_000_000)
            where = "WHERE visits.visit_time > ?"
            params = [webkit_since]

        query = f"""
            SELECT
                urls.url,
                urls.title,
                visits.visit_time,
                visits.visit_duration
            FROM visits
            JOIN urls ON visits.url = urls.id
            {where}
            ORDER BY visits.visit_time DESC
        """

        cur.execute(query, params)
        rows = cur.fetchall()
        conn.close()

        events = []
        for url, title, visit_time_us, duration_us in rows:
            # duration_us 可能为 None 或 0
            duration_sec = int((duration_us or 0) / 1_000_000)
            events.append(Event(
                timestamp=_webkit_to_datetime(visit_time_us),
                duration_seconds=duration_sec,
                source="browser",
                category="other",  # 待分类
                subcategory=None,
                title=title or "",
                url_or_path=url,
            ))

        return events
    finally:
        # 清理临时文件
        try:
            tmp_path.unlink()
        except OSError:
            pass
