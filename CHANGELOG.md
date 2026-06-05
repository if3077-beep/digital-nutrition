# Changelog

All notable changes to Digital Nutrition Label are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)

## [0.5.5] - 2026-06-05

### Changed
- **集中版本号**：`__version__` 移到 `digital_nutrition/__init__.py`，CLI 用 `--version` 输出
- **分享卡 footer** 不再硬编码 "v0.5"，用 `__version__` 动态注入
- **报告 HTML footer** 加版本号 (`v{{ version }}`)
- **首次运行欢迎信息**：跑 `weekly` / `daily` 时若 history 为空，打印 5 行欢迎 + 配置/历史目录路径
- **`show --no-open`** 输出更详细：`[i] filename  日期  人格  总时长  · 主类别`
- **`init`** 输出增加配置目录位置提示

### Added
- `--version` CLI flag
- `format_human(seconds)` 工具：`<1m` / `45m` / `2h 30m`
- `_top_category_label(by_category)` 工具：返回 "💻写代码" / "🎬娱乐" 等
- `_read_report_for_html(html_path)` 工具：取代只读 persona 的版本
- `_maybe_welcome_first_run()` 工具：检测 + 写标记
- `tests/test_cli_helpers.py`（13 tests）
- 4 个真实 e2e（不只测 help 文本）：
  - `test_show_no_open_with_real_history` — show 在有真实历史时输出正确
  - `test_export_subcommand_creates_file_with_data` — export 写文件 + JSON 可解析
  - `test_share_card_footer_uses_dynamic_version` — 分享卡 footer 用 `__version__`
  - `test_template_uses_dynamic_version` — 模板 disclaimer 用 `{{ version }}`
- `CHANGELOG.md`（本文件）

### Tests
- 139 → 157 tests (+18)

## [0.5.x] - 2026-06-05

### Added
- `show` 子命令：列出 / 打开历史报告（`--index` / `--no-open` / `--limit`）
- `init` 子命令：在用户配置目录创建 `user_rules.json` 模板（`--force` 覆盖）
- `weekly` / `daily --export PATH`：跑完自动 export 所有历史
- 周末模式洞察：`generate_weekend_insight()` 分析工作日 vs 周末平均时长
- `aggregate_by_day_of_week()` 在 `analyze.py`
- `list_html_reports()` + `save_report(html_path=...)` 把 HTML + assets 一起存到 history

## [0.5] - 2026-06-05

### Added
- **顶层 package**：`scripts/` → `digital_nutrition/`，`pip install -e .`
- **browser-history 集成**：替代自实现的 Chrome/Edge SQLite 适配器（删 200+ 行）
- **`Source` ABC** in `sources/base.py`（用 `ABC` 不用 `Protocol` 因为后者不支持 `class X(Source)` 声明）
- **`BrowserSource`** 包装 browser-history 0.5（支持 8+ 浏览器白送）
- **`GitSource`** 包装原 `read_git_activity`
- **PNG 分享卡**：浏览器端 Canvas 绘制，`toDataURL()` 下载
- **JSON 导出**：`digital-nutrition export --output backup.json`
- 模板增加 `downloadShareCard()` JS 函数

### Removed
- `scripts/` 整个目录（11 个 v0.2 模块）
- `collect_chrome.py` / `collect_edge.py`（被 browser-history 替代）
- 11 个 `sys.path.insert` 散弹

## [0.2] - 2026-06-05

### Added
- 历史对比（`save_report` / `load_history` / `list_reports`）
- 每日趋势图（ECharts 堆叠柱图）
- 趋势洞察（`generate_trend_insight` + `compute_category_deltas`）

## [0.1] - 2026-06-04

### Added
- Chrome / Edge / Git 基础采集
- 7 种开发者人格分类
- 4 种洞察（极端 / 模式 / 平衡）
- HTML 报告渲染
- 11 模块 / 93 tests / 16 commits
