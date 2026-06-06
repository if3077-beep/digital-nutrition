"""
浏览器历史数据源 - 包装 browser-history 库（Chrome/Edge/Firefox/Safari/Arc/Zen/Brave 等）
"""
from collections import defaultdict
from datetime import datetime
from typing import List, Optional, Tuple
from urllib.parse import urlparse

from ..models import Event
from ..sources.base import Source


# 时长估算常量（v0.5.8 新增）
# 同域名相邻 visit 时间差作为停留时长，但截断到 MAX，避免后台标签页造成的虚高
MAX_BROWSER_DURATION_SEC = 30 * 60  # 30 分钟上限
MIN_BROWSER_DURATION_SEC = 5         # 5 秒下限（避免 0 噪音）


# v0.7.0 --browser 参数：浏览器名 → 库具体类名（小写）
# 库 browser-history v0.5.0 有 13 个具体类：
# Chromium / Chrome / Edge / Opera / OperaGX / Brave / Vivaldi / Epic / Arc /
# Firefox / LibreWolf / Zen / Safari
# 之前的 `ChromiumBasedBrowser` 是抽象基类（不能直接实例化），不要用它
_BROWSER_ALIASES = {
    # chromium 系
    "chromium": "chromium",
    "chrome": "chrome",
    "google-chrome": "chrome",
    "edge": "edge",
    "brave": "brave",
    "arc": "arc",
    "opera": "opera",
    "operagx": "operagx",
    "vivaldi": "vivaldi",
    "epic": "epic",
    # firefox 系
    "firefox": "firefox",
    "ff": "firefox",
    "librewolf": "librewolf",
    "zen": "zen",
    # safari
    "safari": "safari",
}


def _resolve_browsers(browsers: Optional[List[str]]) -> List[str]:
    """解析浏览器别名 → 库具体类名（去重 + 排序）

    Args:
        browsers: 用户传的浏览器名列表（支持别名），None 或 [] 表示"全部"

    Returns:
        去重 + 排序后的具体类名列表；空列表表示"调 get_history() 全扫"

    Raises:
        ValueError: 不支持的浏览器名
    """
    if not browsers:
        return []
    resolved = set()
    unsupported = []
    for b in browsers:
        if not isinstance(b, str):
            continue
        canon = _BROWSER_ALIASES.get(b.strip().lower())
        if canon:
            resolved.add(canon)
        else:
            unsupported.append(b)
    if unsupported:
        raise ValueError(
            f"不支持的浏览器：{', '.join(unsupported)}。"
            f"支持：{', '.join(sorted(_BROWSER_ALIASES.keys()))}"
        )
    return sorted(resolved)


def _fetch_browser_class(name: str):
    """通过库 browsers 模块的 getattr 拿到具体类（不 import 全集）"""
    import browser_history.browsers as b_mod
    # 类名是首字母大写（Chrome/Edge/Opera/OperaGX/Brave/Vivaldi/Epic/Arc/
    #   Firefox/LibreWolf/Zen/Safari/Chromium）
    return getattr(b_mod, name.capitalize(), None)


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
    自动处理 8+ 浏览器的历史读取（Chrome / Edge / Firefox / Safari / Arc / Zen / Brave）。
    0 依赖、20KB。

    时长估算（v0.5.8 新增）：
      browser-history 不提供停留时长，我们用"同域名相邻 visit 时间差"启发式估算。
      单次访问时长截断到 [5s, 30min] 区间。

    --browser 参数（v0.7.0 任务 3）：
      库不支持按 chrome/edge 区分（都归 chromium）→ 用 3 个具体类分别 fetch
      库自动处理 SQLite 锁（fetch_history 内部复制到临时文件）
    """
    name = "browser"

    def is_available(self) -> bool:
        # browser-history 内部会扫描已知路径
        # 永远返回 True，让 collect() 自己处理空历史
        return True

    def collect(
        self,
        since: Optional[datetime] = None,
        browsers: Optional[List[str]] = None,
    ) -> list[Event]:
        """采集浏览器历史

        Args:
            since: 时间起点（None = 全部）
            browsers: 浏览器列表（None/[] = 全部）。
                      支持 chrome/edge/brave/arc/chromium/firefox/ff/safari。
                      库不支持按 chrome/edge 区分（都归 chromium 类）。
        """
        # v0.7.0：解析 --browser 别名
        canonical = _resolve_browsers(browsers)
        raw_visits = self._fetch_visits(canonical)

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

    @staticmethod
    def _fetch_visits(canonical_browsers: List[str]) -> List[Tuple]:
        """根据 canonical 浏览器列表调相应 fetch 方法

        库的 browser-history v0.5+ 在 fetch_history 内部已自动复制 SQLite 到临时文件
        （避开 Chrome 运行时锁住 History.db 的问题），无需我们手动 copy。
        """
        if not canonical_browsers:
            # 默认全扫
            from browser_history import get_history
            outputs = get_history()
            return list(outputs.histories) if outputs.histories else []

        # 按具体类 fetch
        all_histories: List[Tuple] = []
        for canon in canonical_browsers:
            cls = _fetch_browser_class(canon)
            if cls is None:
                # 类不存在（库版本可能不包含这个浏览器）
                continue
            try:
                outputs = cls().fetch_history()
            except Exception:
                # 单个浏览器失败不阻塞其他
                continue
            if outputs and outputs.histories:
                all_histories.extend(outputs.histories)
        return all_histories
