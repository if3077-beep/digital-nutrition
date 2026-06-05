# Digital Nutrition Label — v0.2 跨 Session 指导手册

> **给后续 session 的执行者使用**（包括未来几天的我）
> 写于 v0.1 完成后，整合了 v0.1 的实战经验和低效教训

---

## 🎯 项目状态

| 项 | 状态 |
|----|------|
| 设计文档 | [design.md](file:///C:/Users/zz/Desktop/TRAE/过程文件/2026-06-04_数字营养标签/design.md) ✅ |
| v0.1 MVP | ✅ 完成（16 commits / 93 tests passing） |
| v0.2 趋势对比 | ⏳ 待开始 |
| 路线图 | v0.2 → v0.3 → v1.0（见 design.md §16） |

## 📁 项目位置

```
工作目录：C:\Users\zz\Desktop\TRAE\过程文件\2026-06-04_数字营养标签\
项目目录：digital-nutrition/
规划文件：digital-nutrition/
  ├── task_plan.md         # 当前阶段计划（每阶段 1 个 commit）
  ├── findings.md          # 研究/发现/坑
  ├── progress.md          # session 日志
  └── AGENTS.md            # 本文件
```

---

## 🚨 v0.1 关键低效教训（必读）

### 教训 1: 16 个 task 粒度过细，commit 散乱
**症状**：每个 helper 函数一个 commit，16 个 `feat: add X` 提交
**问题**：
- 仓库历史噪声大，难看 review
- 大量小 commit 浪费 turn 数
**改进**：**每阶段 1 个 commit**。一个阶段 = 多个相关模块 + 它们的测试 + 整合

### 教训 2: 重复 boilerplate
**症状**：每个 `scripts/*.py` 顶部都有 `sys.path.insert(0, str(Path(__file__).parent))`
**问题**：11 个文件重复这段代码，每次新文件都要复制
**v0.1 现状**：保留现状（已提交），**v0.2 不要再加新 `sys.path.insert`**
**未来重构**：v0.3 改成 `digital_nutrition/` 顶层 package（去掉 scripts/）

### 教训 3: 过度 TDD 粒度
**症状**：`format_duration` 这种简单函数写了 4 个测试，包括 `format_duration(0)` 这种边界 case
**问题**：边界 case 测试拖慢节奏
**改进**：**写代表性测试**，不写穷举。边界 case 在写实现时就处理掉，不写专门测试

### 教训 4: Red-Green-Red-Green 多回合
**症状**：写测试→失败→实现→通过→边界失败→修边界→再通过（2-3 个回合）
**问题**：每个回合都要跑测试 + 思考 + 写代码
**改进**：**写实现时一次到位**。先在脑子里跑通：边界 case、None、空 list、类型。然后写代码 + 测试一起交付

### 教训 5: PowerShell 不支持 `&&`
**症状**：每次用 `cmd1 && cmd2` 都失败
**解决**：**直接用 `;`**（PowerShell 兼容，Bash 也兼容）

### 教训 6: sandbox 警告
**症状**：测试时偶发 `TRAE Sandbox Error: hit restricted` 关于 `webbrowser.cpython-312.pyc`
**实际影响**：无，测试照样通过
**处理**：**忽略**。这是 Trae sandbox 的 `.pyc` 缓存警告，不影响功能

### 教训 7: 没充分利用 subagent 并行
**症状**：独立纯函数模块（persona / insight / serve）串行开发
**v0.2 改进**：3 个独立纯函数模块用 subagent 并行写

### 教训 8: 长输出浪费 context
**症状**：`git log --oneline` 输出 16 行，pytest 全量列表几十行
**改进**：用 `| Select-Object -First 5` / `| tail -3` 限制输出

### 教训 9: 事前探索不足
**症状**：实现 `format_duration` 时没想 `0` 的语义
**改进**：**写实现前先在脑子里跑通：边界 / 异常 / 类型**。把异常 case 列在 commit message 或代码注释里

---

## 🔧 优化后的工作流

### 每次开始 Session 的 4 步

```bash
# 1. 切到项目
cd "C:\Users\zz\Desktop\TRAE\过程文件\2026-06-04_数字营养标签\digital-nutrition"

# 2. 读取规划（5 句话能复述当前状态）
Read task_plan.md        # 当前阶段 + 任务清单
Read progress.md         # 上次进展 + 遇到的问题
Read findings.md         # 已知坑 + 优化点

# 3. 验证环境（30 秒）
git status
python -m pytest --tb=no -q 2>&1 | tail -3   # 确认所有测试还过
```

### 工作时的 5 个原则

| 原则 | 说明 |
|------|------|
| **P1: 一次到位** | 写代码前先想通边界，写完直接通过 |
| **P2: 阶段粒度 commit** | 多个相关模块 + 测试 + 整合 = 1 commit |
| **P3: 代表性测试** | 每个函数 1-2 个测试足够，边界 case 一起写 |
| **P4: subagent 并行** | 3+ 独立纯函数模块用 subagent 同时写 |
| **P5: 精简输出** | 限制 stdout / stderr，避免 noise |

### PowerShell 命令规范

```bash
# ✅ 用 ; 分隔
cd "..."; git status; python -m pytest --tb=no -q | tail -3

# ❌ 不要用 &&
cd "..." && git status

# 测试命令模板（用 Select-Object 限制输出）
python -m pytest --tb=no -q 2>&1 | Select-Object -Last 3
python -m pytest tests/test_X.py -v 2>&1 | Select-Object -First 15
```

### Commit 粒度规范

```bash
# ✅ 一个阶段一个 commit（推荐）
git commit -m "feat: add v0.2 trend analysis (history + comparison + chart)"

# ❌ 不要：一个函数一个 commit
git commit -m "feat: add history module"
git commit -m "feat: add save_report function"
git commit -m "test: add test for save_report"
```

---

## 📋 v0.2 精简计划

**目标**：给 v0.1 加"时间维度" — 历史存储 + 趋势对比 + 每日趋势图

**预估总耗时**：~2 小时（v0.1 用 3 小时做 16 个 task，v0.2 优化为 3 个 phase）

### Phase 1: 基础设施小修（10 min / 1 commit）

- 移除 `report_generator.py` 里的 `import` 错误（如有）
- 加 `digital_nutrition/scripts/__init__.py`（空文件即可）
- 跑全部测试确认基线
- **不引入新功能**

**完成定义**：
- [ ] `python -m pytest` 仍然 93+ tests pass
- [ ] 1 commit

### Phase 2: v0.2 核心功能（90 min / 1 commit）

**模块 1: history.py**（保存 / 读取历史报告）
- `get_history_dir()` → `~/.digital-nutrition/history/`
- `save_report(report_data, persona, insights, path)` → 写 JSON
- `load_history(limit=10)` → 读最近 N 份

**模块 2: trend.py**（聚合 + 对比）
- `build_daily_aggregates(events)` → `{date: {cat: seconds}}`
- `compute_category_deltas(current, previous)` → `{cat: {delta, delta_pct}}`

**修改 1: insight.py**
- 新增 `generate_trend_insight(deltas)` → "相比上周，代码↑25%"
- 扩展 `generate_insights()` 接受可选 `deltas` 参数

**修改 2: report_generator.py + report.html.j2**
- `render_report()` 接受 `daily_aggregates`
- 模板加每日趋势图区块（ECharts 堆叠柱状图）

**修改 3: main.py**
- 采集后：`save_report()` 保存当前报告
- `build_daily_aggregates()` 聚合
- `load_history()` 读最近 1 份，计算 `deltas`
- 重新 `generate_insights(..., deltas=deltas)`
- `render_report(..., daily_aggregates=daily)`

**测试**：每个新函数 2-3 个代表性测试，集中在 `test_history.py` / `test_trend.py` / 在 `test_insight.py` 加 trend 部分

**完成定义**：
- [ ] 跑两次 `python -m scripts.main weekly --no-open`，第二次看到"相比上周"洞察
- [ ] 报告有每日趋势图区块
- [ ] ~20 个新测试
- [ ] 1 commit

### Phase 3: 文档 + E2E（20 min / 1 commit）

- `tests/test_e2e.py` 增加 3-4 个 E2E（验证 history/trend 模块存在、模板支持 daily chart）
- `README.md` 增加 v0.2 特性段
- 跑全部测试确保不退化
- **完成定义**：
  - [ ] `python -m pytest` 110+ tests pass
  - [ ] 1 commit
  - [ ] README 反映 v0.2 状态

### 总计
- **3 个 commit**（v0.1 是 16 个）
- **~2 小时**（v0.1 是 ~4 小时）
- **效率提升 4 倍**

---

## 📞 跨 Session 恢复流程

如果你（未来的我）从 `/clear` 后回来，按这个顺序操作：

1. **读 4 个文件**（10 秒理解状态）：
   - `task_plan.md` — 当前 phase
   - `progress.md` — 上次工作记录
   - `findings.md` — 已知坑
   - `AGENTS.md` — 本文件（工作流）

2. **跑测试基线**：
   ```bash
   cd "C:\Users\zz\Desktop\TRAE\过程文件\2026-06-04_数字营养标签\digital-nutrition"
   python -m pytest --tb=no -q 2>&1 | Select-Object -Last 3
   ```

3. **看 git 状态**：
   ```bash
   git log --oneline | Select-Object -First 10
   git status
   ```

4. **根据 task_plan.md 决定下一步**：
   - 如果当前 phase 没开始 → 开始它
   - 如果当前 phase 部分完成 → 继续它
   - 如果当前 phase 完成 → 标记完成，开始下一 phase

5. **完成时更新 3 个文件 + 1 commit**

---

## 🐛 已知问题汇总（详见 findings.md）

| 问题 | 状态 | 解决方式 |
|------|------|----------|
| `sys.path.insert` 重复 | v0.1 接受 | v0.3 改顶层 package |
| PowerShell `&&` 不支持 | 已记录 | 用 `;` |
| Trae sandbox .pyc 警告 | 已知 | 忽略 |
| 浏览器 DB 锁定 | v0.1 已解 | temp file copy |
| `format_duration(0)` 边界 | v0.1 已修 | 返回 "0m" |
| `classify_url` m.bilibili | v0.1 已修 | keep subdomain, let classify handle |

---

## ✅ 跨 Session "完成定义"

每个 phase 完成时：
- [ ] phase 内所有代码 + 测试 + 整合都完成
- [ ] `python -m pytest` 全部通过
- [ ] 1 个 git commit（不要多个）
- [ ] 更新 `task_plan.md`（标记 phase ✅）+ `progress.md`（记录问题）

v0.2 整体完成：
- [ ] 3 个 phase 全部 ✅
- [ ] 跑两次 `weekly` 看到趋势
- [ ] README + SKILL.md 反映 v0.2
- [ ] 全部测试 110+ pass
