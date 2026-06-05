# Changelog

All notable changes to Digital Nutrition Label are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)

## [0.5.9] - 2026-06-05

### Fixed (review 文档 Phase 1)
- **P0 Windows emoji 兼容**：所有 emoji print 用 `_emoji()` 包装（Windows GBK 终端不再 UnicodeEncodeError）
  - 优先尝试 `sys.stdout.reconfigure(encoding="utf-8")`
  - 失败时降级为 ASCII（`[OK]`, `[WARN]`, `[ERR]` 等）
  - 14 个 print 段已改造
- **P0 git log 合并**：合并两次 `git log` 调用为一次（review 建议方案）
  - 用 `---HASH:` 前缀标识 commit 边界
  - 新增 `parse_git_combined_output()` 函数
  - 大仓库开销减半

### Added (review 文档 Phase 2)
- **P1 CI/CD**：`.github/workflows/test.yml` 跑双平台 × 3 Python 版本矩阵
  - ubuntu-latest + windows-latest × py3.10/3.11/3.12
  - 包含 smoke test (`--version` + `doctor`)
- **P1 VSCode 调试**：`.vscode/launch.json` 提供 6 个调试入口
  - weekly / daily / doctor / show / init / pytest
- 13 个新测试（emoji + combined output）

### Tests
- 172 → 175 tests (+3 for parse_git_combined_output)

## [0.5.8] - 2026-06-05

### Changed (基于 review 文档 P0/P1/P2 优化)

### P0 数据可信度
- **P0-1 浏览器访问时长估算**：用"同域名相邻 visit 时间差"启发式估算（之前全 0）
  - 截断到 [5s, 30min] 区间
  - 同域名分组、独立计算
  - 新增 `estimate_durations()` 函数 + 6 个 unit test
- **P0-2 Git diff 行数估算时长**：用 `git log --shortstat` 拿行数映射时长
  - < 10 lines → 10 min, 10-100 → 30 min, > 100 → 60 min
  - 取代硬编码 30/60 min（review 建议方案 1）
  - 新增 `parse_git_shortstat()` + `_estimate_duration_from_diff()`

### P1 工程清理
- **P1-1 版本号单一来源**：`pyproject.toml` 用 `[tool.setuptools.dynamic]` 从 `__init__.py` 读 `__version__`（review 推荐方案 1）
- **P1-3 删 conftest.py sys.path.insert**：仅留注释（pip install -e . 后无需）

### P2 体验提升
- **P2-1 Top N 多维展示**：新增 "📊 本周概况" 区块（总时长/总事件/最忙日/高峰时段）
- `💡 试试` 区块加 `doctor` 入口

### Added (Tests)
- `test_estimate_durations_*` 6 个（空/同域/上限/下限/不同域）
- `test_domain_of_strips_www_and_lowercases` 1 个
- `test_parse_git_shortstat_*` 3 个（基本/空/只有 insertions）
- `test_estimate_duration_from_diff_tiers` 1 个（3 档边界）
- `test_read_git_activity_large_diff_60min` 1 个（>100 lines）

### Tests
- 161 → 172 tests (+11)

## [0.5.7] - 2026-06-05

### Added (PM 视角第三轮审查)
- **`doctor` 子命令**：自检环境（browser-history 库 / 浏览器历史 / Git 仓库 / user_rules / history 目录）
  - 5 项检查用 ✅/⚠️/❌ 状态展示
  - 有问题项给"💡 建议"
  - 有 err 时 exit code 1，无 err 时 exit code 0（CI 友好）
  - 静音 browser-history 库的 INFO 日志（让输出干净）
- **输出 sections 分组**：`weekly` / `daily` 跑完按 `📊 [1/3] 收集` / `⚙️ [2/3] 渲染` / `💾 [3/3] 持久化` 分块

### Changed
- **Top 3 域名过滤**：只显示 http(s)/ftp URL，过滤掉 Git 本地路径（之前 top 1 经常是 git 仓库路径）
- `first-run` 跳过 `doctor` 子命令（避免自检时打印欢迎）

### Added (Tests)
- `test_doctor_subcommand_exists` — 验证 doctor 在 --help 中
- `test_doctor_runs_and_prints_summary` — 验证 doctor 失败时 exit 1 + 输出格式
- `test_doctor_passes_with_git_repo_and_rules` — 验证 doctor 成功时 exit 0 + 至少 3 个 ✅

### Tests
- 158 → 161 tests (+3)

## [0.5.6] - 2026-06-05

### Changed (PM 视角审查)
- **PM 审查·产品价值**：`weekly` / `daily` 跑完输出"🔥 你访问最多的" Top 3 域名/路径
- **PM 审查·产品价值**：跑完加"💡 试试"提示区块（show / init / export）
- **PM 审查·错误体验**：`weekly` / `daily` 跑完没数据时打印可能原因 + 引导 `init`
- **PM 审查·错误体验**：浏览器历史读取失败时打印"常见原因：Chrome 还在运行"
- **PM 审查·错误体验**：Git 读取失败时提示用 `--repo` 参数
- **PM 审查·错误体验**：当前目录不是 Git 仓库时静默跳过（不是错误）
- **PM 审查·发现性**：主 `help` 加 4 步示例流程 epilog + GitHub 链接
- **PM 审查·传播性**：HTML 报告 footer 加 GitHub 链接
- **PM 审查·传播性**：PNG 分享卡底部加 GitHub URL 链接

### Added
- `tests/test_share.py::test_github_url_in_metadata` — 验证分享卡 metadata 含 GitHub URL

### Tests
- 157 → 158 tests (+1)

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
