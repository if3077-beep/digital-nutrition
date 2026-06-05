# Digital Nutrition Label — 跨 Session 指导手册

> 写于 v0.5 final 规划后（2026-06-05）。给后续 session 使用。

## 🎯 项目状态

| 项 | 状态 | 备注 |
|----|------|------|
| v0.1 MVP | ✅ 完成 | 11 模块 / 93 tests / 16 commits |
| v0.2 趋势对比 | ✅ 完成 | +2 模块 / 112 tests / 3 commits |
| **v0.5 架构现代化** | ⏳ **W1 即将开工** | 5h / 2 commits / 删 200 行 + 加 2 个功能 |

## 📁 位置

```
项目根：C:\Users\zz\Desktop\TRAE\过程文件\2026-06-04_数字营养标签\digital-nutrition\
规划文件：AGENTS.md / task_plan.md / findings.md / progress.md（都在项目根）
设计文档：docs/superpowers/specs/2026-06-05-v0.5-design.md
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
| 8 | 长输出堆积 context | `\| tail -3` / `\| Select-Object -Last 5` |
| 9 | 事前探索不足 | 列边界 case 在 plan 里 |
| 10 | 自己造轮子 | **v0.5 决策：能依赖的依赖**（browser-history 替代 SQLite adapter） |
| 11 | 路径分散 `sys.path` | v0.5 顶层 package 化，pytest 直接 `from digital_nutrition import ...` |

## 🔧 工作流

### Session 开始
```bash
cd "C:\Users\zz\Desktop\TRAE\过程文件\2026-06-04_数字营养标签\digital-nutrition"
# 读 4 个规划文件
git status; python -m pytest --tb=no -q 2>&1 | Select-Object -Last 3
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
cd "..."; git status; python -m pytest --tb=no -q 2>&1 | Select-Object -Last 3
# ❌ && 在 PowerShell 不支持
# ❌ tail 在 PowerShell 不支持（用 Select-Object -Last N）
```

## 🐛 已知坑

详见 [findings.md](file:///C:/Users/zz/Desktop/TRAE/过程文件/2026-06-04_数字营养标签/digital-nutrition/findings.md)

## ✅ 跨 Session 恢复

未来 session 入口：
1. 读 `task_plan.md`（v0.5 final 计划）
2. 读 `AGENTS.md`（本文件）
3. 读 `progress.md`（最近 session log）
4. 跑 `python -m pytest --tb=no -q 2>&1 | Select-Object -Last 3`（确认基线）
5. 看 `git log --oneline | Select-Object -First 5`（最近 commits）
6. 按 `task_plan.md` 当前 phase 继续

**v0.5 待开工**：W1 / 顶层重构 + 分享卡 + JSON 导出 / 5h 工作量。

## 📚 v0.5 关键参考

- [v0.5 设计文档](file:///C:/Users/zz/Desktop/TRAE/过程文件/2026-06-04_数字营养标签/digital-nutrition/docs/superpowers/specs/2026-06-05-v0.5-design.md) — final 设计
- [task_plan.md](file:///C:/Users/zz/Desktop/TRAE/过程文件/2026-06-04_数字营养标签/digital-nutrition/task_plan.md) — 详细开工计划
- [browser-history](https://github.com/browser-history/browser-history) — v0.5 关键依赖
