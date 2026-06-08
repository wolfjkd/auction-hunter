# 数据模型定义
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import json

@dataclass
class AuctionData:
    """竞价数据模型"""
    stock_code: str
    stock_name: str
    market: str
    timestamp: datetime
    auction_price: float
    auction_volume: int
    bid_prices: List[float]
    ask_prices: List[float]
    bid_volumes: List[int]
    ask_volumes: List[int]
    quote_data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuctionData':
        """从字典创建实例"""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

@dataclass
class AuctionSignal:
    """竞价信号模型"""
    stock_code: str
    stock_name: str
    signal_time: datetime
    signal_type: str  # 'strong_buy', 'weak_buy', 'neutral', 'weak_sell', 'strong_sell'
    signal_score: float  # 0-100分
    signal_emoji: str  # 🔴🟡⚪
    signal_text: str  # 信号描述
    predicted_open_price: float
    confidence: float  # 预测置信度
    analysis_details: Dict[str, Any]  # 分析详情
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['signal_time'] = self.signal_time.isoformat()
        return data
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuctionSignal':
        """从字典创建实例"""
        data['signal_time'] = datetime.fromisoformat(data['signal_time'])
        return cls(**data)

@dataclass
class AuctionHistory:
    """竞价历史记录模型"""
    id: Optional[int] = None
    stock_code: str = ""
    stock_name: str = ""
    trade_date: str = ""  # YYYY-MM-DD
    auction_start_price: float = 0.0
    auction_end_price: float = 0.0
    auction_high_price: float = 0.0
    auction_low_price: float = 0.0
    auction_volume: int = 0
    auction_amount: float = 0.0
    open_price: float = 0.0
    signal_type: str = ""
    signal_score: float = 0.0
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuctionHistory':
        """从字典创建实例"""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)

@dataclass
class StockInfo:
    """股票基本信息模型"""
    code: str
    name: str
    market: str  # 'sh' or 'sz'
    industry: str = ""
    sector: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StockInfo':
        """从字典创建实例"""
        return cls(**data)

# 信号类型映射
SIGNAL_TYPES = {
    'strong_buy': {'emoji': '🔴', 'text': '强抢筹', 'color': '#FF0000'},
    'weak_buy': {'emoji': '🟡', 'text': '弱抢筹', 'color': '#FFD700'},
    'neutral': {'emoji': '⚪', 'text': '中性', 'color': '#808080'},
    'weak_sell': {'emoji': '🟡', 'text': '弱出货', 'color': '#FFD700'},
    'strong_sell': {'emoji': '🔴', 'text': '强出货', 'color': '#FF0000'},
}

def get_signal_type(score: float) -> Dict[str, str]:
    """
    根据分数获取信号类型
    
    Args:
        score: 信号分数 (0-100)
        
    Returns:
        Dict: 信号类型信息
    """
    if score >= 80:
        return SIGNAL_TYPES['strong_buy']
    elif score >= 60:
        return SIGNAL_TYPES['weak_buy']
    elif score >= 40:
        return SIGNAL_TYPES['neutral']
    elif score >= 20:
        return SIGNAL_TYPES['weak_sell']
    else:
        return SIGNAL_TYPES['strong_sell']

def create_auction_signal(
    stock_code: str,
    stock_name: str,
    score: float,
    predicted_open: float,
    confidence: float,
    analysis_details: Dict[str, Any]
) -> AuctionSignal:
    """
    创建竞价信号对象
    
    Args:
        stock_code: 股票代码
        stock_name: 股票名称
        score: 信号分数 (0-100)
        predicted_open: 预测开盘价
        confidence: 预测置信度
        analysis_details: 分析详情
        
    Returns:
        AuctionSignal: 竞价信号对象
    """
    signal_info = get_signal_type(score)
    
    return AuctionSignal(
        stock_code=stock_code,
        stock_name=stock_name,
        signal_time=datetime.now(),
        signal_type=signal_info['text'],
        signal_score=score,
        signal_emoji=signal_info['emoji'],
        signal_text=signal_info['text'],
        predicted_open_price=predicted_open,
        confidence=confidence,
        analysis_details=analysis_details
    )