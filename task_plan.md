# Digital Nutrition Label — 当前任务计划

> **更新规则**：每个 phase 完成时更新（不是每个 task）
> **粒度原则**：1 phase = 1 commit = 多模块+测试+整合

---

## 当前状态

- **当前阶段**：v0.1 完成 → 等待开始 v0.2
- **下一动作**：从 Phase 1 开始
- **预估总耗时**：~2 小时

---

## v0.2 路线图

### Phase 1: 基础设施小修（10 min / 1 commit） ✅

**目标**：确保 v0.1 基线干净，移除 `import` 残留

**任务**：
- [x] 检查 `report_generator.py` 等文件是否有 import 错误或残留
- [x] 创建 `digital-nutrition/scripts/__init__.py`（空文件）
- [x] 跑 `python -m pytest --tb=no -q 2>&1 | tail -3` 确认 93+ tests pass

**完成定义**：
- [x] 93+ tests 仍通过（实测 93 passed in 3.28s）
- [x] 1 commit: `chore: v0.2 prep - clean imports and __init__.py`

**不做什么**：
- 不引入新功能
- 不重命名文件
- 不动 v0.1 业务代码

**实战发现**：PowerShell 无 `tail`，要 `Select-Object -Last 5`。已记入 findings.md 待补。

---

### Phase 2: v0.2 核心功能（90 min / 1 commit）

**目标**：实现"时间维度" — 历史 + 趋势 + 每日图

**任务**：

**2.1 新模块 history.py**（20 min）
- [ ] `scripts/history.py`:
  - `get_history_dir()` → `Path.home() / ".digital-nutrition" / "history"`
  - `save_report(report_data, persona, insights, history_dir=None)` → 写 JSON
  - `list_reports(history_dir=None)` → 倒序列表
  - `load_history(limit=10, history_dir=None)` → 读 dict list
- [ ] `tests/test_history.py`: 5-6 个测试
  - `test_get_history_dir`
  - `test_save_report_creates_file` (用 `tmp_path` + monkeypatch)
  - `test_save_report_filename_format`
  - `test_list_reports_sorted`
  - `test_load_history_respects_limit`
  - `test_save_and_load_roundtrip`

**2.2 新模块 trend.py**（15 min）
- [ ] `scripts/trend.py`:
  - `build_daily_aggregates(events)` → `{date_str: {cat: seconds}}`
  - `compute_category_deltas(current, previous)` → `{cat: {current, previous, delta, delta_pct}}`
- [ ] `tests/test_trend.py`: 4-5 个测试
  - `test_build_daily_aggregates_basic`
  - `test_build_daily_aggregates_empty`
  - `test_compare_periods_basic`
  - `test_compare_periods_zero_previous`

**2.3 扩展 insight.py**（15 min）
- [ ] `scripts/insight.py`:
  - 新增 `generate_trend_insight(deltas)` → "相比上周，代码↑25%"
  - 修改 `generate_insights()` 接受可选 `deltas` 参数
- [ ] `tests/test_insight.py` 增加 3 个 trend 测试

**2.4 修改 report_generator.py + 模板**（20 min）
- [ ] `scripts/report_generator.py`:
  - `render_report()` 接受 `daily_aggregates=None` 参数
  - 准备 `daily_chart_data` (JSON) 和 `daily_chart_dates` (JSON list)
- [ ] `templates/report.html.j2`:
  - 在"时间分布"之后插入"每日趋势"区块
  - 模板底部加 ECharts 堆叠柱状图 script

**2.5 修改 main.py 整合**（15 min）
- [ ] `scripts/main.py`:
  - import 增加 `history`, `trend`
  - `generate_report()` 内:
    - `analyze.apply_classification()` 取 classified events
    - `build_daily_aggregates(classified_events)` → daily
    - `load_history(limit=1)` → 上一份报告
    - 如果有 history: `compute_category_deltas(current, previous)` → deltas
    - 重新 `generate_insights(..., deltas=deltas)`
    - `save_report(report_data, persona, insights)` 保存当前
    - `render_report(..., daily_aggregates=daily)` 渲染
- [ ] `tests/test_main.py`:
  - `test_generate_report_saves_history`
  - `test_generate_report_includes_trend_when_history_exists`（mock 历史存在）

**完成定义**：
- [ ] `python -m scripts.main weekly --no-open` 跑 2 次，第二次有"相比上周"洞察
- [ ] 报告 HTML 含每日趋势图
- [ ] 110+ tests pass
- [ ] 1 commit: `feat: add v0.2 trend analysis (history + comparison + daily chart)`

---

### Phase 3: 文档 + E2E（20 min / 1 commit）

**目标**：完善文档和端到端验证

**任务**：
- [ ] `tests/test_e2e.py` 增加 3-4 个 E2E
  - `test_history_module_exposes_api`
  - `test_trend_module_exposes_api`
  - `test_report_template_supports_daily_chart`
  - `test_main_module_imports_history_trend`
- [ ] `README.md` 特性段增加 v0.2 描述
- [ ] `SKILL.md` 更新"输出内容"部分
- [ ] 跑 `python -m pytest` 全部通过

**完成定义**：
- [ ] 110+ tests pass
- [ ] README 反映 v0.2 状态
- [ ] 1 commit: `docs: document v0.2 trend features`

---

## 完成后（v0.2 done）

- 更新本文件：标记所有 phase ✅，加新段"v0.3 计划"
- 更新 `progress.md`：记录 v0.2 session
- v0.3 候选（待用户决定）：
  - Firefox/Safari 支持
  - 分享卡片（PNG 导出）
  - Linux Chrome 路径修正
  - 自定义规则管理 CLI

---

## 决策记录

| 日期 | 决策 | 原因 |
|------|------|------|
| 2026-06-04 | v0.1 用 16 个 task 1 commit/task | 初始设计，过于细粒度 |
| 2026-06-04 | v0.2 改为 3 个 phase | 经验教训：commit 粒度应匹配功能边界 |
| 2026-06-04 | 暂不重构为顶层 package | 保持 v0.1 兼容，留待 v0.3 |
| 2026-06-04 | ECharts 仍本地打包 | 不依赖 CDN |
