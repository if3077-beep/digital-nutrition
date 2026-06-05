# Findings — v0.1 关键记录

> 跨 session 持久化：坑 + 洞察 + 库选型

## 🔴 已修复的坑

| # | 位置 | 症状 | 解决 |
|---|------|------|------|
| 1 | insight.py | `format_duration(0)` 返回 `"0s"` 但期望 `"0m"` | 加 `if seconds == 0` 特判 |
| 2 | classify.py | `m.bilibili.com` 早期想 strip 到 bilibili.com | 设计是保留 subdomain 让 classify 处理 |
| 3 | collect_chrome.py | `_webkit_to_datetime` 返回 UTC aware datetime | 测试用 `tzinfo=timezone.utc` |
| 4 | persona.py | code 50% 触发 learning（应只 strict >50%） | 改测试数据使 code 严格 >50% |
| 5 | main.py | `find_edge_profiles` 不存在但被调用 | 实现 edge profile 查找（用 chrome 路径） |

## 🟡 流程坑

| 坑 | 处理 |
|----|------|
| PowerShell `&&` 不支持 | 用 `;` |
| PowerShell `tail` 不支持 | 用 `Select-Object -Last N` |
| Trae sandbox `.pyc` 警告 | 忽略 |
| pytest 未装 | `pip install pytest --index-url https://mirrors.aliyun.com/pypi/simple/` |
| 16 commit 散乱 | v0.2 改 3 phase 1 commit |
| 93 tests 过度 | v0.2 改 1-2 代表性测试 |
| 长输出堆积 | `\| tail -3` 限制 |

## 🟢 设计洞察

### 7 种人格优先级互斥
code > 50% > learning > 40% > entertainment > 30% > news > 40% > social > 30% > balanced (15-30%) > 多元探索者
**v0.3 候选**：多标签分类（不互斥）

### 浏览器停留 ≠ 真实阅读
Chrome DB 只记 visit 间隔，不区分活跃/挂机。报告顶部已加"估算"提示。

### 域名级粒度有限
`github.com` 默认 learning，但用户可能逛 Issues = work。
**v0.3+ 候选**：子路径规则（`/issues` = work, `/commits` = learning）

## 🛠️ 技术栈

| 库 | 用途 | 评价 |
|----|------|------|
| `jinja2` | 模板 | 标准 |
| `pytest` | 测试 | 必备 |
| ECharts 5 | 可视化 | 本地打包，1MB |
| `http.server` | 本地服务 | 够用 |
| `webbrowser` | 自动开页 | 跨平台 OK |

## 🌍 跨平台路径

- Windows Chrome: `%LOCALAPPDATA%\Google\Chrome\User Data\`
- macOS Chrome: `~/Library/Application Support/Google/Chrome/`
- Linux Chrome: `~/.config/google-chrome/`

## ⏰ WebKit 时间戳

- Epoch: 1601-01-01 00:00:00 UTC
- 公式: `datetime(1601,1,1) + timedelta(microseconds=webkit_us)`
- 注意微秒精度

## 📊 v0.2 候选价值

| 功能 | 价值 | 实施 | v0.2 选 |
|------|------|------|---------|
| 历史对比 | ⭐⭐⭐⭐ | 低 | ✅ |
| 每日趋势图 | ⭐⭐⭐⭐ | 中 | ✅ |
| 趋势洞察 | ⭐⭐⭐ | 低 | ✅ |
| Pipeline 抽象 | ⭐⭐⭐ | 低 | ✅ |
| 自定义规则 | ⭐⭐⭐ | 中 | ⏸️ v0.3 |
| 分享卡片 | ⭐⭐⭐ | 中 | ⏸️ v0.3 |
| Firefox | ⭐⭐ | 中 | ⏸️ v0.3 |
| Linux Chrome 修正 | ⭐⭐ | 低 | ⏸️ v0.3 |
| 顶层 package 重构 | ⭐⭐ | 中 | ⏸️ v0.3 |

## 🔮 未来 TODO

- [ ] v0.3: `sys.path.insert` → 顶层 package 重构
- [ ] v0.3: 浏览器活跃度检测
- [ ] v0.3: 多人格（不互斥）
- [ ] v0.3+: 子路径分类规则
