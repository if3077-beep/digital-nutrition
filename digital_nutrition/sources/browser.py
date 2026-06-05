"""
浏览器历史数据源 - 包装 browser-history 库（Chrome/Edge/Firefox/Safari/Arc/Zen/Brave 等）
"""
from collections import defaultdict
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

from ..models import Event
from ..sources.base import Source


# 时长估算常量（v0.5.8 新增）
# 同域名相邻 visit 时间差作为停留时长，但截断到 MAX，避免后台标签页造成的虚高
MAX_BROWSER_DURATION_SEC = 30 * 60  # 30 分钟上限
MIN_BROWSER_DURATION_SEC = 5         # 5 秒下限（避免 0 噪音）


def _domain_of(url: str) -> str:
    """提取 URL 域名（同源判定用）"""
    try:
        netloc = urlparse(url).netloc.lower()
        # 去掉 www. 前缀
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc
    except (ValueError, AttributeError):
        return ""


def estimate_durations(visits: list, max_sec: int = MAX_BROWSER_DURATION_SEC) -> list:
    """
    用"同域名相邻 visit 时间差"作为停留时长（启发式估算）。

    算法：
      1. 按域名分组
      2. 每组内按 timestamp 升序排序
      3. 相邻 visit 的时间差 ≈ 在前一个页面的停留时长
      4. 截断到 [MIN, MAX] 区间

    Args:
        visits: list of (dt, url, title) tuples
        max_sec: 单次访问时长上限

    Returns:
        同长度的 list of (dt, url, title, duration_sec)
    """
    if not visits:
        return []

    # 1) 按域名分组
    by_domain: dict = defaultdict(list)
    for entry in visits:
        try:
            dt = entry[0]
            url = entry[1] if len(entry) > 1 else ""
        except (IndexError, TypeError):
            continue
        if not url:
            continue
        domain = _domain_of(url)
        if not domain:
            continue
        by_domain[domain].append((dt, url, entry))

    # 2) 每组按时间升序
    for domain in by_domain:
        by_domain[domain].sort(key=lambda x: x[0])

    # 3) 计算每个 visit 的 duration = min(到下一个 visit 的时间差, MAX)
    durations = {}  # id(entry) -> duration_sec
    for domain, items in by_domain.items():
        for i in range(len(items) - 1):
            dt_curr = items[i][0]
            dt_next = items[i + 1][0]
            gap = (dt_next - dt_curr).total_seconds()
            # 截断到 [MIN, MAX]
            duration = max(MIN_BROWSER_DURATION_SEC, min(int(gap), max_sec))
            durations[id(items[i][2])] = duration
        # 最后一笔：给一个默认 30 秒（用户离开时停留未知）
        durations[id(items[-1][2])] = 30

    # 4) 组装结果
    result = []
    for entry in visits:
        try:
            dt = entry[0]
            url = entry[1] if len(entry) > 1 else ""
            title = entry[2] if len(entry) > 2 else ""
        except (IndexError, TypeError):
            continue
        if not url:
            continue
        dur = durations.get(id(entry), 30)
        result.append((dt, url, title, dur))
    return result


class BrowserSource(Source):
    """通用浏览器历史数据源

    通过 [browser-history](https://github.com/browser-history/browser-history) 库
    自动处理 8+ 浏览器的历史读取（Chrome / Edge / Firefox / Safari / Arc / Zen / Brave / Vivaldi）。
    0 依赖、20KB。

    时长估算（v0.5.8 新增）：
      browser-history 不提供停留时长，我们用"同域名相邻 visit 时间差"启发式估算。
      单次访问时长截断到 [5s, 30min] 区间。
    """
    name = "browser"

    def is_available(self) -> bool:
        # browser-history 内部会扫描已知路径
        # 永远返回 True，让 collect() 自己处理空历史
        return True

    def collect(self, since: Optional[datetime] = None) -> list[Event]:
        from browser_history import get_history

        outputs = get_history()
        raw_visits = list(outputs.histories) if outputs.histories else []

        # v0.5.8：先估算 duration
        enriched = estimate_durations(raw_visits)

        events = []
        for dt, url, title, duration_sec in enriched:
            # 统一时区：since 通常是 tz-naive（datetime.now()），dt 是 tz-aware
            if since is not None:
                if since.tzinfo is None and dt.tzinfo is not None:
                    # 移除 dt 的 tzinfo，让 naive since 可以比较
                    dt_compare = dt.replace(tzinfo=None)
                elif since.tzinfo is not None and dt.tzinfo is None:
                    dt_compare = dt.replace(tzinfo=since.tzinfo)
                else:
                    dt_compare = dt
                if dt_compare < since:
                    continue
            events.append(Event(
                timestamp=dt,
                duration_seconds=duration_sec,  # v0.5.8：估算的停留时长
                source="browser",
                category="other",     # 待 classify.py 处理
                subcategory=None,
                title=title or "",
                url_or_path=url,
            ))
        return events
