# eltdx竞价数据采集模块
import time
import logging
from datetime import datetime, time as dt_time
from typing import Dict, List, Optional, Any
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import ELTDX_HOST, ELTDX_TIMEOUT, WATCHLIST, AUCTION_START, AUCTION_END, COLLECTION_INTERVAL

logger = logging.getLogger(__name__)

class AuctionCollector:
    """集合竞价数据采集器"""
    
    def __init__(self, host: str = ELTDX_HOST):
        """
        初始化采集器
        
        Args:
            host: eltdx服务器地址
        """
        self.host = host
        self.client = None
        self.connected = False
        
    def connect(self) -> bool:
        """
        连接到eltdx服务器
        
        Returns:
            bool: 连接是否成功
        """
        try:
            from eltdx import Client
            self.client = Client(host=self.host)
            # 测试连接
            test_quote = self.client.get_quote("600170")
            if test_quote:
                self.connected = True
                logger.info(f"成功连接到eltdx服务器: {self.host}")
                return True
            else:
                logger.error("连接测试失败")
                return False
        except Exception as e:
            logger.error(f"连接eltdx服务器失败: {e}")
            return False
    
    def get_auction_data(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        获取单只股票的竞价数据
        
        Args:
            stock_code: 股票代码
            
        Returns:
            Dict: 竞价数据字典
        """
        if not self.connected or not self.client:
            logger.error("未连接到eltdx服务器")
            return None
        
        try:
            # 获取竞价数据
            auction_data = self.client.get_auction_data(stock_code)
            if not auction_data:
                logger.warning(f"获取{stock_code}竞价数据失败")
                return None
            
            # 获取实时行情快照
            quote = self.client.get_quote(stock_code)
            
            # 整理数据
            result = {
                "stock_code": stock_code,
                "timestamp": datetime.now(),
                "auction_price": auction_data.get("price", 0),
                "auction_volume": auction_data.get("volume", 0),
                "bid_price": auction_data.get("bid_price", []),
                "ask_price": auction_data.get("ask_price", []),
                "bid_volume": auction_data.get("bid_volume", []),
                "ask_volume": auction_data.get("ask_volume", []),
                "quote": quote,
                "raw_data": auction_data
            }
            
            logger.debug(f"获取{stock_code}竞价数据成功")
            return result
            
        except Exception as e:
            logger.error(f"获取{stock_code}竞价数据异常: {e}")
            return None
    
    def get_realtime_quote(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        获取实时行情快照
        
        Args:
            stock_code: 股票代码
            
        Returns:
            Dict: 实时行情数据
        """
        if not self.connected or not self.client:
            logger.error("未连接到eltdx服务器")
            return None
        
        try:
            quote = self.client.get_quote(stock_code)
            if quote:
                return {
                    "stock_code": stock_code,
                    "timestamp": datetime.now(),
                    "price": quote.get("price", 0),
                    "open": quote.get("open", 0),
                    "high": quote.get("high", 0),
                    "low": quote.get("low", 0),
                    "volume": quote.get("volume", 0),
                    "amount": quote.get("amount", 0),
                    "bid1_price": quote.get("bid1_price", 0),
                    "bid1_volume": quote.get("bid1_volume", 0),
                    "ask1_price": quote.get("ask1_price", 0),
                    "ask1_volume": quote.get("ask1_volume", 0),
                    "raw_data": quote
                }
            return None
        except Exception as e:
            logger.error(f"获取{stock_code}实时行情异常: {e}")
            return None
    
    def collect_auction_batch(self, stock_list: List[Dict] = None, force: bool = False) -> List[Dict[str, Any]]:
        """
        批量采集竞价数据
        
        Args:
            stock_list: 股票列表，默认使用配置的自选股
            force: 是否强制采集（忽略竞价时间限制）
            
        Returns:
            List[Dict]: 竞价数据列表
        """
        if stock_list is None:
            stock_list = WATCHLIST
        
        # 非竞价时间且未强制采集时，使用实时行情接口
        if not force and not self.is_auction_time():
            logger.info("当前不在竞价时间内，使用实时行情接口")
            return self.collect_realtime_batch(stock_list)
        
        results = []
        for stock in stock_list:
            stock_code = stock["code"]
            data = self.get_auction_data(stock_code)
            if data:
                data["stock_name"] = stock["name"]
                data["market"] = stock["market"]
                results.append(data)
        
        logger.info(f"批量采集完成，成功获取{len(results)}/{len(stock_list)}只股票数据")
        return results
    
    def collect_realtime_batch(self, stock_list: List[Dict] = None) -> List[Dict[str, Any]]:
        """
        批量采集实时行情数据（非竞价时间使用）
        
        Args:
            stock_list: 股票列表，默认使用配置的自选股
            
        Returns:
            List[Dict]: 实时行情数据列表
        """
        if stock_list is None:
            stock_list = WATCHLIST
        
        results = []
        for stock in stock_list:
            stock_code = stock["code"]
            quote = self.get_realtime_quote(stock_code)
            if quote:
                # 转换为竞价数据格式
                data = {
                    "stock_code": stock_code,
                    "stock_name": stock["name"],
                    "market": stock["market"],
                    "timestamp": quote["timestamp"],
                    "auction_price": quote["price"],
                    "auction_volume": quote["volume"],
                    "bid_price": [quote.get("bid1_price", 0)],
                    "ask_price": [quote.get("ask1_price", 0)],
                    "bid_volume": [quote.get("bid1_volume", 0)],
                    "ask_volume": [quote.get("ask1_volume", 0)],
                    "quote": quote,
                    "is_realtime": True  # 标记为实时数据
                }
                results.append(data)
        
        logger.info(f"实时行情采集完成，成功获取{len(results)}/{len(stock_list)}只股票数据")
        return results
    
    def is_auction_time(self) -> bool:
        """
        检查当前是否在竞价时间内
        
        Returns:
            bool: 是否在竞价时间内
        """
        now = datetime.now().time()
        return AUCTION_START <= now <= AUCTION_END
    
    def collect_auction_period(self, duration_minutes: int = 10) -> List[Dict[str, Any]]:
        """
        采集整个竞价周期的数据
        
        Args:
            duration_minutes: 采集持续时间（分钟）
            
        Returns:
            List[Dict]: 竞价数据列表
        """
        if not self.is_auction_time():
            logger.warning("当前不在竞价时间内")
            return []
        
        all_data = []
        start_time = datetime.now()
        end_time = start_time.replace(second=start_time.second + duration_minutes * 60)
        
        logger.info(f"开始采集竞价数据，持续{duration_minutes}分钟")
        
        while datetime.now() < end_time and self.is_auction_time():
            batch_data = self.collect_auction_batch()
            all_data.extend(batch_data)
            
            # 等待下一次采集
            time.sleep(COLLECTION_INTERVAL)
        
        logger.info(f"竞价数据采集完成，共采集{len(all_data)}条记录")
        return all_data
    
    def disconnect(self):
        """断开连接"""
        if self.client:
            try:
                # eltdx客户端可能没有显式的disconnect方法
                self.client = None
                self.connected = False
                logger.info("已断开eltdx连接")
            except Exception as e:
                logger.error(f"断开连接异常: {e}")

# 测试代码
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    # 测试采集器
    collector = AuctionCollector()
    
    print("测试连接到eltdx服务器...")
    if collector.connect():
        print("连接成功！")
        
        # 测试获取单只股票数据
        print("\n测试获取上海建工(600170)竞价数据...")
        data = collector.get_auction_data("600170")
        if data:
            print(f"获取成功：{data['stock_code']} - {data['timestamp']}")
            print(f"竞价价格: {data['auction_price']}")
            print(f"竞价成交量: {data['auction_volume']}")
        else:
            print("获取失败")
        
        # 测试批量采集
        print("\n测试批量采集自选股...")
        batch_data = collector.collect_auction_batch()
        print(f"批量采集完成，获取{len(batch_data)}只股票数据")
        
        # 断开连接
        collector.disconnect()
    else:
        print("连接失败！")