# 集合竞价猎手 (Auction Hunter)

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.13+-green)
![License](https://img.shields.io/badge/license-MIT-yellow)

> A股集合竞价阶段自动化分析系统，利用eltdx独有竞价数据，实时解析竞价阶段的量价变化，自动识别抢筹/出货信号。

---

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v1.0.0 | 2026-06-08 | 初始版本，完成核心功能开发 |

---

## 项目概述

A股集合竞价阶段（9:15-9:25）是T0交易的黄金窗口。本系统通过自动化分析竞价数据，帮助交易员在开盘前10分钟做出更明智的决策。

### 核心特性

- **实时竞价数据采集**：利用eltdx TDX郑州节点，每5秒采集一次竞价数据
- **五维度信号评分**：竞价量比、价格趋势、撤单率、委比变化、封单力度
- **智能信号识别**：强抢筹🔴、弱抢筹🟡、中性⚪、弱出货🟡、强出货🔴
- **开盘价预测**：基于多种算法的开盘价预测模型
- **Web竞价面板**：实时可视化竞价数据和信号
- **自动推送**：9:24自动推送竞价结论到腾讯文档

---

## 技术架构

```
┌─────────────────────────────────────────────────┐
│                   用户层                         │
│  ┌──────────────┐  ┌──────────────┐             │
│  │  Web竞价面板  │  │ 腾讯文档推送  │             │
│  └──────┬───────┘  └──────┬───────┘             │
├─────────┼──────────────────┼─────────────────────┤
│         │    信号分析引擎    │                     │
│  ┌──────┴──────────────────┴───────┐             │
│  │     AuctionAnalyzer             │             │
│  │  - 竞价轨迹分析                  │             │
│  │  - 撤单行为检测                  │             │
│  │  - 信号评分算法                  │             │
│  │  - 开盘价预测                    │             │
│  └──────────────┬──────────────────┘             │
├─────────────────┼────────────────────────────────┤
│      数据采集层  │                                │
│  ┌──────────────┴──────────────────┐             │
│  │     eltdx TDX郑州节点            │             │
│  │  - 集合竞价数据接口              │             │
│  │  - 实时行情快照                  │             │
│  │  - 历史竞价数据                  │             │
│  └─────────────────────────────────┘             │
├──────────────────────────────────────────────────┤
│                   存储层                         │
│  ┌──────────────┐  ┌──────────────┐             │
│  │  SQLite竞价库 │  │ CSV日志导出   │             │
│  └──────────────┘  └──────────────┘             │
└──────────────────────────────────────────────────┘
```

---

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/wolfjkd/auction-hunter.git
cd auction-hunter
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置自选股

编辑 `config.py` 文件中的 `WATCHLIST` 列表：

```python
WATCHLIST = [
    {"code": "600170", "name": "上海建工", "market": "sh"},
    {"code": "603077", "name": "和邦生物", "market": "sh"},
    {"code": "601868", "name": "中国能建", "market": "sh"},
    # 添加更多股票...
]
```

### 4. 启动Web服务器

```bash
python web/app.py
```

访问 http://localhost:5001 查看看板。

### 5. 生成测试数据（可选）

```bash
python generate_mock_data.py
```

---

## 项目结构

```
auction-hunter/
├── README.md                 # 项目说明
├── requirements.txt          # 依赖包
├── config.py                 # 配置文件
├── generate_mock_data.py     # 模拟数据生成工具
├── core/                     # 核心模块
│   ├── __init__.py
│   ├── collector.py          # 数据采集
│   ├── analyzer.py           # 信号分析
│   ├── scorer.py             # 评分算法
│   ├── predictor.py          # 开盘价预测
│   └── models.py             # 数据模型
├── storage/                  # 存储模块
│   ├── __init__.py
│   ├── database.py           # SQLite操作
│   └── exporter.py           # CSV导出
├── web/                      # Web界面
│   ├── app.py                # Flask应用
│   ├── templates/
│   │   ├── dashboard.html    # 竞价看板
│   │   └── history.html      # 历史查询
│   └── static/
├── push/                     # 推送模块
│   ├── __init__.py
│   └── tencent_docs.py       # 腾讯文档推送
├── scheduler/                # 调度模块
│   ├── __init__.py
│   └── tasks.py              # 定时任务
├── tests/                    # 测试模块
│   ├── __init__.py
│   ├── test_collector.py     # 采集测试
│   └── test_scorer.py        # 评分测试
└── data/                     # 数据目录（运行时生成）
    ├── auction.db            # SQLite数据库
    ├── exports/              # CSV导出
    ├── reports/              # 每日报告
    └── alerts/               # 信号预警
```

---

## 信号评分算法

### 评分维度

| 维度 | 权重 | 说明 |
|------|------|------|
| 竞价量比 | 30% | 竞价成交量 vs 近5日平均竞价量 |
| 价格趋势 | 25% | 9:20-9:25价格变化方向和幅度 |
| 撤单率 | 20% | 9:15-9:20撤单量/总挂单量 |
| 委比变化 | 15% | 委买/委卖比值的变化趋势 |
| 封单力度 | 10% | 开盘价附近的挂单密集度 |

### 信号判定

```
总分 ≥ 80  → 🔴 强抢筹
总分 ≥ 60  → 🟡 弱抢筹
总分 ≥ 40  → ⚪ 中性
总分 ≥ 20  → 🟡 弱出货
总分 < 20  → 🔴 强出货
```

---

## API接口

### 竞价数据

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/auction-data?date=YYYY-MM-DD` | 获取竞价数据 |
| GET | `/api/auction-signals?date=YYYY-MM-DD` | 获取竞价信号 |
| GET | `/api/auction-history/{stock_code}?days=30` | 获取竞价历史 |

### 分析预测

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/collect-auction` | 手动采集竞价数据 |
| POST | `/api/analyze-signals` | 分析竞价信号 |
| POST | `/api/predict-open` | 预测开盘价 |

### 数据导出

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/export-data` | 导出数据到CSV |

### 系统状态

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| GET | `/api/database-stats` | 数据库统计 |
| GET | `/api/daily-report?date=YYYY-MM-DD` | 每日报告 |

---

## 配置说明

### eltdx配置

```python
ELTDX_HOST = "182.118.8.4:7709"  # TDX郑州节点
ELTDX_TIMEOUT = 5                # 超时时间（秒）
```

### 竞价时间配置

```python
AUCTION_START = time(9, 15)  # 9:15
AUCTION_END = time(9, 25)    # 9:25
COLLECTION_INTERVAL = 5      # 采集间隔（秒）
```

### 信号阈值配置

```python
SIGNAL_THRESHOLDS = {
    "strong_buy": 80,    # 强抢筹
    "weak_buy": 60,      # 弱抢筹
    "neutral": 40,       # 中性
    "weak_sell": 20,     # 弱出货
    "strong_sell": 0,    # 强出货
}
```

---

## 开发计划

### v1.0.0 (2026-06-08) ✅

- [x] eltdx竞价数据接口封装
- [x] 竞价数据定时采集（9:15-9:25，每5秒）
- [x] SQLite竞价数据表设计与存储
- [x] 五维度评分算法实现
- [x] 撤单行为检测逻辑
- [x] 开盘价预测模型
- [x] Web竞价实时面板（Flask + Chart.js）
- [x] 9:24自动推送腾讯文档
- [x] 信号分级展示
- [x] 竞价曲线可视化

### v1.1.0 (计划中)

- [ ] 竞价数据历史回测功能
- [ ] 信号准确率统计与优化
- [ ] 多时间框架分析（5分钟/15分钟/30分钟）
- [ ] 自定义信号规则引擎

### v1.2.0 (计划中)

- [ ] 机器学习信号预测模型
- [ ] 实时WebSocket推送
- [ ] 移动端适配
- [ ] 多账户管理

### v2.0.0 (远期)

- [ ] 全市场扫描（4000+股票）
- [ ] 板块联动分析
- [ ] 资金流向深度分析
- [ ] 智能交易建议

---

## 风险与注意事项

| 风险 | 影响 | 应对方案 |
|------|------|---------|
| eltdx竞价接口可能有调用频率限制 | 数据采集不完整 | 控制采集频率（5秒/次），本地缓存 |
| 竞价阶段网络波动 | 数据延迟 | 设置超时重连，记录缺失标记 |
| 信号准确率不达预期 | 误判率高 | 先用历史数据回测，调优参数后再上线 |
| 竞价数据量大 | 存储压力 | 每日竞价数据约1-2MB，SQLite足够 |

---

## 技术栈

| 层次 | 技术选型 |
|------|---------|
| 数据采集 | eltdx (TDX郑州节点 182.118.8.4:7709) |
| 信号分析 | Python (numpy, pandas) |
| Web前端 | Flask + Bootstrap + Chart.js |
| 推送 | 腾讯文档MCP |
| 存储 | SQLite + CSV |
| 定时调度 | APScheduler |

---

## 依赖包

```
eltdx>=1.0.2
numpy>=1.24.0
pandas>=2.0.0
flask>=2.3.0
apscheduler>=3.10.0
requests>=2.31.0
python-dateutil>=2.8.0
matplotlib>=3.7.0
jinja2>=3.1.0
werkzeug>=2.3.0
pytest>=7.0.0
```

---

## 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

**免责声明**：本项目仅供学习研究使用，不构成任何投资建议。股市有风险，投资需谨慎。

---

## 联系方式

- **作者**：wolfjkd
- **GitHub**：https://github.com/wolfjkd/auction-hunter

如有问题或建议，请提交 [Issue](https://github.com/wolfjkd/auction-hunter/issues)。

---

## 致谢

- [eltdx](https://github.com/electkismet/eltdx/) - 通达信A股行情协议Python库
- [Flask](https://flask.palletsprojects.com/) - 轻量级Web框架
- [Chart.js](https://www.chartjs.org/) - 图表库
- [Bootstrap](https://getbootstrap.com/) - 前端UI框架