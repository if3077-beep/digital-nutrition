# Digital Nutrition Label

> 一个 Claude Code Skill — 分析浏览器历史和 Git 活动，生成你的"开发者人格"报告。
> **GitHub**: [if3077-beep/digital-nutrition](https://github.com/if3077-beep/digital-nutrition) | **当前版本**: v0.7.0
>
> ![Test](https://github.com/if3077-beep/digital-nutrition/actions/workflows/test.yml/badge.svg) ![PyPI](https://img.shields.io/pypi/v/digital-nutrition.svg) ![Python](https://img.shields.io/pypi/pyversions/digital-nutrition.svg) ![License](https://img.shields.io/pypi/l/digital-nutrition.svg)

## 特性

- 📊 **多数据源**：Chrome、Edge、Firefox、Safari、Arc、Zen、Brave 等浏览器历史 + Git commit（v0.5 通过 `browser-history` 库统一支持）
- 🧠 **人格分类**：自动识别 7 种开发者人格类型
- 💡 **智能洞察**：生成 3-5 条自然语言洞察（含"相比上周"趋势对比）
- 📅 **每日趋势图**：7 天堆叠柱状图，看清每天在做什么
- 🎨 **可视化报告**：基于 ECharts 的交互式页面
- 🔒 **隐私优先**：完全本地运行，无网络请求
- 📁 **历史报告**：自动保存到 `~/.digital-nutrition/history/`，可对比往期
- 📤 **分享卡**（v0.5）：浏览器端一键导出 PNG 分享卡
- 💾 **JSON 导出**（v0.5）：备份所有历史报告到单个 JSON 文件

## 快速开始

### 方式一：`pip install`（推荐，v0.7.0+）

```bash
# 1. 直接装
pip install digital-nutrition

# 2. （可选）首次跑：创建自定义规则模板
digital-nutrition init

# 3. 跑本周报告
digital-nutrition weekly
```

### 方式二：从 GitHub 克隆（开发者模式）

```bash
# 1. 克隆
git clone https://github.com/if3077-beep/digital-nutrition.git
cd digital-nutrition

# 2. 安装（开发模式）
pip install -e .

# 3. 跑本周报告
digital-nutrition weekly
```

### 系统要求

- Python ≥ 3.10
- 操作系统：Windows 10+ / macOS 10.15+ / Linux
- 浏览器：Chrome / Edge / Firefox / Safari / Arc / Zen / Brave 任一（v0.5 通过 [browser-history](https://github.com/browser-history/browser-history) 库统一支持 8+ 浏览器）
- Git（可选，用于采集 commit 活动）

### 故障排查

跑 `digital-nutrition doctor` 一键自检环境（5 项检查 + 建议）。

## 开发者人格类型

| 类型 | 特征 | 描述 |
|------|------|------|
| 🧱 代码机器人 | code > 50% | 你是一台不知疲倦的代码生成器 |
| 📚 学习永动机 | learning > 40% | 你每天都在学习，但代码产出呢？ |
| 🎬 娱乐至上 | entertainment > 30% | 你看的视频比写的代码多 |
| 📰 资讯焦虑 | news > 40% | 你被信息流裹挟，难以静心 |
| 🔍 观察者 | social > 30% | 你了解所有人的动态 |
| ⚖️ 平衡大师 | 各类别 15-30% 均匀 | 你的时间分配堪称教科书 |
| 🌐 多元探索者 | 其他 | 你的兴趣广泛 |

## 架构（v0.5）

```
digital_nutrition/                # 顶层 package
├── cli.py / models.py / classify.py
├── analyze.py / persona.py / insight.py
├── report_generator.py / trend.py / history.py
│
├── sources/                      # 数据源（Source 协议）
│   ├── browser.py                # 包装 browser-history（Chrome/Edge/Firefox/...）
│   └── git.py
│
├── history/                      # 持久化
│   ├── store.py                  # 保存/加载
│   └── export.py                 # JSON 导出
│
└── report/                       # 报告生成
    ├── generator.py
    └── share.py                  # 浏览器端 PNG 分享卡 metadata
```

**数据流**：
```
BrowserSource + GitSource → [Event] → apply_classification
    → build_report_data → classify_persona → generate_insights
    → render_report (HTML) → save_report → export (optional)
```

## 开发

```bash
# 运行测试
python -m pytest tests/ -v

# 手动测试
python -m digital_nutrition.cli weekly --no-open
```

## 路线图

- [x] v0.1: Chrome/Edge/Git 基础采集 + 人格分类 + 洞察（11 模块 / 93 tests / 16 commits）
- [x] v0.2: 历史对比 + 每日趋势图 + 趋势洞察（+2 模块 / 112 tests / 3 commits）
- [x] v0.5: 顶层重构 + browser-history 集成 + PNG 分享卡 + JSON 导出（114 tests / 2 commits）
- [x] v0.5.x: 周末模式洞察 + show/init 子命令 + weekly --export 自动备份（139 tests / 1 commit）
- [x] v0.5.5-v0.5.9: 集中版本号 + 分享卡 footer 动态版本 + doctor + Top N + CI/CD
- [x] v0.6.0: ignored_domains 隐私列表 + --json 输出 + --since 自定义时间范围（187 tests）
- [x] v0.7.0: rules CLI + --browser 过滤 + cli_print 拆分 + **PyPI 发布**（227 tests）

## v0.5.x 用法

### `show` 查看历史报告

```bash
# 列出最近 10 份报告
digital-nutrition show --no-open

# 打开最新报告（默认 --index 0）
digital-nutrition show

# 打开第 3 份报告
digital-nutrition show --index 2
```

### `init` 一键配置自定义规则

```bash
digital-nutrition init          # 在用户配置目录创建 user_rules.json 模板
digital-nutrition init --force  # 强制覆盖已存在的文件
```

模板示例：把 `my-tech-blog.com` 加到 `learning`，把 `jira.mycompany.com` 加到 `work`，下次 `weekly` 自动应用。

### `weekly --export` 自动备份

```bash
# 跑完 weekly 自动把所有历史报告导出到 backup.json
digital-nutrition weekly --no-open --export backup.json
```

### 周末模式洞察

新增 1 条洞察：分析工作日 vs 周末的时间分配。  
- `你周末更活跃（周末日均是工作日的 1.8 倍）` 
- `你周末明显放松（周末日均只有工作日的 30%）`

需要至少 3 个有数据的工作日 + 1 个有数据的周末日才触发。

## v0.7.0 用法

### `rules` CLI — 不打开编辑器也能管理规则

```bash
# 列出当前规则
digital-nutrition rules list

# 添加规则（重复 domain 会被拒绝）
digital-nutrition rules add my-tech-blog.com learning
digital-nutrition rules add jira.mycompany.com work

# 删除规则
digital-nutrition rules remove my-tech-blog.com

# 测试 URL 分类（只读，不写文件）
digital-nutrition rules test https://github.com/foo/bar
```

支持的 8 个类别：`code` / `learning` / `work` / `entertainment` / `news` / `social` / `shopping` / `other`

### `--browser` — 只看指定浏览器

```bash
# 只看 Chrome
digital-nutrition weekly --browser chrome

# 看 Chrome + Edge
digital-nutrition weekly --browser chrome,edge

# 全部浏览器（默认）
digital-nutrition weekly
```

支持的浏览器别名：`chrome` / `edge` / `brave` / `arc` / `opera` / `operagx` / `vivaldi` / `epic` / `firefox` / `ff` / `librewolf` / `zen` / `safari` / `chromium` / `google-chrome`

## 常见问题

**Q: `weekly` 跑完浏览器没自动打开？**
A: 加 `--no-open` 跳过自动打开，然后 `digital-nutrition show` 手动打开。

**Q: 数据是云端还是本地？**
A: 完全本地。`~/.digital-nutrition/` 目录下，所有数据不离开你的电脑。
- 历史报告：`%APPDATA%/../.digital-nutrition/history/`（Windows）/ `~/.digital-nutrition/history/`（macOS/Linux）
- 用户配置：`%APPDATA%/digital-nutrition/user_rules.json`

**Q: `browser-history` 找不到 Chrome / Edge 历史？**
A: 先关闭所有 Chrome 窗口（Chrome 锁住 History 数据库不让读）。Firefox/Safari 通常不需要。

**Q: 想自定义人格分类阈值？**
A: 编辑 `user_rules.json`，把域名加到对应类别（learning / work / entertainment / shopping / news / social）。

**Q: 周末洞察没显示？**
A: 需要至少 3 个有数据的工作日 + 1 个有数据的周末日才触发。

**Q: 怎么删掉所有数据？**
A: 删除 `~/.digital-nutrition/` 整个目录。

## 许可

MIT
