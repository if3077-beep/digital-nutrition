---
name: digital-nutrition
description: 生成你的"开发者人格"周报。分析浏览器历史（Chrome/Edge）和 Git 活动，揭示你的时间分配、人格类型和隐藏模式。当用户说"我的周报"、"数字营养"、"时间分析"、"开发者人格"、"我最近在干嘛"时使用。
---

# Digital Nutrition Label

本地运行的开发者自我认知工具。分析你的浏览器历史和 Git 活动，生成"开发者人格"报告。

## 快速使用

```bash
# 安装
pip install -e .

# 生成本周报告
digital-nutrition weekly

# 生成今日报告
digital-nutrition daily
```

报告将自动在浏览器中打开。

## 数据源

| 数据源 | 平台 | 状态 |
|--------|------|------|
| Chrome | Windows, macOS, Linux | ✅ MVP |
| Edge | Windows, macOS | ✅ MVP |
| Firefox | 全平台 | ⏸️ v0.3 |
| Safari | macOS | ⏸️ v0.3 |
| Git | 全平台 | ✅ MVP |

## 输出内容

- **人格类型**：基于时间分配判断的 7 种开发者人格（代码机器人/学习永动机/娱乐至上等）
- **时间分布**：本周各类别时长占比（圆环图）
- **洞察**：3-5 条自然语言洞察（Top 1 类别、时段高峰等）

## 数据隐私

✅ 完全本地运行，无网络请求
✅ 临时数据库读取后立即删除
✅ 不写入浏览器历史
✅ 开源代码，可审计

## 详细参考

按需读取以下文档：

- `references/persona-types.md` — 7 种人格类型详细说明
- `references/insight-patterns.md` — 洞察生成模式说明

## 自定义分类

```bash
# 添加自定义域名分类
echo '{"learning": ["my-tech-blog.com"]}' > ~/.config/digital-nutrition/user_rules.json
```

## 限制

- 浏览器停留时长 ≠ 真实阅读时间（含挂机时间）
- 域名级分类粒度有限（无法判断同一域名的不同用途）
- 准确度依赖浏览器历史和 Git 活动的真实性

## 已知问题

- 浏览器运行时数据库被锁定，工具会自动复制临时副本读取
- 部分 Linux 发行版的 Chrome 路径可能不同
