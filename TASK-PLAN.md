# 集合竞价猎手 - 任务拆解与开发指令

> **项目目录**：`C:\Users\wolfj\WorkBuddy\Claw\auction-hunter\`
> **工作目录**：同上（所有任务统一使用此目录）

---

## 🔧 需要的连接器

| 连接器 | 状态 | 用途 |
|--------|------|------|
| tdx-connector (通达信) | ✅ 已连接 | 竞价数据采集、实时行情 |
| tencent-docs (腾讯文档) | ✅ 已连接 | 竞价报告推送 |

---

## 🛠️ 需要的技能

| 技能 | 用途 | 是否已安装 |
|------|------|-----------|
| tencent-finance | 腾讯行情数据（备用数据源） | ✅ |
| data-analyst | 数据分析与可视化 | ✅ |
| tencent-docs | 报告推送到腾讯文档 | ✅ |
| skill-creator | 将完成的工作保存为可复用技能 | ✅ |

---

## 📋 任务拆解（共11个任务，3个阶段）

### 阶段一：数据采集层（4个任务）

#### Task 1：项目初始化
- **指令**：在 `C:\Users\wolfj\WorkBuddy\Claw\auction-hunter\` 目录下创建项目结构，包括 `core/`、`storage/`、`web/`、`push/`、`scheduler/`、`tests/` 子目录，以及 `requirements.txt`、`config.py`、`README.md` 基础文件
- **技能**：无（基础文件操作）
- **连接器**：无
- **产出**：项目骨架

#### Task 2：eltdx竞价数据接口封装
- **指令**：基于通达信连接器（tdx-connector），编写 `core/collector.py`，封装集合竞价数据采集接口。功能：(1) 连接TDX郑州节点 182.118.8.4:7709 (2) 获取单只股票的集合竞价数据（价格、成交量、委买委卖）(3) 支持批量获取多只股票 (4) 异常处理和自动重连
- **技能**：无（使用tdx-connector的MCP接口）
- **连接器**：tdx-connector
- **产出**：`core/collector.py`

#### Task 3：竞价数据定时采集与SQLite存储
- **指令**：编写定时采集调度器和SQLite存储模块。(1) `storage/database.py` - SQLite数据库操作，表结构：auction_snapshots（快照表）、auction_signals（信号表）(2) `scheduler/tasks.py` - 定时任务，9:15-9:25每5秒采集一次竞价数据 (3) 支持历史数据查询
- **技能**：无
- **连接器**：tdx-connector
- **产出**：`storage/database.py`、`scheduler/tasks.py`

#### Task 4：竞价数据采集功能测试
- **指令**：编写测试用例，验证竞价数据采集和存储功能。(1) 测试eltdx连接 (2) 测试竞价数据获取 (3) 测试SQLite读写 (4) 用自选股列表做端到端测试
- **技能**：无
- **连接器**：tdx-connector
- **产出**：`tests/test_collector.py`、`tests/test_database.py`

---

### 阶段二：信号分析引擎（4个任务）

#### Task 5：五维度竞价评分算法
- **指令**：编写 `core/scorer.py`，实现五维度竞价信号评分算法。维度：(1) 竞价量比（30%权重）- 竞价成交量 vs 近5日平均 (2) 价格趋势（25%）- 9:20-9:25价格变化 (3) 撤单率（20%）- 撤单量/总挂单量 (4) 委比变化（15%）- 委买/委卖比值 (5) 封单力度（10%）- 开盘价附近挂单密集度。输出：0-100分，对应强出货→强抢筹五档信号
- **技能**：无
- **连接器**：无
- **产出**：`core/scorer.py`

#### Task 6：撤单行为检测模块
- **指令**：编写 `core/cancel_detector.py`，检测9:15-9:20期间的撤单行为。(1) 跟踪挂单变化，识别大单撤退 (2) 计算撤单率 (3) 标记异常撤单模式（如9:19大量撤单）
- **技能**：无
- **连接器**：tdx-connector
- **产出**：`core/cancel_detector.py`

#### Task 7：开盘价预测模型
- **指令**：编写 `core/predictor.py`，基于竞价数据预测开盘价区间。(1) 输入：竞价阶段的价格、成交量、委买委卖 (2) 输出：预测开盘价区间（高/中/低三个值）(3) 用历史竞价数据验证准确率
- **技能**：无
- **连接器**：无
- **产出**：`core/predictor.py`

#### Task 8：信号准确率回测
- **指令**：编写回测模块 `tests/test_backtest.py`，用历史数据验证信号准确率。(1) 模拟历史竞价数据 (2) 运行评分算法 (3) 对比实际开盘后30分钟走势 (4) 统计各信号档位的准确率 (5) 输出回测报告
- **技能**：data-analyst
- **连接器**：无
- **产出**：`tests/test_backtest.py`、回测报告

---

### 阶段三：输出与界面（3个任务）

#### Task 9：Web竞价实时面板
- **指令**：基于Flask开发Web竞价看板 `web/app.py`。(1) 实时展示自选股竞价数据 (2) 竞价曲线图（Chart.js）(3) 信号颜色标识（红=抢筹、绿=出货）(4) WebSocket实时推送 (5) 响应式布局，适配不同屏幕
- **技能**：无（Flask Web开发）
- **连接器**：无
- **产出**：`web/app.py`、`web/templates/dashboard.html`、`web/static/`

#### Task 10：腾讯文档竞价报告推送
- **指令**：编写 `push/tencent_docs.py`，在9:24自动推送竞价结论到腾讯文档。(1) 生成Markdown格式报告（自选股竞价信号、开盘价预测）(2) 调用腾讯文档MCP创建文档 (3) 推送链接
- **技能**：tencent-docs
- **连接器**：tencent-docs
- **产出**：`push/tencent_docs.py`

#### Task 11：系统集成与定时调度
- **指令**：整合所有模块，配置定时调度。(1) `main.py` - 主程序入口 (2) 整合采集→分析→推送流程 (3) 配置定时任务（每天9:15自动启动）(4) 日志记录 (5) 异常告警 (6) 端到端测试
- **技能**：无
- **连接器**：tdx-connector、tencent-docs
- **产出**：`main.py`、完整的可运行系统

---

## 🚀 推荐执行顺序

```
Task 1（项目初始化）
    ↓
Task 2（eltdx接口）→ Task 3（存储）→ Task 4（测试）
    ↓
Task 5（评分算法）→ Task 6（撤单检测）→ Task 7（开盘价预测）→ Task 8（回测）
    ↓
Task 9（Web面板）→ Task 10（推送）→ Task 11（集成）
```

**可并行的任务**：
- Task 2 和 Task 5 可并行（数据层 vs 分析层）
- Task 9 和 Task 10 可并行（Web vs 推送）

---

## 📝 每个任务的WorkBuddy创建模板

创建任务时使用以下格式：

```
【工作目录】C:\Users\wolfj\WorkBuddy\Claw\auction-hunter\
【任务描述】（对应上面每个Task的"指令"内容）
【参考文件】@开发计划书.md（如果需要上下文）
```
