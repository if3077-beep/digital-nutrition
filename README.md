# Digital Nutrition Label | 数字营养标签

![Test](https://github.com/if3077-beep/digital-nutrition/actions/workflows/test.yml/badge.svg)
![GitHub release](https://img.shields.io/github/v/release/if3077-beep/digital-nutrition)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)

> **GitHub**: [if3077-beep/digital-nutrition](https://github.com/if3077-beep/digital-nutrition) | **当前版本 / Current**: v0.7.0

---

## 简介 | Introduction

### 🇨🇳 中文

**数字营养标签** 是一款为开发者设计的自我观察工具。它通过分析你的浏览器历史（Chrome / Edge / Firefox / Safari / Arc / Zen / Brave 等 8+ 浏览器）和 Git commit 活动，自动生成一份独特的"开发者人格"报告。

你将看到：

- 📊 **多数据源**：单一命令汇总浏览器历史 + Git 活动
- 🧠 **人格分类**：自动识别 7 种开发者人格类型（"代码机器人" / "学习永动机" / "娱乐至上" ...）
- 💡 **智能洞察**：3-5 条自然语言洞察，含"相比上周"趋势对比
- 📅 **每日趋势图**：7 天堆叠柱状图，看清每天在做什么
- 🎨 **可视化报告**：基于 ECharts 的交互式 HTML 页面
- 🔒 **隐私优先**：完全本地运行，无网络请求
- 📁 **历史报告**：自动保存到 `~/.digital-nutrition/history/`，可对比往期
- 📤 **分享卡**：浏览器端一键导出 PNG 分享卡

> 💡 **核心理念**：和食品营养标签一样，让数字生活的"成分"一目了然——你花多少时间在写代码、学习、刷新闻上。

### 🇬🇧 English

**Digital Nutrition Label** is a self-observation tool designed for developers. It analyzes your browser history (Chrome, Edge, Firefox, Safari, Arc, Zen, Brave — 8+ browsers supported) and Git commit activity, then automatically generates a unique "developer persona" report.

You will see:

- 📊 **Multi-source data**: One command to aggregate browser history + Git activity
- 🧠 **Persona classification**: Auto-identify 7 developer persona types ("Code Robot" / "Learning Machine" / "Entertainment First" ...)
- 💡 **Smart insights**: 3-5 natural language insights, including week-over-week trend comparisons
- 📅 **Daily trend chart**: 7-day stacked bar chart, see what you do every day
- 🎨 **Visual report**: Interactive HTML page powered by ECharts
- 🔒 **Privacy-first**: Runs entirely locally, no network requests
- 📁 **Historical reports**: Auto-save to `~/.digital-nutrition/history/`, compare with past
- 📤 **Share card**: One-click export PNG share card in browser

> 💡 **Core idea**: Just like a food nutrition label, make the "ingredients" of your digital life transparent — how much time you spend on coding, learning, news, and so on.

---

## 快速开始 | Quick Start

```bash
# 1. 克隆
git clone https://github.com/if3077-beep/digital-nutrition.git
cd digital-nutrition

# 2. 安装（开发模式）
pip install -e .

# 3. （可选）首次跑：创建自定义规则模板
digital-nutrition init

# 4. 跑本周报告
digital-nutrition weekly
```

### 系统要求 | Requirements

- Python ≥ 3.10
- 操作系统 / OS: Windows 10+ / macOS 10.15+ / Linux
- 浏览器 / Browser: Chrome / Edge / Firefox / Safari / Arc / Zen / Brave 任一
- Git（可选 / optional，用于采集 commit 活动）

### 故障排查 | Troubleshooting

跑 `digital-nutrition doctor` 一键自检环境（5 项检查 + 建议）。

---

## 开发者人格类型 | Developer Personas

| 类型 / Type | 特征 / Trait | 描述 / Description |
|------|------|------|
| 🧱 代码机器人 Code Robot | code > 50% | 你是一台不知疲倦的代码生成器 / An tireless code generator |
| 📚 学习永动机 Learning Machine | learning > 40% | 你每天都在学习，但代码产出呢？/ You learn every day, but where's the code? |
| 🎬 娱乐至上 Entertainment First | entertainment > 30% | 你看的视频比写的代码多 / You watch more videos than write code |
| 📰 资讯焦虑 News Addict | news > 40% | 你被信息流裹挟，难以静心 / You're swept by the information stream |
| 🔍 观察者 Observer | social > 30% | 你了解所有人的动态 / You know everyone's updates |
| ⚖️ 平衡大师 Balanced Master | 各类别 15-30% 均匀 / 15-30% each | 你的时间分配堪称教科书 / Your time allocation is textbook-perfect |
| 🌐 多元探索者 Explorer | 其他 / Other | 你的兴趣广泛 / Your interests are broad |

---

## 架构 | Architecture (v0.5+)

```
digital_nutrition/                # 顶层 package
├── cli.py / models.py / classify.py
├── analyze.py / persona.py / insight.py
├── report_generator.py / trend.py / history.py
│
├── sources/                      # 数据源 / Data sources
│   ├── browser.py                # 包装 browser-history（Chrome/Edge/Firefox/...）
│   └── git.py
│
├── history/                      # 持久化 / Persistence
│   ├── store.py                  # 保存/加载 / Save/load
│   └── export.py                 # JSON 导出 / JSON export
│
└── report/                       # 报告生成 / Report generation
    ├── generator.py
    └── share.py                  # 浏览器端 PNG 分享卡 metadata
```

**数据流 / Data flow**：
```
BrowserSource + GitSource → [Event] → apply_classification
    → build_report_data → classify_persona → generate_insights
    → render_report (HTML) → save_report → export (optional)
```

---

## 开发 | Development

```bash
# 运行测试 / Run tests
python -m pytest tests/ -v

# 手动测试 / Manual test
python -m digital_nutrition.cli weekly --no-open
```

---

## 路线图 | Roadmap

- [x] v0.1: Chrome/Edge/Git 基础采集 + 人格分类 + 洞察（11 模块 / 93 tests / 16 commits）
- [x] v0.2: 历史对比 + 每日趋势图 + 趋势洞察（+2 模块 / 112 tests / 3 commits）
- [x] v0.5: 顶层重构 + browser-history 集成 + PNG 分享卡 + JSON 导出（114 tests / 2 commits）
- [x] v0.5.x: 周末模式洞察 + show/init 子命令 + weekly --export 自动备份（139 tests / 1 commit）
- [x] v0.5.5-v0.5.9: 集中版本号 + 分享卡 footer 动态版本 + doctor + Top N + CI/CD
- [x] v0.6.0: ignored_domains 隐私列表 + --json 输出 + --since 自定义时间范围（187 tests）
- [x] v0.7.0: rules CLI + --browser 过滤 + cli_print 拆分（227 tests）

---

## v0.7.0 用法 | v0.7.0 Usage

### `rules` CLI — 不打开编辑器也能管理规则 / Manage rules without opening editor

```bash
# 列出当前规则 / List current rules
digital-nutrition rules list

# 添加规则（重复 domain 会被拒绝） / Add rule (duplicate domain is rejected)
digital-nutrition rules add my-tech-blog.com learning
digital-nutrition rules add jira.mycompany.com work

# 删除规则 / Remove rule
digital-nutrition rules remove my-tech-blog.com

# 测试 URL 分类（只读，不写文件） / Test URL classification (read-only)
digital-nutrition rules test https://github.com/foo/bar
```

支持的 8 个类别 / Supported 8 categories：`code` / `learning` / `work` / `entertainment` / `news` / `social` / `shopping` / `other`

### `--browser` — 只看指定浏览器 / Filter by browser

```bash
# 只看 Chrome / Chrome only
digital-nutrition weekly --browser chrome

# 看 Chrome + Edge / Chrome + Edge
digital-nutrition weekly --browser chrome,edge

# 全部浏览器（默认） / All browsers (default)
digital-nutrition weekly
```

支持的浏览器别名 / Supported browser aliases：`chrome` / `edge` / `brave` / `arc` / `opera` / `operagx` / `vivaldi` / `epic` / `firefox` / `ff` / `librewolf` / `zen` / `safari` / `chromium` / `google-chrome`

---

## 常见问题 | FAQ

**Q: `weekly` 跑完浏览器没自动打开？/ Browser doesn't open automatically?**
A: 加 `--no-open` 跳过自动打开，然后 `digital-nutrition show` 手动打开。
   Use `--no-open` to skip auto-open, then `digital-nutrition show` to open manually.

**Q: 数据是云端还是本地？/ Cloud or local?**
A: 完全本地。`~/.digital-nutrition/` 目录下，所有数据不离开你的电脑。
   Entirely local. All data stays under `~/.digital-nutrition/`, never leaves your computer.
- 历史报告 / History: `%APPDATA%/../.digital-nutrition/history/`（Windows）/ `~/.digital-nutrition/history/`（macOS/Linux）
- 用户配置 / Config: `%APPDATA%/digital-nutrition/user_rules.json`

**Q: `browser-history` 找不到 Chrome / Edge 历史？/ Can't find Chrome/Edge history?**
A: 先关闭所有 Chrome 窗口（Chrome 锁住 History 数据库不让读）。Firefox/Safari 通常不需要。
   Close all Chrome windows first (Chrome locks the History database). Firefox/Safari usually don't need this.

**Q: 想自定义人格分类阈值？/ Want to customize persona thresholds?**
A: 编辑 `user_rules.json`，把域名加到对应类别（learning / work / entertainment / shopping / news / social）。

**Q: 周末洞察没显示？/ Weekend insights not showing?**
A: 需要至少 3 个有数据的工作日 + 1 个有数据的周末日才触发。
   Need at least 3 weekdays + 1 weekend day with data.

**Q: 怎么删掉所有数据？/ How to delete all data?**
A: 删除 `~/.digital-nutrition/` 整个目录。
   Delete the entire `~/.digital-nutrition/` directory.

---

## 许可 | License

MIT
