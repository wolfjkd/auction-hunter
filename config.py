# 集合竞价猎手 - 配置文件
import os
from datetime import time

# 项目配置
PROJECT_NAME = "集合竞价猎手"
VERSION = "1.0.0"

# eltdx配置
ELTDX_HOST = "182.118.8.4:7709"
ELTDX_TIMEOUT = 5  # 超时时间（秒）

# 自选股列表（从用户记忆中获取）
WATCHLIST = [
    {"code": "600170", "name": "上海建工", "market": "sh"},
    {"code": "603077", "name": "和邦生物", "market": "sh"},
    {"code": "601868", "name": "中国能建", "market": "sh"},
    {"code": "601390", "name": "中国中铁", "market": "sh"},
    {"code": "000061", "name": "农产品", "market": "sz"},
    {"code": "000560", "name": "我爱我家", "market": "sz"},
]

# 竞价时间配置
AUCTION_START = time(9, 15)  # 9:15
AUCTION_END = time(9, 25)    # 9:25
COLLECTION_INTERVAL = 5      # 采集间隔（秒）

# 信号评分阈值
SIGNAL_THRESHOLDS = {
    "strong_buy": 80,    # 强抢筹
    "weak_buy": 60,      # 弱抢筹
    "neutral": 40,       # 中性
    "weak_sell": 20,     # 弱出货
    "strong_sell": 0,    # 强出货
}

# 评分权重
SCORING_WEIGHTS = {
    "volume_ratio": 0.30,      # 竞价量比
    "price_trend": 0.25,       # 价格趋势
    "cancel_rate": 0.20,       # 撤单率
    "bid_ask_ratio": 0.15,     # 委比变化
    "seal_strength": 0.10,     # 封单力度
}

# 数据库配置
DATABASE_PATH = os.path.join(os.path.dirname(__file__), "data", "auction.db")
CSV_EXPORT_PATH = os.path.join(os.path.dirname(__file__), "data", "exports")

# Web配置
WEB_HOST = "0.0.0.0"
WEB_PORT = 5001
WEB_DEBUG = False

# 推送配置
PUSH_TENCENT_DOCS = True  # 是否推送到腾讯文档

# 日志配置
LOG_LEVEL = "INFO"
LOG_FILE = os.path.join(os.path.dirname(__file__), "logs", "auction.log")

# 确保目录存在
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
os.makedirs(CSV_EXPORT_PATH, exist_ok=True)
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)