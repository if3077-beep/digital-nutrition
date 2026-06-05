"""
历史报告导出 - 把所有历史报告序列化为单一 JSON 文件
用于备份、迁移到新机器、跨平台同步
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from digital_nutrition.history.store import list_reports


def export_all_reports(
    output_path: Path,
    history_dir: Optional[Path] = None,
) -> Path:
    """
    把 history_dir 里所有报告导出到单一 JSON 文件。

    输出格式：
    {
        "exported_at": "2026-06-05T12:30:00",
        "count": 5,
        "reports": [ {...}, {...} ]
    }

    Args:
        output_path: 导出文件路径
        history_dir: 历史目录（默认 ~/.digital-nutrition/history/）

    Returns:
        写入的 output_path
    """
    paths = list_reports(history_dir)
    reports: List[Dict] = []
    for p in paths:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            # 单个文件坏掉不应阻断整个导出，但记录
            print(f"Warning: skip {p.name}: {e}")
            continue
        # 补上 source_filename 方便排查
        data.setdefault("source_filename", p.name)
        reports.append(data)

    payload = {
        "exported_at": datetime.now().isoformat(timespec="seconds"),
        "count": len(reports),
        "reports": reports,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_path
