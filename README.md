# Digital Nutrition Label

> 一个 Claude Code Skill — 分析浏览器历史和 Git 活动，生成你的"开发者人格"报告。

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

```bash
# 1. 克隆并安装
git clone <repo>
cd digital-nutrition
pip install -e .

# 2. 运行
digital-nutrition weekly
```

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
