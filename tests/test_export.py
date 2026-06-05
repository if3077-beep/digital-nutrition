"""Tests for history export."""
import json
from digital_nutrition.history.export import export_all_reports
from digital_nutrition.history.store import save_report


def test_export_empty_history(tmp_path):
    """空历史导出应得到空 reports 列表"""
    output = tmp_path / "backup.json"
    result = export_all_reports(output, history_dir=tmp_path)
    assert result == output
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["count"] == 0
    assert payload["reports"] == []
    assert "exported_at" in payload


def test_export_all_reports_serializes_each(tmp_path):
    """多次 save 后导出应包含所有报告"""
    save_report({"by_category": {"code": 100}}, "🧱", ["i1"], history_dir=tmp_path)
    save_report({"by_category": {"learn": 200}}, "📚", ["i2"], history_dir=tmp_path)

    output = tmp_path / "backup.json"
    export_all_reports(output, history_dir=tmp_path)

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["count"] == 2
    personas = {r["persona"] for r in payload["reports"]}
    assert personas == {"🧱", "📚"}
    for r in payload["reports"]:
        assert "source_filename" in r
        assert r["source_filename"].endswith(".json")


def test_export_creates_parent_dir(tmp_path):
    """输出路径的父目录不存在时应自动创建"""
    output = tmp_path / "deep" / "nested" / "backup.json"
    export_all_reports(output, history_dir=tmp_path)
    assert output.exists()


def test_export_skips_corrupt_files(tmp_path):
    """坏掉的 JSON 文件应被跳过，其余正常导出"""
    save_report({"by_category": {"code": 50}}, "🧱", [], history_dir=tmp_path)
    # 写入一个坏 JSON
    (tmp_path / "bad.json").write_text("{not valid json", encoding="utf-8")

    output = tmp_path / "backup.json"
    export_all_reports(output, history_dir=tmp_path)
    payload = json.loads(output.read_text(encoding="utf-8"))
    # 只导出了 1 个有效报告
    assert payload["count"] == 1
    assert payload["reports"][0]["persona"] == "🧱"
