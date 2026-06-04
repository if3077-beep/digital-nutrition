# Digital Nutrition Label

> 一个 Claude Code Skill — 分析浏览器历史和 Git 活动，生成你的"开发者人格"报告。

## 特性

- 📊 **多数据源**：Chrome、Edge 浏览器历史 + Git commit
- 🧠 **人格分类**：自动识别 7 种开发者人格类型
- 💡 **智能洞察**：生成 3-5 条自然语言洞察
- 🎨 **可视化报告**：基于 ECharts 的交互式页面
- 🔒 **隐私优先**：完全本地运行，无网络请求

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

## 架构

```
collect_chrome.py ─┐
collect_edge.py   ├─→ Event[] → analyze.py → report_data
collect_git.py    ─┘                              ↓
                                            persona.py
classify.py (domain rules)                       ↓
                                            insight.py
                                                ↓
                                       report_generator.py → HTML
                                                ↓
                                            serve.py → Browser
```

## 开发

```bash
# 运行测试
python -m pytest tests/ -v

# 手动测试
python -m scripts.main weekly --no-open
```

## 路线图

- [x] v0.1: Chrome/Edge/Git 基础采集 + 人格分类 + 洞察
- [ ] v0.2: Linux Chrome、趋势图、自定义规则、分享卡片
- [ ] v0.3: Firefox、匿名贡献、高级洞察
- [ ] v1.0: MCP Server、PyPI 发布、社区运营

## 许可

MIT
