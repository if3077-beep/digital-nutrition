# Findings — 跨 Session 踩坑记录

> 持久化：坑 + 洞察 + 库选型，给后续 session 参考

## 🔴 已修复的坑

| # | 位置 | 症状 | 解决 |
|---|------|------|------|
| 1 | insight.py | `format_duration(0)` 返回 `"0s"` 但期望 `"0m"` | 加 `if seconds == 0` 特判 |
| 2 | classify.py | `m.bilibili.com` 早期想 strip 到 bilibili.com | 设计是保留 subdomain 让 classify 处理 |
| 3 | collect_chrome.py | `_webkit_to_datetime` 返回 UTC aware datetime | 测试用 `tzinfo=timezone.utc` |
| 4 | persona.py | code 50% 触发 learning（应只 strict >50%） | 改测试数据使 code 严格 >50% |
| 5 | main.py | `find_edge_profiles` 不存在但被调用 | 实现 edge profile 查找（用 chrome 路径） |
| 6 | history.py | 同秒保存导致 filename 冲突 | UUID prefix + mtime 排序 |
| 7 | test_main.py | `monkeypatch.setattr(history_mod, ...)` 不生效 | 改用 `monkeypatch.setenv("USERPROFILE")` |
| 8 | trend.py | `from scripts import trend` 失败 | 加 `sys.path.insert(0, ...)` |
| 9 | scripts/ | 11 个文件都 `sys.path.insert(0, ...)` | **v0.5 顶层 package 化彻底解决** |

## 🟡 流程坑

| 坑 | 处理 |
|----|------|
| PowerShell `&&` 不支持 | 用 `;` |
| PowerShell `tail` 不支持 | 用 `Select-Object -Last N` |
| Trae sandbox `.pyc` 警告 | 忽略 |
| pytest 未装 | `pip install pytest --index-url https://mirrors.aliyun.com/pypi/simple/` |
| 16 commit 散乱（v0.1） | v0.2 改 3 phase 1 commit |
| 93 tests 过度（v0.1） | v0.2/v0.5 改 1-2 代表性测试 |
| 长输出堆积 | `\| Select-Object -Last 3` 限制 |
| 自己造 SQLite adapter | v0.5 改依赖 `browser-history` |
| 跨 session 状态丢失 | AGENTS.md + task_plan.md + findings.md + progress.md 4 文件 |

## 🟢 设计洞察

### 7 种人格优先级互斥
code > 50% > learning > 40% > entertainment > 30% > news > 40% > social > 30% > balanced (15-30%) > 多元探索者

### 浏览器停留 ≠ 真实阅读
Chrome DB 只记 visit 间隔，不区分活跃/挂机。报告顶部已加"估算"提示。
真实 AFK 检测需 OS 钩子（Windows API / macOS Quartz / X11/Wayland），超出 v0.5 范围。

### 域名级粒度有限
`github.com` 默认 learning，但用户可能逛 Issues = work。
**v0.5+ 候选**：子路径规则（`/issues` = work, `/commits` = learning）— 暂不实现

## 🛠️ 技术栈

| 库 | 用途 | 评价 |
|----|------|------|
| `jinja2` | 模板 | 标准 |
| `pytest` | 测试 | 必备 |
| ECharts 5 | 可视化 | 本地打包，1MB |
| `http.server` | 本地服务 | 够用 |
| `webbrowser` | 自动开页 | 跨平台 OK |
| `browser-history` (v0.5) | 多浏览器历史 | 0 依赖，20KB，支持 8+ 浏览器 |
| `browser_history.get_history()` | 一次拿所有浏览器 | API 极简 |

## 🌍 跨平台路径

- Windows Chrome: `%LOCALAPPDATA%\Google\Chrome\User Data\`
- macOS Chrome: `~/Library/Application Support/Google/Chrome/`
- Linux Chrome: `~/.config/google-chrome/`
- Firefox / Edge / Safari / Arc / Zen / Brave / Vivaldi / Opera: 由 `browser-history` 库自动处理（v0.5 起）

## ⏰ WebKit 时间戳

- Epoch: 1601-01-01 00:00:00 UTC
- 公式: `datetime(1601,1,1) + timedelta(microseconds=webkit_us)`
- 注意微秒精度
- v0.5 起：Chrome/Edge 用 browser-history 库自动处理

## 📊 v0.5 决策记录

| 决策 | 选 | 不选 | 理由 |
|------|----|----|------|
| 顶层 package 化 | ✅ flat-layout（`digital_nutrition/` 在根） | ❌ src-layout | 避免 v0.1→v0.2→v0.5 三次重命名 |
| 数据源实现 | ✅ 依赖 `browser-history` | ❌ 自写 SQLite adapter | 0 依赖、20KB、支持 8+ 浏览器 |
| 规则引擎 | ❌ 推迟 v0.5+ | — | v0.2 dict 合并够用，单次 report 价值有限 |
| 多维度人格 | ❌ 推迟 v0.5+ | — | v0.2 的 7 种够用 |
| 分享卡 | ✅ 浏览器端 canvas | ❌ Pillow / Playwright | 零新依赖，所见即所得 |
| AFK 检测 | ❌ 推迟 v0.5+ | — | 需 OS 钩子，超范围 |
| Firefox | ✅ v0.5 顺便支持（via browser-history） | ❌ 单独实现 | 白送 |
| 中间版本规划 | ❌ 砍掉 v0.6/v0.7/v1.0 详细计划 | — | 用户决定只做 v0.5 |

## 🔮 未来 TODO（v0.5+）

v0.5 完成后可考虑：
- 规则引擎 + 用户规则 CLI
- 多维度人格 + 多标签
- 多周期对比（7d / 30d / 90d）
- 真实 AFK 检测（OS 钩子）
- Chrome 浏览器扩展（持续追踪）
- 本地 server + REST API + buckets
- Dropbox 同步
- Web UI dashboard
- 1.0 发布
