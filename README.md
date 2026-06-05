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

## v0.5 用法

### 分享卡

`weekly` / `daily` 命令生成的报告页面底部有 **"📤 保存分享卡 (PNG)"** 按钮。点击后浏览器端用 Canvas 绘制 720×480 PNG 卡片，含：

- 你的开发者人格 emoji + 名称（用 persona 主题色）
- 周期 + 总时长
- Top 3 类别横条（含百分比 + 时长）
- 1 条高亮洞察
- 底部 brand line

### JSON 导出

```bash
# 把所有历史报告导出到单个 JSON 文件（备份/迁移用）
digital-nutrition export --output backup-2026-06-05.json
```

输出结构：
```json
{
  "exported_at": "2026-06-05T12:30:00",
  "count": 5,
  "reports": [ { "saved_at": "...", "persona": "🌐 多元探索者", "by_category": {...}, "insights": [...], "source_filename": "..." } ]
}
```

## 许可

MIT
