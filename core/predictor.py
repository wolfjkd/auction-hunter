# 开盘价预测模型
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.models import AuctionData

logger = logging.getLogger(__name__)

class AuctionPredictor:
    """竞价开盘价预测器"""
    
    def __init__(self, database=None):
        """
        初始化预测器
        
        Args:
            database: 数据库实例
        """
        if database is None:
            from storage.database import AuctionDatabase
            database = AuctionDatabase()
        self.database = database
        
    def predict_open_price(self, 
                          stock_code: str, 
                          current_data: AuctionData,
                          historical_data: List[AuctionData] = None) -> Tuple[float, float]:
        """
        预测开盘价
        
        Args:
            stock_code: 股票代码
            current_data: 当前竞价数据
            historical_data: 历史竞价数据
            
        Returns:
            Tuple[float, float]: (预测开盘价, 置信度)
        """
        try:
            # 如果没有历史数据，从数据库获取
            if historical_data is None:
                historical_data = self._get_historical_data(stock_code)
            
            # 使用多种方法预测
            predictions = []
            confidences = []
            
            # 方法1: 加权平均法
            pred1, conf1 = self._weighted_average_prediction(current_data, historical_data)
            predictions.append(pred1)
            confidences.append(conf1)
            
            # 方法2: 趋势外推法
            pred2, conf2 = self._trend_extrapolation_prediction(current_data, historical_data)
            predictions.append(pred2)
            confidences.append(conf2)
            
            # 方法3: 量价关系法
            pred3, conf3 = self._volume_price_relationship_prediction(current_data, historical_data)
            predictions.append(pred3)
            confidences.append(conf3)
            
            # 方法4: 市场情绪法
            pred4, conf4 = self._market_sentiment_prediction(current_data, historical_data)
            predictions.append(pred4)
            confidences.append(conf4)
            
            # 综合预测（加权平均）
            if predictions and confidences:
                total_confidence = sum(confidences)
                if total_confidence > 0:
                    weighted_prediction = sum(p * c for p, c in zip(predictions, confidences)) / total_confidence
                    avg_confidence = np.mean(confidences)
                else:
                    weighted_prediction = np.mean(predictions)
                    avg_confidence = 0.5
            else:
                weighted_prediction = current_data.auction_price
                avg_confidence = 0.5
            
            # 预测区间
            prediction_std = np.std(predictions) if len(predictions) > 1 else 0
            
            logger.info(f"预测{stock_code}开盘价: {weighted_prediction:.2f} (置信度: {avg_confidence:.1%})")
            
            return weighted_prediction, avg_confidence
            
        except Exception as e:
            logger.error(f"预测{stock_code}开盘价异常: {e}")
            return current_data.auction_price, 0.5
    
    def _weighted_average_prediction(self, 
                                   current_data: AuctionData, 
                                   historical_data: List[AuctionData]) -> Tuple[float, float]:
        """
        加权平均法预测
        
        Args:
            current_data: 当前竞价数据
            historical_data: 历史竞价数据
            
        Returns:
            Tuple[float, float]: (预测价格, 置信度)
        """
        if not historical_data:
            return current_data.auction_price, 0.5
        
        # 获取历史价格
        historical_prices = [d.auction_price for d in historical_data if d.auction_price > 0]
        
        if not historical_prices:
            return current_data.auction_price, 0.5
        
        # 计算历史平均价格
        avg_historical = np.mean(historical_prices)
        
        # 加权平均：当前价格权重0.7，历史价格权重0.3
        predicted = current_data.auction_price * 0.7 + avg_historical * 0.3
        
        # 置信度基于数据一致性
        price_std = np.std(historical_prices)
        if price_std <= 0.01:  # 价格波动很小
            confidence = 0.8
        elif price_std <= 0.05:
            confidence = 0.6
        else:
            confidence = 0.4
        
        return predicted, confidence
    
    def _trend_extrapolation_prediction(self, 
                                      current_data: AuctionData, 
                                      historical_data: List[AuctionData]) -> Tuple[float, float]:
        """
        趋势外推法预测
        
        Args:
            current_data: 当前竞价数据
            historical_data: 历史竞价数据
            
        Returns:
            Tuple[float, float]: (预测价格, 置信度)
        """
        if len(historical_data) < 2:
            return current_data.auction_price, 0.5
        
        # 获取历史价格（按时间排序）
        prices = [d.auction_price for d in historical_data if d.auction_price > 0]
        prices.append(current_data.auction_price)
        
        if len(prices) < 2:
            return current_data.auction_price, 0.5
        
        # 计算价格变化趋势
        price_changes = []
        for i in range(1, len(prices)):
            change = (prices[i] - prices[i-1]) / prices[i-1]
            price_changes.append(change)
        
        if not price_changes:
            return current_data.auction_price, 0.5
        
        # 计算趋势斜率
        avg_change = np.mean(price_changes)
        
        # 外推预测
        predicted = current_data.auction_price * (1 + avg_change)
        
        # 置信度基于趋势一致性
        change_std = np.std(price_changes)
        if change_std <= 0.005:  # 趋势非常稳定
            confidence = 0.7
        elif change_std <= 0.01:
            confidence = 0.5
        else:
            confidence = 0.3
        
        return predicted, confidence
    
    def _volume_price_relationship_prediction(self, 
                                            current_data: AuctionData, 
                                            historical_data: List[AuctionData]) -> Tuple[float, float]:
        """
        量价关系法预测
        
        Args:
            current_data: 当前竞价数据
            historical_data: 历史竞价数据
            
        Returns:
            Tuple[float, float]: (预测价格, 置信度)
        """
        if not historical_data:
            return current_data.auction_price, 0.5
        
        # 计算量比
        historical_volumes = [d.auction_volume for d in historical_data if d.auction_volume > 0]
        
        if not historical_volumes:
            return current_data.auction_price, 0.5
        
        avg_volume = np.mean(historical_volumes)
        volume_ratio = current_data.auction_volume / avg_volume if avg_volume > 0 else 1.0
        
        # 量价关系分析
        # 放量上涨: 价格可能继续上涨
        # 放量下跌: 价格可能继续下跌
        # 缩量上涨: 上涨动力不足
        # 缩量下跌: 下跌动力不足
        
        # 计算价格变化
        historical_prices = [d.auction_price for d in historical_data if d.auction_price > 0]
        if historical_prices:
            price_change = (current_data.auction_price - historical_prices[-1]) / historical_prices[-1]
        else:
            price_change = 0
        
        # 基于量价关系调整预测
        if volume_ratio > 1.5:  # 放量
            if price_change > 0:  # 放量上涨
                adjustment = 0.02  # 预计继续上涨2%
            else:  # 放量下跌
                adjustment = -0.02  # 预计继续下跌2%
        elif volume_ratio < 0.5:  # 缩量
            if price_change > 0:  # 缩量上涨
                adjustment = -0.01  # 上涨动力不足，可能回调
            else:  # 缩量下跌
                adjustment = 0.01  # 下跌动力不足，可能反弹
        else:  # 正常成交量
            adjustment = price_change * 0.5  # 延续当前趋势
        
        predicted = current_data.auction_price * (1 + adjustment)
        
        # 置信度
        confidence = 0.6 if volume_ratio > 1.2 or volume_ratio < 0.8 else 0.4
        
        return predicted, confidence
    
    def _market_sentiment_prediction(self, 
                                   current_data: AuctionData, 
                                   historical_data: List[AuctionData]) -> Tuple[float, float]:
        """
        市场情绪法预测
        
        Args:
            current_data: 当前竞价数据
            historical_data: 历史竞价数据
            
        Returns:
            Tuple[float, float]: (预测价格, 置信度)
        """
        # 分析委买委卖比例
        total_bid = sum(current_data.bid_volumes) if current_data.bid_volumes else 0
        total_ask = sum(current_data.ask_volumes) if current_data.ask_volumes else 0
        
        if total_ask == 0:
            return current_data.auction_price, 0.5
        
        bid_ask_ratio = total_bid / total_ask
        
        # 市场情绪分析
        # 委买 > 委卖: 看涨情绪
        # 委卖 > 委买: 看跌情绪
        
        if bid_ask_ratio > 1.5:  # 强烈看涨
            sentiment_adjustment = 0.02
        elif bid_ask_ratio > 1.2:  # 看涨
            sentiment_adjustment = 0.01
        elif bid_ask_ratio < 0.5:  # 强烈看跌
            sentiment_adjustment = -0.02
        elif bid_ask_ratio < 0.8:  # 看跌
            sentiment_adjustment = -0.01
        else:  # 中性
            sentiment_adjustment = 0
        
        predicted = current_data.auction_price * (1 + sentiment_adjustment)
        
        # 置信度
        confidence = 0.5
        
        return predicted, confidence
    
    def _get_historical_data(self, stock_code: str, days: int = 5) -> List[AuctionData]:
        """
        获取历史竞价数据
        
        Args:
            stock_code: 股票代码
            days: 获取天数
            
        Returns:
            List[AuctionData]: 历史竞价数据
        """
        try:
            # 从数据库获取历史数据
            history_records = self.database.get_auction_history(stock_code, days)
            
            historical_data = []
            for record in history_records:
                # 创建AuctionData对象
                auction_data = AuctionData(
                    stock_code=record['stock_code'],
                    stock_name=record['stock_name'],
                    market='sh',  # 简化处理
                    timestamp=datetime.strptime(record['trade_date'], '%Y-%m-%d'),
                    auction_price=record.get('auction_end_price', 0),
                    auction_volume=record.get('auction_volume', 0),
                    bid_prices=[],
                    ask_prices=[],
                    bid_volumes=[],
                    ask_volumes=[]
                )
                historical_data.append(auction_data)
            
            return historical_data
            
        except Exception as e:
            logger.error(f"获取{stock_code}历史数据异常: {e}")
            return []
    
    def predict_multiple_stocks(self, stock_data_list: List[Dict[str, Any]]) -> Dict[str, Tuple[float, float]]:
        """
        预测多只股票开盘价
        
        Args:
            stock_data_list: 股票数据列表
            
        Returns:
            Dict[str, Tuple[float, float]]: 预测结果 {股票代码: (预测价格, 置信度)}
        """
        predictions = {}
        
        for data in stock_data_list:
            stock_code = data.get('stock_code')
            stock_name = data.get('stock_name')
            
            if not stock_code:
                continue
            
            # 转换为AuctionData对象
            auction_data = AuctionData(
                stock_code=stock_code,
                stock_name=stock_name,
                market=data.get('market', 'sh'),
                timestamp=data.get('timestamp', datetime.now()),
                auction_price=data.get('auction_price', 0),
                auction_volume=data.get('auction_volume', 0),
                bid_prices=data.get('bid_price', []),
                ask_prices=data.get('ask_price', []),
                bid_volumes=data.get('bid_volume', []),
                ask_volumes=data.get('ask_volume', [])
            )
            
            # 预测开盘价
            predicted_price, confidence = self.predict_open_price(stock_code, auction_data)
            predictions[stock_code] = (predicted_price, confidence)
        
        logger.info(f"预测{len(predictions)}只股票开盘价完成")
        return predictions
    
    def calculate_prediction_accuracy(self, stock_code: str, days: int = 30) -> Dict[str, Any]:
        """
        计算预测准确率
        
        Args:
            stock_code: 股票代码
            days: 计算天数
            
        Returns:
            Dict: 准确率统计
        """
        try:
            # 获取历史数据
            history = self.database.get_auction_history(stock_code, days)
            
            if len(history) < 2:
                return {'accuracy': 0, 'sample_size': 0}
            
            # 计算预测准确率
            correct_predictions = 0
            total_predictions = 0
            errors = []
            
            for i in range(1, len(history)):
                current = history[i]
                previous = history[i-1]
                
                # 获取实际开盘价
                actual_open = current.get('open_price', 0)
                if actual_open <= 0:
                    continue
                
                # 获取竞价价格（作为预测基准）
                auction_price = current.get('auction_end_price', 0)
                if auction_price <= 0:
                    continue
                
                # 计算预测误差
                error = abs(actual_open - auction_price) / actual_open
                errors.append(error)
                
                # 判断预测是否准确（误差在1%以内）
                if error <= 0.01:
                    correct_predictions += 1
                
                total_predictions += 1
            
            # 计算准确率
            accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0
            avg_error = np.mean(errors) if errors else 0
            
            result = {
                'stock_code': stock_code,
                'accuracy': accuracy,
                'average_error': avg_error,
                'sample_size': total_predictions,
                'correct_predictions': correct_predictions,
                'analysis_period_days': days
            }
            
            logger.info(f"计算{stock_code}预测准确率: {accuracy:.1%}")
            return result
            
        except Exception as e:
            logger.error(f"计算{stock_code}预测准确率异常: {e}")
            return {'accuracy': 0, 'sample_size': 0}

# 测试代码
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建预测器
    predictor = AuctionPredictor()
    
    # 测试预测
    print("测试开盘价预测...")
    
    # 创建测试数据
    current_data = AuctionData(
        stock_code="600170",
        stock_name="上海建工",
        market="sh",
        timestamp=datetime.now(),
        auction_price=2.85,
        auction_volume=200000,
        bid_prices=[2.84, 2.83, 2.82],
        ask_prices=[2.86, 2.87, 2.88],
        bid_volumes=[50000, 40000, 30000],
        ask_volumes=[30000, 25000, 20000]
    )
    
    # 预测开盘价
    predicted_price, confidence = predictor.predict_open_price("600170", current_data)
    
    print(f"当前竞价价格: {current_data.auction_price}")
    print(f"预测开盘价: {predicted_price:.2f}")
    print(f"置信度: {confidence:.1%}")
    
    # 计算预测准确率
    print("\n计算预测准确率...")
    accuracy_stats = predictor.calculate_prediction_accuracy("600170", 30)
    print(f"准确率: {accuracy_stats.get('accuracy', 0):.1%}")
    print(f"平均误差: {accuracy_stats.get('average_error', 0):.2%}")
    print(f"样本数量: {accuracy_stats.get('sample_size', 0)}")