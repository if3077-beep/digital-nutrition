"""
历史报告存储 - 每次生成的报告序列化到 JSON 文件
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


def get_history_dir() -> Path:
    """获取历史报告目录（默认 ~/.digital-nutrition/history/）"""
    d = Path.home() / ".digital-nutrition" / "history"
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_report(
    report_data: Dict,
    persona: str,
    insights: List[str],
    history_dir: Optional[Path] = None,
) -> Path:
    """保存报告到历史目录，返回写入的文件路径"""
    if history_dir is None:
        history_dir = get_history_dir()
    history_dir.mkdir(parents=True, exist_ok=True)

    # 用日期 + 短 UUID 保证唯一性
    timestamp = datetime.now()
    short_id = uuid.uuid4().hex[:8]
    filename = f"{timestamp.strftime('%Y-%m-%d_%H%M%S')}_{short_id}.json"
    path = history_dir / filename

    payload = {
        "saved_at": timestamp.isoformat(),
        "persona": persona,
        "insights": insights,
        **report_data,
    }
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def list_reports(history_dir: Optional[Path] = None) -> List[Path]:
    """列出所有历史报告，按修改时间倒序（最新优先）"""
    if history_dir is None:
        history_dir = get_history_dir()
    if not history_dir.exists():
        return []
    files = list(history_dir.glob("*.json"))
    # 用 mtime 排序而不是文件名（文件名内 UUID 随机，无法保证新文件在最后）
    return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)


def load_history(limit: int = 10, history_dir: Optional[Path] = None) -> List[Dict]:
    """读取最近 N 份历史报告"""
    paths = list_reports(history_dir)[:limit]
    return [json.loads(p.read_text(encoding="utf-8")) for p in paths]
