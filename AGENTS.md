# Digital Nutrition Label — 跨 Session 指导手册

> 写于 v0.5 final 规划后（2026-06-05）。给后续 session 使用。

## 🎯 项目状态

| 项 | 状态 | 计划周次 |
|----|------|----------|
| v0.1 MVP | ✅ 完成 | — |
| v0.2 趋势对比 | ✅ 完成 | — |
| v0.3 Firefox + 分享卡片 | ❌ 已被 v0.5 取代 | — |
| **v0.5 架构现代化** | ⏳ **本周 W1 开工** | W1 |
| v0.6 数据丰富 + 实时 | ⏸️ 待 v0.5 完成后 | W2-W5 |
| v0.7 平台化骨架 | ⏸️ | W6-W9 |
| v1.0 整合 + 发布 | ⏸️ | W10-W12 |

## 📁 位置

```
项目根：C:\Users\zz\Desktop\TRAE\过程文件\2026-06-04_数字营养标签\digital-nutrition\
规划文件：AGENTS.md / task_plan.md / findings.md / progress.md（都在项目根）
设计文档：..\design.md
```

## 🚨 v0.1/v0.2 关键教训（必读）

| # | 教训 | 改进 |
|---|------|------|
| 1 | 16 task 粒度过细 | 每 phase 1 commit |
| 2 | 11 个文件都 `sys.path.insert` | **v0.5 顶层 package 化彻底解决** |
| 3 | 过度 TDD（4-15 tests/函数） | 1-2 代表性测试 |
| 4 | 多回合 red-green | 写实现前想通边界，一次到位 |
| 5 | PowerShell `&&` 不支持 | 用 `;` |
| 6 | Trae sandbox `.pyc` 警告 | 忽略 |
| 7 | 没利用 subagent 并行 | 独立纯函数模块用 subagent 并行 |
| 8 | 长输出堆积 context | `\| tail -3` / `\| Select-Object -First 5` |
| 9 | 事前探索不足 | 列边界 case 在 plan 里 |
| 10 | 自己造轮子 | **v0.5 决策：能依赖的依赖**（browser-history 替代 SQLite adapter） |
| 11 | 路径分散 `sys.path` | v0.5 顶层 package 化，pytest 直接 `from digital_nutrition import ...` |

## 🔧 工作流

### Session 开始
```bash
cd "C:\Users\zz\Desktop\TRAE\过程文件\2026-06-04_数字营养标签\digital-nutrition"
# 读 4 个规划文件
git status; python -m pytest --tb=no -q 2>&1 | tail -3
```

### 工作时
- **一次到位**：想清边界再写
- **阶段粒度 commit**：1 phase = 1 commit
- **代表性测试**：1-2 tests/函数
- **subagent 并行**：独立纯函数
- **精简输出**：限制 stdout

### 命令规范
```bash
# ✅ PowerShell 兼容
cd "..."; git status; python -m pytest --tb=no -q 2>&1 | tail -3
# ❌ && 在 PowerShell 不支持
```

## 🎨 v0.2 顶层设计：Pipeline 模式

按用户决定，v0.2 引入轻量级 Pipeline 抽象（不重构 v0.1 整体）。

```python
# data flow: collect → classify → aggregate → analyze → render
Pipeline = [
    ("collect",    collect_all_sources),
    ("classify",   apply_classification_rules),
    ("aggregate",  compute_aggregates),
    ("persona",    classify_persona),
    ("insight",    generate_insights),
    ("render",     render_html_report),
    ("serve",      open_in_browser),  # 可选
]
```

**目的**：每个 stage 是独立函数 + 协议；v0.3 加 stage（如 `share_card`）只插一行。

具体实现放在 `main.py`（v0.2 不拆新文件，保持改动最小）。

## 📋 v0.2 计划（3 phase / 3 commit）

见 [task_plan.md](file:///C:/Users/zz/Desktop/TRAE/过程文件/2026-06-04_数字营养标签/digital-nutrition/task_plan.md)

## 🐛 已知坑

详见 [findings.md](file:///C:/Users/zz/Desktop/TRAE/过程文件/2026-06-04_数字营养标签/digital-nutrition/findings.md)

## ✅ 跨 Session 恢复

未来 session 入口：
1. 读 `task_plan.md`（3 个月 final 规划）
2. 读 `AGENTS.md`（本文件）
3. 读 `progress.md`（最近 session log）
4. 跑 `python -m pytest --tb=no -q 2>&1 | tail -3`（确认基线）
5. 看 `git log --oneline | Select-Object -First 5`（最近 commits）
6. 按 `task_plan.md` 当前 phase 继续

**v0.5 已开工**：W1 / 顶层重构 / 5h 工作量。

## 📚 v0.5 关键参考

- [v0.5 设计文档](file:///C:/Users/zz/Desktop/TRAE/过程文件/2026-06-04_数字营养标签/digital-nutrition/docs/superpowers/specs/2026-06-05-v0.5-design.md) — 完整 v1→v2→v3 思考过程
- [task_plan.md](file:///C:/Users/zz/Desktop/TRAE/过程文件/2026-06-04_数字营养标签/digital-nutrition/task_plan.md) — 3 个月 final 路线图
- [browser-history](https://github.com/browser-history/browser-history) — v0.5 关键依赖
