"""
历史报告存储 - 每次生成的报告序列化到 JSON 文件
"""
import json
import shutil
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
    html_path: Optional[Path] = None,
) -> Path:
    """
    保存报告到历史目录，返回写入的 JSON 文件路径。

    如果提供 html_path，会把该 HTML 复制到 history_dir
    （同名 stem，方便 `show` 子命令直接打开历史报告）。
    """
    if history_dir is None:
        history_dir = get_history_dir()
    history_dir.mkdir(parents=True, exist_ok=True)

    # 用日期 + 短 UUID 保证唯一性
    timestamp = datetime.now()
    short_id = uuid.uuid4().hex[:8]
    stem = f"{timestamp.strftime('%Y-%m-%d_%H%M%S')}_{short_id}"
    json_path = history_dir / f"{stem}.json"

    payload = {
        "saved_at": timestamp.isoformat(),
        "persona": persona,
        "insights": insights,
        **report_data,
    }
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # 可选：把 HTML 也存一份到 history_dir
    if html_path is not None and Path(html_path).exists():
        html_dest = history_dir / f"{stem}.html"
        assets_dirname = f"{stem}_assets"
        # 读 HTML，把 assets 引用改写到新位置，再写回
        html_text = Path(html_path).read_text(encoding="utf-8")
        html_text = html_text.replace('src="assets/', f'src="{assets_dirname}/')
        html_text = html_text.replace('href="assets/', f'href="{assets_dirname}/')
        html_dest.write_text(html_text, encoding="utf-8")
        # 把 assets 目录复制到 history_dir（重命名）
        assets_src = Path(html_path).parent / "assets"
        if assets_src.exists() and assets_src.is_dir():
            assets_dest = history_dir / assets_dirname
            if assets_dest.exists():
                shutil.rmtree(assets_dest)
            shutil.copytree(assets_src, assets_dest)

    return json_path


def list_reports(history_dir: Optional[Path] = None) -> List[Path]:
    """列出所有历史报告（JSON），按修改时间倒序（最新优先）"""
    if history_dir is None:
        history_dir = get_history_dir()
    if not history_dir.exists():
        return []
    files = list(history_dir.glob("*.json"))
    # 用 mtime 排序而不是文件名（文件名内 UUID 随机，无法保证新文件在最后）
    return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)


def list_html_reports(history_dir: Optional[Path] = None) -> List[Path]:
    """列出所有历史 HTML 报告（与 JSON 同 stem），按 mtime 倒序"""
    if history_dir is None:
        history_dir = get_history_dir()
    if not history_dir.exists():
        return []
    files = list(history_dir.glob("*.html"))
    return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)


def load_history(limit: int = 10, history_dir: Optional[Path] = None) -> List[Dict]:
    """读取最近 N 份历史报告"""
    paths = list_reports(history_dir)[:limit]
    return [json.loads(p.read_text(encoding="utf-8")) for p in paths]
