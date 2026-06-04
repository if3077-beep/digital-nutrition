"""
生成 Chrome History 测试 fixture
运行: python -m tests.fixtures.create_fixture
"""
import sqlite3
from datetime import datetime
from pathlib import Path

FIXTURE_PATH = Path(__file__).parent / "chrome_history_sample.db"

# WebKit 时间戳基准：1601-01-01 到 1970-01-01 的秒数
WEBKIT_EPOCH_SECONDS = 11644473600


def to_webkit(dt_str: str) -> int:
    """ISO 时间字符串转 WebKit 微秒时间戳"""
    dt = datetime.fromisoformat(dt_str)
    return int((dt.timestamp() + WEBKIT_EPOCH_SECONDS) * 1_000_000)


def create_fixture():
    if FIXTURE_PATH.exists():
        FIXTURE_PATH.unlink()

    conn = sqlite3.connect(FIXTURE_PATH)
    cur = conn.cursor()

    # Chrome schema (简化版)
    cur.execute("""
        CREATE TABLE urls (
            id INTEGER PRIMARY KEY,
            url TEXT,
            title TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE visits (
            id INTEGER PRIMARY KEY,
            url INTEGER,
            visit_time INTEGER,
            visit_duration INTEGER DEFAULT 0
        )
    """)

    sample_data = [
        # (url, title, visit_time_iso, duration_us)
        ("https://github.com/user/repo", "GitHub Repo", "2024-06-01T10:00:00", 5_000_000),
        ("https://stackoverflow.com/questions/123", "Stack Overflow Q", "2024-06-01T11:00:00", 3_000_000),
        ("https://twitter.com/home", "Twitter Home", "2024-06-01T12:00:00", 1_000_000),
        ("https://youtube.com/watch?v=abc", "YouTube Video", "2024-06-01T14:00:00", 10_000_000),
        ("https://weibo.com/123", "Weibo Post", "2024-06-01T15:00:00", 2_000_000),
        ("https://unknown-site.com/page", "Unknown", "2024-06-01T16:00:00", 1_000_000),
    ]

    for i, (url, title, dt, duration) in enumerate(sample_data, 1):
        cur.execute("INSERT INTO urls (id, url, title) VALUES (?, ?, ?)", (i, url, title))
        cur.execute(
            "INSERT INTO visits (id, url, visit_time, visit_duration) VALUES (?, ?, ?, ?)",
            (i, i, to_webkit(dt), duration)
        )

    conn.commit()
    conn.close()
    print(f"Created fixture: {FIXTURE_PATH}")


if __name__ == "__main__":
    create_fixture()
