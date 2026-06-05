# Task Plan — v0.5 开工计划

> **2026-06-05 final**（3 个月路线图砍掉中间版本，只做 v0.5）
> **状态**：等待开工
> **工作量**：5h / 1 周内完成

---

## 🎯 v0.5 目标

**站在巨人肩膀上，做架构现代化**：
- 用 [browser-history](https://github.com/browser-history/browser-history) 替代自实现的 Chrome/Edge/Firefox SQLite 适配器
- 把 `scripts/` 中间层提到顶层 `digital_nutrition/` package
- 加 PNG 分享卡（浏览器端 canvas）
- 加 JSON 导出（为 sync / 备份打基础）

**v0.5 = 删 200 行 + 升 1 个架构 + 加 2 个新功能**

---

## 📦 Phase 1：顶层重构（3h）

### 1.1 依赖更新（5min）

- 改 `pyproject.toml`：
  - 加 `[project.scripts] digital-nutrition = "digital_nutrition.cli:main"`
  - 加 `[project.dependencies] browser-history = ">=0.5.0"`
- 改 `requirements.txt` 加 `browser-history>=0.5.0`

### 1.2 创建新 package 结构（10min）

```
digital_nutrition/
├── __init__.py
├── cli.py               # 原 main.py
├── models.py            # 原 scripts/models.py
├── classify.py          # 原 scripts/classify.py
├── analyze.py           # 原 scripts/analyze.py
├── persona.py           # 原 scripts/persona.py
├── insight.py           # 原 scripts/insight.py
├── report_generator.py  # 原 scripts/report_generator.py
├── trend.py             # 原 scripts/trend.py
├── history.py           # 原 scripts/history.py
│
├── sources/
│   ├── __init__.py
│   ├── base.py          # NEW
│   ├── browser.py       # NEW: 包装 browser-history
│   └── git.py           # 原 scripts/collect_git.py
│
├── history/
│   ├── __init__.py
│   ├── store.py         # 原 history.py 拆分
│   └── export.py        # NEW
│
└── report/
    ├── __init__.py
    ├── generator.py     # 原 report_generator.py 拆分
    └── share.py         # NEW
```

### 1.3 迁移 v0.2 代码到新位置（30min）

按依赖顺序（从下到上）：
1. `models.py` (无依赖)
2. `classify.py` (依赖 models)
3. `analyze.py` (依赖 models)
4. `persona.py` (依赖 models)
5. `insight.py` (依赖 models)
6. `trend.py` (依赖 models)
7. `report_generator.py` (依赖 models)
8. `history.py` (依赖 models)
9. `sources/git.py` (依赖 models)
10. `sources/browser.py` (依赖 models + browser_history)
11. `cli.py` (依赖所有)

### 1.4 修所有内部导入（30min）

- `from scripts.X import` → `from digital_nutrition.X import`（或 from digital_nutrition.submodule import）
- 删 11 个 `sys.path.insert(0, ...)`
- 跑 `pytest` 确认 112 tests 还过

### 1.5 删 v0.1 旧模块（5min）

- `git rm scripts/collect_chrome.py`（130 行）
- `git rm scripts/collect_edge.py`（80 行）
- `git rm scripts/` 整个目录

### 1.6 验证 Phase 1（10min）

```bash
cd "C:\Users\zz\Desktop\TRAE\过程文件\2026-06-04_数字营养标签\digital-nutrition"
pip install -e .
python -m digital_nutrition.cli weekly   # 应该和 v0.2 输出一样
```

- 验收：112 tests 全过、weekly 命令正常输出

### Phase 1 commit
```bash
git add .
git commit -m "refactor: top-level package + browser-history dependency

- scripts/ → digital_nutrition/ (top-level package)
- 11 sys.path.insert → clean imports
- Add BrowserSource wrapping browser-history (0 deps, 8+ browsers)
- Add Source Protocol in sources/base.py
- Delete collect_chrome.py / collect_edge.py (-200 lines)
- 112 tests still pass"
```

---

## 📦 Phase 2：分享卡 + 导出（2h）

### 2.1 JSON 导出（30min）

- 新建 `digital_nutrition/history/export.py`（`export_all_reports()`）
- 把 `history.py` 拆成 `history/store.py` + `history/export.py`
- 跑测试：`tests/test_history.py` 加 `test_export_all_reports` 系列

### 2.2 PNG 分享卡 metadata（30min）

- 新建 `digital_nutrition/report/share.py`（`get_share_card_metadata()`）
- 在 `cli.py` 调用 `get_share_card_metadata()` 并注入到 HTML 模板
- 跑测试：`tests/test_share.py` 加 `test_metadata_structure`

### 2.3 模板加 PNG 按钮（30min）

- `templates/report.html.j2` 末尾加：
  - `<button onclick="downloadShareCard()">📤 保存分享卡 (PNG)</button>`
  - `<script>` 含 canvas 绘制逻辑
- 注入 `window.__SHARE_CARD_DATA__`

### 2.4 文档 + 验收（30min）

- 更新 `README.md` 加 "分享卡" 和 "导出" 章节
- 更新 `SKILL.md` 输出内容 + 数据隐私
- 跑全测试 + E2E
- 验证 `digital-nutrition export` 和 `digital-nutrition weekly` 都工作

### Phase 2 commit
```bash
git add .
git commit -m "feat: browser PNG share card + JSON export

- digital_nutrition/history/export.py: export_all_reports()
- digital_nutrition/report/share.py: get_share_card_metadata()
- templates/report.html.j2: PNG share card button (browser-side canvas)
- digital-nutrition export subcommand
- tests: +6 tests (export + share + E2E)
- README / SKILL updated"
```

---

## 🧪 测试

- **目标**：40-60 tests
- **保留**：v0.2 关键测试（核心 classify / analyze / persona / insight / trend / report_generator）
- **删**：v0.1 的 `test_collect_chrome.py` / `test_collect_edge.py`（被 BrowserSource 替代）
- **新增**：
  - `tests/test_browser_source.py`（2-3 tests，mock browser-history）
  - `tests/test_export.py`（2-3 tests）
  - `tests/test_share.py`（1-2 tests）
  - `tests/test_e2e.py` 更新（3-5 tests，weekly/export/报告生成）

---

## ✅ 验收标准（全部 ✓ 才算 v0.5 完成）

- [ ] `pip install -e .` 成功
- [ ] `digital-nutrition weekly` 与 v0.2 输出**视觉一致**
- [ ] `digital-nutrition export --output backup.json` 导出成功
- [ ] 浏览器点 "保存分享卡" 下载 PNG
- [ ] 40-60 tests pass
- [ ] 删 `collect_chrome.py` / `collect_edge.py` 已 git rm
- [ ] 删 `scripts/` 整个目录
- [ ] 2 commits（Phase 1 / Phase 2）

---

## 🚫 不做（YAGNI）

- ❌ 规则引擎
- ❌ 多维度人格
- ❌ AFK 检测
- ❌ Pillow PNG（用浏览器按钮代替）
- ❌ 规则 CLI
- ❌ 多周期对比
- ❌ 浏览器扩展
- ❌ Server / REST API
- ❌ Firefox 单独实现（browser-history 已支持）
- ❌ 多用户
- ❌ 云同步
- ❌ AI 洞察
- ❌ Safari

---

## 📋 开工清单

**准备**（开工前 5min）：
- [ ] 读 `findings.md` 复习踩坑记录
- [ ] 跑 `python -m pytest --tb=no -q` 确认 v0.2 baseline 112 tests 过
- [ ] 跑 `git status` 确认工作区干净

**Phase 1**（3h）：
- [ ] 1.1 改 pyproject.toml + requirements.txt
- [ ] 1.2 创建 digital_nutrition/ 结构
- [ ] 1.3 迁移 11 个 v0.2 模块
- [ ] 1.4 修所有内部导入
- [ ] 1.5 删 collect_chrome.py / collect_edge.py / scripts/
- [ ] 1.6 验证：weekly 命令、112 tests

**Phase 2**（2h）：
- [ ] 2.1 export.py + 拆分 history.py
- [ ] 2.2 share.py metadata
- [ ] 2.3 模板加 PNG 按钮
- [ ] 2.4 文档 + E2E + 验收

**完成**：
- [ ] 2 commits
- [ ] push 到 origin（可选）
- [ ] 更新 progress.md

---

## 🗂️ 关键参考

- 📄 [v0.5 设计文档](file:///C:/Users/zz/Desktop/TRAE/过程文件/2026-06-04_数字营养标签/digital-nutrition/docs/superpowers/specs/2026-06-05-v0.5-design.md) — 完整 final 设计
- 📊 [findings.md](file:///C:/Users/zz/Desktop/TRAE/过程文件/2026-06-04_数字营养标签/digital-nutrition/findings.md) — 跨 session 踩坑记录
- 📖 [AGENTS.md](file:///C:/Users/zz/Desktop/TRAE/过程文件/2026-06-04_数字营养标签/digital-nutrition/AGENTS.md) — 跨 session 指导
- 📈 [progress.md](file:///C:/Users/zz/Desktop/TRAE/过程文件/2026-06-04_数字营养标签/digital-nutrition/progress.md) — session log
- 🔗 [browser-history](https://github.com/browser-history/browser-history) — v0.5 关键依赖
