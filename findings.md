# Findings — Digital Nutrition Label

> 跨 session 记录研究、发现、踩过的坑
> 写于 v0.1 完成后，融合实战经验

---

## v0.1 实战发现

### 🔴 代码层面的坑（已修复 / 仍存在）

#### 1. `format_duration(0)` 边界 case
- **位置**: `scripts/insight.py`
- **症状**: 测试期望 `format_duration(0) == "0m"`，但实现返回 `"0s"`
- **解决**: 加 `if seconds == 0: return "0m"` 特判
- **教训**: 写函数时先想通 0 / None / 空 list 等退化情况

#### 2. `classify_url` 子域名处理
- **位置**: `scripts/classify.py`
- **症状**: 早期版本想 `m.bilibili.com` → `bilibili.com`，但设计是保留子域名让 `classify_url` 处理
- **解决**: `extract_host` 只 strip `www.` 和端口，subdomain 保留
- **教训**: 设计意图要明确写进 plan，别边做边改

#### 3. `_webkit_to_datetime` 时区
- **位置**: `scripts/collect_chrome.py`
- **症状**: 返回 UTC datetime 但测试用 naive datetime
- **解决**: 测试用 `tzinfo=timezone.utc`
- **教训**: 时间函数统一用 aware datetime（带 timezone）

#### 4. `classify_persona` 优先级测试
- **位置**: `scripts/persona.py` + `tests/test_persona.py`
- **症状**: 测试数据 `{code: 5000, learning: 4500}` 想测 code > learning，但 code 不是严格 >50%
- **解决**: 改测试数据 `{code: 6000, learning: 3500}`
- **教训**: 边界条件用 `>` 不是 `>=`，测试数据要算清百分比

#### 5. `sys.path.insert` 重复
- **位置**: 所有 `scripts/*.py`
- **症状**: 每个文件顶部 `sys.path.insert(0, str(Path(__file__).parent))`
- **v0.1 状态**: 保留（已 commit）
- **未来方案**: v0.3 改成 `digital_nutrition/` 顶层 package，去掉 `scripts/` 中间层

---

### 🟡 流程层面的坑

#### 1. PowerShell 不支持 `&&`
- **症状**: `cmd1 && cmd2` 报 "The token '&&' is not a valid statement separator"
- **解决**: 用 `;` 分隔（PowerShell 兼容，bash 也兼容）
- **根因**: PowerShell 用 `;` 而非 `&&`

#### 2. Trae sandbox 警告
- **症状**: 测试时偶发 `TRAE Sandbox Error: hit restricted: .pyc files`
- **影响**: 无，测试照样通过
- **原因**: Trae sandbox 限制访问 Python 安装目录的 `.pyc` 缓存
- **处理**: 忽略警告，关注 exit code 和实际测试结果

#### 3. pytest 不在全局
- **症状**: 第一次跑测试报 `ModuleNotFoundError: No module named 'pytest'`
- **解决**: `python -m pip install pytest --index-url https://mirrors.aliyun.com/pypi/simple/`

#### 4. v0.1 commit 散乱（16 个）
- **症状**: 每个 helper 函数一个 commit
- **影响**: 仓库历史噪声大
- **v0.2 改进**: 每 phase 1 commit（3-5 个 commit 总数）

#### 5. v0.1 测试过度（93 个）
- **症状**: 简单函数也有 4-5 个边界测试
- **v0.2 改进**: 每个函数 1-2 个代表性测试，110+ tests 通过

#### 6. 边界 case 漏考虑导致回滚
- **症状**: `format_duration(0)` 这种零值
- **改进**: 写实现前用 5 分钟想清楚边界

---

### 🟢 设计层面的洞察

#### 1. 7 种人格优先级 vs 互斥
- **设计**: code > 50% > learning > 40% > entertainment > 30% > news > 40% > social > 30% > balanced (15-30%) > 多元
- **观察**: 用户偶尔会同时是"代码机器人"+"学习永动机"（code 50%, learning 45%）
- **解决**: 优先级判断，第一个满足的胜出
- **v0.3 候选**: 多标签分类（不互斥）

#### 2. 浏览器停留时长 ≠ 真实阅读时间
- **风险**: 用户看到 5 小时 bilibili 会惊讶，但实际是开着没关
- **缓解**: 报告顶部加"基于浏览器历史估算"提示
- **现状**: 已实现

#### 3. 域名级分类粒度有限
- **风险**: `github.com` 默认 learning，但用户可能逛 Issues = 工作
- **现状**: 接受此限制
- **v0.3+ 候选**: 子路径规则（如 `/issues` = work）

---

## 技术栈发现

### 库选型

| 库 | 用途 | 评价 |
|----|------|------|
| `jinja2` | 模板 | 必要，标准 |
| `pytest` | 测试 | 必要 |
| ECharts 5 | 可视化 | 本地打包，无 CDN 依赖 |
| 标准库 `http.server` | 本地服务 | 够用，不需要 Flask |
| `webbrowser` | 自动开页 | 跨平台 OK |

### 跨平台兼容性

- Windows Chrome 路径: `%LOCALAPPDATA%\Google\Chrome\User Data\`
- macOS Chrome 路径: `~/Library/Application Support/Google/Chrome/`
- Linux Chrome 路径: `~/.config/google-chrome/`
- 测试用 `monkeypatch` + `tmp_path` 处理

### SQLite WebKit 时间戳

- WebKit epoch: 1601-01-01 00:00:00 UTC
- 转换: `datetime(1601,1,1) + timedelta(microseconds=webkit_us)`
- 注意: 微秒精度

---

## v0.2 路线图（候选功能价值评估）

| 功能 | 价值 | 实施成本 | v0.2 优先级 |
|------|------|----------|------------|
| 历史对比 | ⭐⭐⭐⭐ | 低 | ✅ 已选 |
| 每日趋势图 | ⭐⭐⭐⭐ | 中 | ✅ 已选 |
| 趋势洞察 | ⭐⭐⭐ | 低 | ✅ 已选 |
| 自定义规则 | ⭐⭐⭐ | 中 | ⏸️ v0.3 |
| 分享卡片 | ⭐⭐⭐ | 中 | ⏸️ v0.3 |
| Firefox | ⭐⭐ | 中 | ⏸️ v0.3 |
| Linux Chrome 修正 | ⭐⭐ | 低 | ⏸️ v0.3 |
| 顶层 package 重构 | ⭐⭐ | 中 | ⏸️ v0.3 |

---

## 未来要解决的问题

- [ ] `sys.path.insert` 重复 → v0.3 改顶层 package
- [ ] 浏览器停留时长夸大 → v0.3 加活跃度检测
- [ ] 7 种人格互斥 → v0.3 多标签
- [ ] 子路径分类 → v0.3+ 可选
