"""
下载 ECharts JS 文件到本地 assets 目录。
仅在开发/打包时运行一次。
"""
import urllib.request
from pathlib import Path

ASSETS_DIR = Path(__file__).parent.parent / "assets"
ECHARTS_URL = "https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"
ECHARTS_FILE = ASSETS_DIR / "echarts.min.js"


def fetch():
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    if ECHARTS_FILE.exists():
        print(f"Already exists: {ECHARTS_FILE}")
        return
    print(f"Downloading ECharts from {ECHARTS_URL}...")
    urllib.request.urlretrieve(ECHARTS_URL, ECHARTS_FILE)
    size_kb = ECHARTS_FILE.stat().st_size / 1024
    print(f"Downloaded: {ECHARTS_FILE} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    fetch()
