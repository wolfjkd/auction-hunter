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
            # 获取竞价数据 (返回AuctionSeries对象)
            auction_series = self.client.get_call_auction(stock_code)
            if not auction_series or not auction_series.points:
                logger.warning(f"获取{stock_code}竞价数据失败或无数据")
                return None
            
            # 获取最新竞价点
            latest_point = auction_series.points[-1]
            
            # 获取行情快照 (返回列表，第一个元素是QuoteSnapshot)
            quotes = self.client.get_quote(stock_code)
            quote = quotes[0] if quotes else None
            
            # 计算竞价统计
            total_matched = sum(p.matched_volume for p in auction_series.points)
            total_unmatched = latest_point.unmatched_volume
            
            # 获取买五卖五
            bid_prices = []
            bid_volumes = []
            ask_prices = []
            ask_volumes = []
            
            if quote:
                for level in quote.buy_levels:
                    if level.price > 0:
                        bid_prices.append(level.price)
                        bid_volumes.append(level.volume)
                for level in quote.sell_levels:
                    if level.price > 0:
                        ask_prices.append(level.price)
                        ask_volumes.append(level.volume)
            
            # 整理数据
            result = {
                "stock_code": stock_code,
                "timestamp": datetime.now(),
                "auction_price": latest_point.price,
                "auction_volume": total_matched,
                "auction_unmatched": total_unmatched,
                "auction_direction": "buy" if latest_point.unmatched_direction_raw > 0 else "sell",
                "auction_points": len(auction_series.points),
                "bid_price": bid_prices,
                "ask_price": ask_prices,
                "bid_volume": bid_volumes,
                "ask_volume": ask_volumes,
                "quote": {
                    "pre_close": quote.pre_close_price if quote else 0,
                    "last_price": quote.last_price if quote else 0,
                    "open_price": quote.open_price if quote else 0,
                },
                "raw_data": {
                    "latest_time": latest_point.time_label,
                    "latest_price_milli": latest_point.price_milli,
                    "matched_volume": latest_point.matched_volume,
                    "unmatched_volume": latest_point.unmatched_volume,
                }
            }
            
            logger.debug(f"获取{stock_code}竞价数据成功: {latest_point.time_label} 价格={latest_point.price:.2f} 已匹配={total_matched}")
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
            quotes = self.client.get_quote(stock_code)
            if not quotes:
                return None
            
            q = quotes[0]
            
            # 获取买五卖五
            bid_prices = []
            bid_volumes = []
            ask_prices = []
            ask_volumes = []
            
            for level in q.buy_levels:
                if level.price > 0:
                    bid_prices.append(level.price)
                    bid_volumes.append(level.volume)
            for level in q.sell_levels:
                if level.price > 0:
                    ask_prices.append(level.price)
                    ask_volumes.append(level.volume)
            
            return {
                "stock_code": stock_code,
                "timestamp": datetime.now(),
                "price": q.last_price if q.last_price > 0 else q.pre_close_price,
                "pre_close": q.pre_close_price,
                "open": q.open_price,
                "high": q.high_price,
                "low": q.low_price,
                "volume": q.total_hand,
                "amount": q.amount,
                "bid1_price": bid_prices[0] if bid_prices else 0,
                "bid1_volume": bid_volumes[0] if bid_volumes else 0,
                "ask1_price": ask_prices[0] if ask_prices else 0,
                "ask1_volume": ask_volumes[0] if ask_volumes else 0,
                "bid_prices": bid_prices,
                "ask_prices": ask_prices,
                "bid_volumes": bid_volumes,
                "ask_volumes": ask_volumes,
            }
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
                    "bid_price": quote.get("bid_prices", []),
                    "ask_price": quote.get("ask_prices", []),
                    "bid_volume": quote.get("bid_volumes", []),
                    "ask_volume": quote.get("ask_volumes", []),
                    "quote": quote,
                    "is_realtime": True
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
                self.client = None
                self.connected = False
                logger.info("已断开eltdx连接")
            except Exception as e:
                logger.error(f"断开连接异常: {e}")

# 测试代码
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    collector = AuctionCollector()
    
    print("测试连接到eltdx服务器...")
    if collector.connect():
        print("连接成功！")
        print(f"是否竞价时间: {collector.is_auction_time()}")
        
        # 测试获取竞价数据
        print("\n测试获取上海建工(600170)竞价数据...")
        data = collector.get_auction_data("600170")
        if data:
            print(f"获取成功：{data['stock_code']}")
            print(f"竞价价格: {data['auction_price']:.2f}")
            print(f"已匹配量: {data['auction_volume']}")
            print(f"未匹配量: {data['auction_unmatched']}")
            print(f"竞价方向: {data['auction_direction']}")
            print(f"竞价点数: {data['auction_points']}")
        else:
            print("获取失败")
        
        # 测试批量采集
        print("\n测试批量采集自选股...")
        batch_data = collector.collect_auction_batch()
        print(f"批量采集完成，获取{len(batch_data)}只股票数据")
        for d in batch_data:
            print(f"  {d['stock_code']} {d['stock_name']}: {d['auction_price']:.2f} (量={d['auction_volume']})")
        
        collector.disconnect()
    else:
        print("连接失败！")