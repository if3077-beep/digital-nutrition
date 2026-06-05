"""
浏览器历史数据源 - 包装 browser-history 库（Chrome/Edge/Firefox/Safari/Arc/Zen/Brave 等）
"""
from datetime import datetime
from typing import Optional

from ..models import Event
from ..sources.base import Source


class BrowserSource(Source):
    """通用浏览器历史数据源

    通过 [browser-history](https://github.com/browser-history/browser-history) 库
    自动处理 8+ 浏览器的历史读取（Chrome / Edge / Firefox / Safari / Arc / Zen / Brave / Vivaldi）。
    0 依赖、20KB。

    注意：browser-history 不提供 title 持续时间和 title（实际是有的，见下）；
    duration 默认为 0（待 v0.5+ 增强）。
    """
    name = "browser"

    def is_available(self) -> bool:
        # browser-history 内部会扫描已知路径
        # 永远返回 True，让 collect() 自己处理空历史
        return True

    def collect(self, since: Optional[datetime] = None) -> list[Event]:
        from browser_history import get_history

        outputs = get_history()
        events = []
        for entry in outputs.histories:
            # browser-history 0.5.0 返回 (datetime, url, title) 3-tuple
            dt, url, title = entry[0], entry[1], entry[2] if len(entry) > 2 else ""
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
                duration_seconds=0,  # browser-history 不提供
                source="browser",
                category="other",     # 待 classify.py 处理
                subcategory=None,
                title=title or "",
                url_or_path=url,
            ))
        return events
