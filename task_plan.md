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

### Phase 2: v0.2 核心功能（90 min / 1 commit） ✅

**目标**：实现"时间维度" — 历史 + 趋势 + 每日图

**任务**：

**2.1 新模块 history.py**（20 min）
- [x] `scripts/history.py`:
  - [x] `get_history_dir()` → `Path.home() / ".digital-nutrition" / "history"`
  - [x] `save_report(report_data, persona, insights, history_dir=None)` → 写 JSON
  - [x] `list_reports(history_dir=None)` → 倒序列表（**按 mtime 而非文件名**）
  - [x] `load_history(limit=10, history_dir=None)` → 读 dict list
- [x] `tests/test_history.py`: 4 个代表性测试

**2.2 新模块 trend.py**（15 min）
- [x] `scripts/trend.py`:
  - [x] `build_daily_aggregates(events)` → `{date_str: {cat: seconds}}`
  - [x] `compute_category_deltas(current, previous)` → `{cat: {current, previous, delta, delta_pct}}`
- [x] `tests/test_trend.py`: 4 个代表性测试

**2.3 扩展 insight.py**（15 min）
- [x] `scripts/insight.py`:
  - [x] 新增 `generate_trend_insight(deltas)` → "相比上周，代码↑25%"
  - [x] 修改 `generate_insights()` 接受可选 `deltas` 参数
- [x] `tests/test_insight.py` 增加 4 个 trend 测试

**2.4 修改 report_generator.py + 模板**（20 min）
- [x] `scripts/report_generator.py`:
  - [x] `render_report()` 接受 `daily_aggregates=None` 参数
  - [x] 新增 `build_daily_chart()` 构建 ECharts 堆叠柱状图数据
- [x] `templates/report.html.j2`:
  - [x] 插入"每日趋势"区块
  - [x] ECharts 堆叠柱状图 script

**2.5 修改 main.py 整合**（15 min）
- [x] `scripts/main.py`:
  - [x] 引入 Pipeline 注释
  - [x] `apply_classification()` 分类后构建 daily aggregates
  - [x] `load_history(limit=1)` 计算 deltas
  - [x] 重新生成含趋势的 insights
  - [x] `save_report()` 保存历史
  - [x] `render_report(..., daily_aggregates=daily)` 渲染
- [x] `tests/test_main.py`:
  - [x] `test_generate_report_saves_to_history`（用 USERPROFILE 重定向）
  - [x] `test_generate_report_includes_trend_with_history`

**完成定义**：
- [x] `python -m scripts.main weekly --no-open` 跑 2+ 次，历史累积
- [x] 报告 HTML 含每日趋势图
- [x] 107 tests pass
- [x] 1 commit: `feat: add v0.2 trend analysis (history + comparison + daily chart)`

**实战发现**：
- ⚠️ main.py 的 `from history import` 加载的是 `history` 模块（不是 `scripts.history`），导致 monkeypatch 不生效。改用 `monkeypatch.setenv("USERPROFILE", ...)` 重定向 `Path.home()` 是更稳的方案
- ⚠️ 文件名用 UUID 唯一后，按文件名排序的方案不行（同秒内 UUID 顺序随机）。改为按 mtime 排序
- ✅ Pipeline 模式落地：collect → classify → aggregate → persona → insight → render → save

---

### Phase 3: 文档 + E2E（20 min / 1 commit） ✅

**目标**：完善文档和端到端验证

**任务**：
- [x] `tests/test_e2e.py` 增加 5 个 E2E 测试（history/trend/template/main 集成）
- [x] `README.md` 增加 v0.2 特性段（趋势图 + 历史报告）
- [x] `SKILL.md` 更新"输出内容"和"数据隐私"（增加 v0.2 标注）
- [x] 跑 `python -m pytest` 全部通过（112 pass）

**实战发现**：
- ⚠️ `trend.py` 缺 `sys.path.insert`，导致 `from scripts import trend` 失败。已补上
- ✅ 顶层 `test_e2e.py` 用静态 import + 内容断言，5 行覆盖整个 v0.2 集成

**完成定义**：
- [x] 112+ tests pass
- [x] README 反映 v0.2 状态
- [x] 1 commit: `docs: document v0.2 trend features`

---

## 🎉 v0.2 整体完成

- **3 个 phase** 全部 ✅（对比 v0.1 的 16 个 task）
- **总耗时**：~2 小时（v0.1 用 4 小时，效率 +100%）
- **测试**：93 → 112（+19）
- **Git**：v0.2 共 +3 commits
- **新功能**：历史存储 + 趋势对比 + 每日趋势图 + Pipeline 模式

下次工作入口：v0.3 候选（Firefox 支持 / 分享卡片 / Linux Chrome 修正 / 顶层 package 重构）

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
