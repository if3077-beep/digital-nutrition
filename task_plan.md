# Digital Nutrition Label — 3 个月 final 规划

> **2026-06-05 v3 final**（基于 v1→v2→v3 反思 + 6 个相似项目研究）
> **目标**：3 个月内从 v0.2 走到 v1.0，单人项目，每周 3-5 小时投入
> **节奏**：1 release = 1 phase = 1 commit / 多 commit，按风险分

---

## 🗺️ 路线图（3 个月 / 12 周 / 4 个 release）

```
Week  1  2  3  4  5  6  7  8  9  10 11 12
      ├──v0.5──┤
              ├──────v0.6───────┤
                              ├──v0.6.1─┤
                                      ├──────v0.7───────┤
                                                      ├────v1.0────┤
```

| Release | 周次 | 主题 | 关键交付 | 工作量 |
|---------|------|------|----------|--------|
| **v0.5** | W1 | 架构现代化 | 顶层 package + browser-history 集成 + PNG 分享 + JSON 导出 | 5h |
| **v0.6** | W2-W5 | 数据丰富 + 实时 | Chrome 扩展 + 真实 AFK（OS 钩子）+ 多维度人格 | 16-20h |
| **v0.7** | W6-W9 | 平台化骨架 | local server (FastAPI) + buckets + REST API + CLI 客户端 | 16-20h |
| **v1.0** | W10-W12 | 整合 + 体验 | 同步（Dropbox） + Web UI（基础） + 完整文档 + 1.0 发布 | 12-15h |

**总工作量**：~50-60h（v0.2 用了 2h / 11 模块作基线，3 个月节奏合理）

---

## 📦 v0.5（W1 / 5h / 1 周内）

**核心**：站在巨人肩膀上。v0.2 已有 11 模块 / 112 tests，v0.5 不重写，只**升级架构 + 删冗余 + 加分享/导出**。

### 1.1 顶层重构（3h）

- 改 `pyproject.toml`: `[project.scripts] digital_nutrition = "digital_nutrition.cli:main"`
- 把 `scripts/*.py` 平移成 `digital_nutrition/*.py`（保留 11 个 v0.2 模块，文件名不变）
- 创建子目录：
  ```
  digital_nutrition/
    cli.py (原 main.py)
    sources/  (空目录, v0.6 用)
    history/  (从 history.py 拆出 export.py)
    report/   (从 report_generator.py 拆出 share.py)
  ```
- 删 `scripts/collect_chrome.py` / `scripts/collect_edge.py`（被 browser-history 替代）
- 新增 `digital_nutrition/sources/browser.py`：包装 `browser-history` 的 `get_history()`
- 删 v0.1 的 `sys.path.insert` 散弹（11 个文件）
- **删除 ~200 行代码**

### 1.2 PNG 分享卡（1h）

- 浏览器端方案：在 `report.html.j2` 加按钮 → `<canvas>` 绘制 → `toDataURL('image/png')` → 触发下载
- 不引入 Pillow / Playwright 等新依赖
- 模板画 1200×630 卡片（标题 + 人格 + 7 维度条 + 时间戳）

### 1.3 JSON 导出（1h）

- 新增 `digital_nutrition/history/export.py`: `export_all_reports(output_path) -> Path`
- CLI 子命令 `digital-nutrition export --output backup.json`
- 包含所有历史报告的元数据 + by_category + insights + persona

### 完成定义
- [ ] `pip install -e .` 成功
- [ ] `digital-nutrition weekly` 与 v0.2 输出**视觉一致**（人格/洞察/图表/趋势全部保留）
- [ ] `digital-nutrition export` 输出 JSON 可读
- [ ] 浏览器点 "保存分享卡" 下载 PNG
- [ ] 40-60 tests pass（v0.2 是 112，v0.5 简化后目标减半）
- [ ] 1 commit: `refactor: top-level package + browser-history + share/export`

---

## 📡 v0.6（W2-W5 / 16-20h / 4 周）

**核心**：从"我跑一下报告" → "我装上扩展后**自动持续追踪**"。这是用户粘性的关键节点。

### 2.1 Chrome 扩展（W2-W3 / 8-10h）

- Manifest V3 扩展
- 后台 Service Worker 定时（每 30s）发 heartbeat 到 local HTTP server
- 数据流：`chrome.tabs.onActivated` + `chrome.history.onVisited` → 队列 → 本地 API
- **单 Chrome 优先**（Firefox 后做，见 v0.6.1）
- 难点：manifest V3 的 Service Worker 限制、permissions、content security policy

### 2.2 真实 AFK 检测（W4 / 4-6h）

- Windows: `ctypes` 调 `GetLastInputInfo` 检测空闲时间
- macOS: `Quartz.CoreGraphics` via `pyobjc`（如果装得上的话）
- Linux: 跳过（用户少，复杂度高）
- 数据模型加 `is_afk: bool` 字段
- v0.5 阶段先用 `ctypes` Windows 验证可行性

### 2.3 多维度人格（W5 / 4h）

- 实现 `PersonaScore` dataclass（v0.5 v3 文档设计）
- 7 个维度 0-1 评分
- 主标签 = 最高分维度 + 阈值（v0.2 的 7 种人格逻辑保留）
- 报告 HTML 加"维度条"图

### 完成定义
- [ ] Chrome 扩展装上后，能在 local server 看到心跳数据
- [ ] AFK 检测能区分"真挂机" vs "切走一会"
- [ ] 人格报告显示 7 维度评分
- [ ] 60-80 tests pass
- [ ] 3-4 commits: `feat: chrome extension` / `feat: afk detection` / `feat: multi-dim persona`

### v0.6.1（降级方案 / 如果延期）

- 浏览器扩展做**简化版**：只发 URL，duration 用 `performance.now()` 差值
- 实在做不出 → 只做 "本地数据增强"（不要扩展）
- AFK 跨平台做不出 → 只做 Windows
- 决策点：W4 周末评估

---

## 🏗️ v0.7（W6-W9 / 16-20h / 4 周）

**核心**：从"本地工具" → "本地 server + CLI/扩展客户端"。让数据可查询、可多客户端。

### 3.1 local server（W6-W7 / 8h）

- FastAPI 框架
- 单进程，跑在 `127.0.0.1:5600`（ActivityWatch 默认端口）
- 心跳 API：`POST /api/heartbeat` 接收 `{timestamp, source, data}`
- 数据存储：SQLite（不动用 Postgres）
- 启动：CLI 启动 server + 浏览器扩展配置

### 3.2 buckets + REST API（W8-W9 / 8-10h）

- Buckets: 类似 ActivityWatch 的概念
  - `aw-watcher-browser-chrome` bucket：浏览器 URL/title/timestamp
  - `aw-watcher-afk` bucket：AFK 状态
  - `aw-watcher-window` bucket：当前窗口（v0.7 不实现，记录设计）
- API endpoints:
  - `GET /api/buckets` 列出所有 buckets
  - `GET /api/buckets/{id}/events?start=&end=` 查事件
  - `POST /api/query` 跑 query（ActivityWatch 风格）
  - `POST /api/heartbeat` 接收 watcher 心跳
- CLI 客户端 `digital-nutrition query` 包装 REST API

### 3.3 Query language（W9 / 2-4h）

- 简单声明式 query，类似 AW：
  ```python
  query = "events = query_bucket('aw-watcher-browser-chrome'); RETURN = count_by(events, 'data.url')"
  ```
- 不做完整 AW QL（mini 版本即可：filter / groupby / count）

### 完成定义
- [ ] `digital-nutrition serve` 启动 local server
- [ ] 浏览器扩展能发心跳 → server 收到
- [ ] `digital-nutrition query "..."` 能查数据
- [ ] 80-100 tests pass
- [ ] 2-3 commits: `feat: local server + buckets` / `feat: query language`

### v0.7.1（降级方案 / 如果延期）

- server 跨平台做不出 → 只做 Windows
- query language 难做 → 砍掉，只做固定 API endpoints
- 决策点：W8 周末评估

---

## 🚀 v1.0（W10-W12 / 12-15h / 3 周）

**核心**：从"开发版" → "可发布版"。补完体验 + 文档 + 发布。

### 4.1 同步（W10 / 4-5h）

- Dropbox / iCloud / OneDrive 文件夹同步
- 历史报告 JSON 同步到云端文件夹
- 报告 HTML 也同步（用户多设备看）
- **不做自定义 sync 协议**——靠系统文件同步

### 4.2 基础 Web UI（W11 / 5-6h）

- 在 local server 基础上，加 `GET /` 路由
- 简单 HTML + ECharts dashboard
- 类似 v0.2 的报告 HTML，但**实时**（不再只 weekly/daily）
- 时间线 + 类别饼图 + 当前状态

### 4.3 文档 + 发布（W12 / 3-4h）

- 完整 README（功能 + 安装 + 用法 + 截图）
- CHANGELOG（v0.1 → v1.0 全记录）
- 录一个 1 分钟 demo GIF
- PyPI 发布（可选，时间紧就只发 GitHub Releases）
- 写一个发布博客

### 完成定义
- [ ] v1.0 tag + GitHub Release
- [ ] 用户装上 Chrome 扩展后，能看到自己的"实时"数字营养报告
- [ ] 历史数据能同步到云盘
- [ ] 100-120 tests pass（恢复 v0.2 水平）
- [ ] 1 commit: `release: v1.0`

---

## 🔍 合理性 + 可行性检验

### 合理性（做的对不对？）

| 检验项 | 通过 | 证据 |
|--------|------|------|
| 路线图连贯性 | ✅ | v0.5 解决"工具现代化"，v0.6 解决"实时数据"，v0.7 解决"可查询"，v1.0 解决"发布" |
| 价值递增 | ✅ | 每一版都比上一版**有明确的新能力**，不是堆 feature |
| YAGNI | ✅ | 8 个 v0.3 候选有 6 个推迟到 v0.6+，4 个直接砍掉 |
| 与相似项目对比 | ✅ | v1.0 ≈ ActivityWatch 5 年前水平，可达；不自建 Web Extension Store |
| 测试节奏 | ✅ | 每版 +20 tests，v0.5 减半是因为删了 200 行 SQLite adapter |

### 可行性（做得完吗？）

| 检验项 | 评估 | 风险 |
|--------|------|------|
| 工作量 | 50-60h / 3 个月 / 每周 3-5h | ✅ 可行 |
| 技术栈 | Python + FastAPI + Chrome MV3 + Jinja2 + SQLite | ✅ 全是熟悉技术 |
| 外部依赖 | browser-history (0 依赖) + FastAPI + 少量 npm（扩展） | ✅ 无阻塞 |
| 平台覆盖 | 3 平台目标，v0.6 跨平台 AFK 可能延期 | ⚠️ 中等风险 |
| 个人时间 | 假设每周稳定投入 3-5h | ⚠️ 受其他项目影响 |
| Chrome 扩展 | Manifest V3 有 learning curve | ⚠️ 高风险 |
| 发布 v1.0 | 3 周内 polish 完整 UI 较紧 | ⚠️ 中等风险 |

### 风险等级总览

| 风险点 | 等级 | 缓解 |
|--------|------|------|
| Chrome 扩展（v0.6 最重） | 🟡 高 | v0.6.1 降级方案：简化版（不发 duration） |
| 跨平台 AFK（v0.6） | 🟡 中 | 先 Windows，macOS 后做，Linux 砍 |
| FastAPI + buckets（v0.7） | 🟢 低 | 仿 ActivityWatch 模型，文档全 |
| Web UI（v1.0） | 🟡 中 | v1.0.1 降级：只做 CLI dashboard，不做 Web |
| 总体延期 | 🟡 中 | 3 个月内 4 release 紧，留 v0.X.1 降级空间 |

---

## 🪞 反思（这个规划还有什么问题？）

### 反思 1：v0.6 浏览器扩展是最大风险

- Chrome MV3 Service Worker 限制很多（不能 long-running）
- 学习曲线 + 调试工具不友好
- **缓解**：v0.6.1 准备简化版（只发 URL，duration 客户端算）

### 反思 2：v0.7 server 是否真有必要？

- ActivityWatch 已有完整 server，我们再做一遍价值？
- 但 v0.7 server 集成**我们的 v0.5 + v0.6 能力**（规则、人格、报告）——比 AW 强
- **决策点**：W5 周末评估"做 v0.7 server 还是用 AW"

### 反思 3：v1.0 Web UI 时间不够

- 3 周 polish 完整 UI 太紧
- 用户可能只用 CLI 不需要 Web
- **缓解**：v1.0.1 降级 — 砍 Web UI，v1.0 = "完整 CLI 工具"

### 反思 4：3 个月是否能 100% 完成？

- 任何版本延期 1 周 → 整个路线图延期
- **应对**：每月评估一次，必要时砍 1-2 个 release 不做

### 反思 5：v0.5 → v0.6 跨度过大

- v0.5 = 工具升级（5h）
- v0.6 = 实时数据 + 浏览器扩展（20h）
- 中间没有"小步快跑"的过渡版
- **缓解**：W4 周末评估"是否需要在 v0.5 和 v0.6 之间插入 v0.5.1（小数据增强）"

### 反思 6：测试数量波动不合理

- v0.5: 40-60 tests（减半）
- v0.6: 60-80 tests
- v0.7: 80-100 tests
- v1.0: 100-120 tests
- **解释**：v0.5 删了 200 行代码，测试减半合理；后续每版 +20 tests 是稳态

---

## ✅ 决策点（要用户拍板的事）

| 决策 | 选项 | 推荐 |
|------|------|------|
| v0.5 立即开工？ | 是 / 否 | 是 |
| 浏览器扩展先 Chrome 还是先 Firefox？ | Chrome / Firefox | Chrome（市场份额大） |
| v0.7 server 还是要复用 ActivityWatch？ | 自建 / 复用 AW | 自建（差异化能力） |
| v1.0 是否发 PyPI？ | 是 / 否 / 仅 GitHub Release | 仅 GitHub Release（节省时间） |

---

## 📋 下一步（v0.5 Phase 1 准备开工）

1. **本周内**（W1）：
   - 创建 v0.5 顶层 package 结构
   - 集成 `browser-history` 依赖
   - 实现 `BrowserSource` + `GitSource`
   - 删 `collect_chrome.py` / `collect_edge.py`
   - 加 `export` subcommand + `share` 按钮
   - 跑通所有现有 tests（v0.2 112 → v0.5 40-60）
2. **W1 周末**：
   - 评估"是否需要 v0.5.1 过渡版"
   - 决定 v0.6 浏览器扩展的具体范围

3. **W2 开始 v0.6**：Chrome 扩展脚手架

**今天就能开始**：v0.5 Phase 1 / 顶层重构 / 5h 工作量。

---

## 🗂️ 关键文件指引

- 📄 [v0.5 设计文档（含 v1/v2/v3 思考过程）](file:///C:/Users/zz/Desktop/TRAE/过程文件/2026-06-04_数字营养标签/digital-nutrition/docs/superpowers/specs/2026-06-05-v0.5-design.md)
- 📊 [findings.md — 跨 session 持久化踩坑记录](file:///C:/Users/zz/Desktop/TRAE/过程文件/2026-06-04_数字营养标签/digital-nutrition/findings.md)
- 📋 [AGENTS.md — 跨 session 指导手册](file:///C:/Users/zz/Desktop/TRAE/过程文件/2026-06-04_数字营养标签/digital-nutrition/AGENTS.md)
- 📈 [progress.md — session log](file:///C:/Users/zz/Desktop/TRAE/过程文件/2026-06-04_数字营养标签/digital-nutrition/progress.md)
