# 五维度评分算法
import numpy as np
import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SCORING_WEIGHTS, SIGNAL_THRESHOLDS
from core.models import AuctionData, AuctionSignal, create_auction_signal

logger = logging.getLogger(__name__)

class AuctionScorer:
    """竞价信号评分器"""
    
    def __init__(self, weights: Dict[str, float] = None):
        """
        初始化评分器
        
        Args:
            weights: 评分权重字典
        """
        self.weights = weights or SCORING_WEIGHTS
        self.thresholds = SIGNAL_THRESHOLDS
        
    def calculate_volume_ratio_score(self, current_volume: int, historical_volumes: List[int]) -> float:
        """
        计算竞价量比分数
        
        Args:
            current_volume: 当前竞价成交量
            historical_volumes: 历史竞价成交量列表
            
        Returns:
            float: 量比分 (0-100)
        """
        if not historical_volumes or current_volume <= 0:
            return 50  # 中性分数
        
        # 计算历史平均值
        avg_volume = np.mean(historical_volumes)
        
        if avg_volume <= 0:
            return 50
        
        # 计算量比
        volume_ratio = current_volume / avg_volume
        
        # 量比分计算逻辑
        # 量比 > 3: 高分 (可能抢筹)
        # 量比 1-3: 中等分数
        # 量比 < 1: 低分 (可能出货)
        
        if volume_ratio >= 3.0:
            score = 90 + min(10, (volume_ratio - 3.0) * 5)  # 最高100分
        elif volume_ratio >= 2.0:
            score = 70 + (volume_ratio - 2.0) * 20
        elif volume_ratio >= 1.5:
            score = 60 + (volume_ratio - 1.5) * 20
        elif volume_ratio >= 1.0:
            score = 50 + (volume_ratio - 1.0) * 20
        elif volume_ratio >= 0.5:
            score = 30 + (volume_ratio - 0.5) * 40
        else:
            score = max(0, volume_ratio * 60)
        
        return min(100, max(0, score))
    
    def calculate_price_trend_score(self, price_history: List[float]) -> float:
        """
        计算价格趋势分数
        
        Args:
            price_history: 价格历史列表（按时间顺序）
            
        Returns:
            float: 价格趋势分 (0-100)
        """
        if len(price_history) < 2:
            return 50  # 中性分数
        
        # 计算价格变化
        price_changes = []
        for i in range(1, len(price_history)):
            change = (price_history[i] - price_history[i-1]) / price_history[i-1] * 100
            price_changes.append(change)
        
        if not price_changes:
            return 50
        
        # 计算趋势指标
        avg_change = np.mean(price_changes)
        total_change = (price_history[-1] - price_history[0]) / price_history[0] * 100
        
        # 趋势一致性（所有变化方向一致）
        positive_changes = sum(1 for c in price_changes if c > 0)
        consistency = positive_changes / len(price_changes) if price_changes else 0.5
        
        # 分数计算
        # 稳步上涨: 高分
        # 稳步下跌: 低分
        # 震荡: 中等分数
        
        base_score = 50
        
        # 总体变化影响
        if total_change > 2.0:
            base_score += 30
        elif total_change > 1.0:
            base_score += 20
        elif total_change > 0.5:
            base_score += 10
        elif total_change < -2.0:
            base_score -= 30
        elif total_change < -1.0:
            base_score -= 20
        elif total_change < -0.5:
            base_score -= 10
        
        # 趋势一致性影响
        if consistency > 0.8:  # 高度一致
            if total_change > 0:
                base_score += 10  # 上涨趋势加分
            else:
                base_score -= 10  # 下跌趋势减分
        elif consistency < 0.2:  # 高度一致（下跌）
            if total_change < 0:
                base_score -= 10
        
        return min(100, max(0, base_score))
    
    def calculate_cancel_rate_score(self, cancel_volume: int, total_volume: int) -> float:
        """
        计算撤单率分数
        
        Args:
            cancel_volume: 撤单量
            total_volume: 总挂单量
            
        Returns:
            float: 撤单率分 (0-100)
        """
        if total_volume <= 0:
            return 50  # 中性分数
        
        # 计算撤单率
        cancel_rate = cancel_volume / total_volume
        
        # 撤单率分数计算
        # 高撤单率: 低分（可能出货）
        # 低撤单率: 高分（真实成交）
        
        if cancel_rate <= 0.05:  # 5%以下
            score = 90 + (0.05 - cancel_rate) * 200  # 最高100分
        elif cancel_rate <= 0.10:  # 5-10%
            score = 70 + (0.10 - cancel_rate) * 400
        elif cancel_rate <= 0.20:  # 10-20%
            score = 50 + (0.20 - cancel_rate) * 200
        elif cancel_rate <= 0.30:  # 20-30%
            score = 30 + (0.30 - cancel_rate) * 200
        else:  # 30%以上
            score = max(0, 30 - (cancel_rate - 0.30) * 200)
        
        return min(100, max(0, score))
    
    def calculate_bid_ask_ratio_score(self, bid_volumes: List[int], ask_volumes: List[int]) -> float:
        """
        计算委比变化分数
        
        Args:
            bid_volumes: 委买量列表
            ask_volumes: 委卖量列表
            
        Returns:
            float: 委比分 (0-100)
        """
        if not bid_volumes or not ask_volumes:
            return 50
        
        # 计算总委买和总委卖
        total_bid = sum(bid_volumes)
        total_ask = sum(ask_volumes)
        
        if total_bid + total_ask == 0:
            return 50
        
        # 计算委比
        bid_ask_ratio = total_bid / total_ask if total_ask > 0 else 1.0
        
        # 委比分数计算
        # 委买 > 委卖: 高分（买方力量强）
        # 委卖 > 委买: 低分（卖方力量强）
        
        if bid_ask_ratio >= 2.0:
            score = 90 + min(10, (bid_ask_ratio - 2.0) * 5)
        elif bid_ask_ratio >= 1.5:
            score = 70 + (bid_ask_ratio - 1.5) * 40
        elif bid_ask_ratio >= 1.0:
            score = 50 + (bid_ask_ratio - 1.0) * 40
        elif bid_ask_ratio >= 0.5:
            score = 30 + (bid_ask_ratio - 0.5) * 40
        else:
            score = max(0, bid_ask_ratio * 60)
        
        return min(100, max(0, score))
    
    def calculate_seal_strength_score(self, near_price_volumes: List[int], total_volume: int) -> float:
        """
        计算封单力度分数
        
        Args:
            near_price_volumes: 开盘价附近的挂单量列表
            total_volume: 总成交量
            
        Returns:
            float: 封单力度分 (0-100)
        """
        if not near_price_volumes or total_volume <= 0:
            return 50
        
        # 计算开盘价附近的挂单比例
        near_volume = sum(near_price_volumes)
        seal_ratio = near_volume / total_volume
        
        # 封单力度分数计算
        # 高封单比例: 高分（支撑强）
        # 低封单比例: 低分（支撑弱）
        
        if seal_ratio >= 0.8:
            score = 90 + (seal_ratio - 0.8) * 50
        elif seal_ratio >= 0.6:
            score = 70 + (seal_ratio - 0.6) * 100
        elif seal_ratio >= 0.4:
            score = 50 + (seal_ratio - 0.4) * 100
        elif seal_ratio >= 0.2:
            score = 30 + (seal_ratio - 0.2) * 100
        else:
            score = seal_ratio * 150
        
        return min(100, max(0, score))
    
    def calculate_total_score(self, scores: Dict[str, float]) -> float:
        """
        计算总分
        
        Args:
            scores: 各维度分数
            
        Returns:
            float: 总分 (0-100)
        """
        total_score = 0
        
        for dimension, weight in self.weights.items():
            if dimension in scores:
                total_score += scores[dimension] * weight
            else:
                logger.warning(f"缺少维度分数: {dimension}")
        
        return min(100, max(0, total_score))
    
    def analyze_auction_data(self, 
                           current_data: AuctionData, 
                           historical_data: List[AuctionData]) -> Tuple[float, Dict[str, Any]]:
        """
        分析竞价数据并计算分数
        
        Args:
            current_data: 当前竞价数据
            historical_data: 历史竞价数据
            
        Returns:
            Tuple[float, Dict[str, Any]]: (总分, 分析详情)
        """
        try:
            # 准备历史数据
            historical_volumes = [d.auction_volume for d in historical_data if d.auction_volume > 0]
            price_history = [d.auction_price for d in historical_data if d.auction_price > 0]
            price_history.append(current_data.auction_price)
            
            # 计算各维度分数
            scores = {}
            
            # 1. 竞价量比分数
            scores['volume_ratio'] = self.calculate_volume_ratio_score(
                current_data.auction_volume, historical_volumes
            )
            
            # 2. 价格趋势分数
            scores['price_trend'] = self.calculate_price_trend_score(price_history)
            
            # 3. 撤单率分数（模拟数据，实际需要从eltdx获取）
            # 这里使用模拟的撤单率
            cancel_volume = int(current_data.auction_volume * 0.1)  # 假设10%撤单
            total_volume = current_data.auction_volume + cancel_volume
            scores['cancel_rate'] = self.calculate_cancel_rate_score(cancel_volume, total_volume)
            
            # 4. 委比变化分数
            scores['bid_ask_ratio'] = self.calculate_bid_ask_ratio_score(
                current_data.bid_volumes, current_data.ask_volumes
            )
            
            # 5. 封单力度分数（模拟数据）
            # 假设开盘价附近有20%的挂单
            near_price_volumes = [int(current_data.auction_volume * 0.2)]
            scores['seal_strength'] = self.calculate_seal_strength_score(
                near_price_volumes, current_data.auction_volume
            )
            
            # 计算总分
            total_score = self.calculate_total_score(scores)
            
            # 分析详情
            analysis_details = {
                'scores': scores,
                'weights': self.weights,
                'volume_ratio': current_data.auction_volume / np.mean(historical_volumes) if historical_volumes else 1.0,
                'price_change': (current_data.auction_price - price_history[0]) / price_history[0] * 100 if price_history else 0,
                'cancel_rate': cancel_volume / total_volume if total_volume > 0 else 0,
                'bid_ask_ratio': sum(current_data.bid_volumes) / sum(current_data.ask_volumes) if current_data.ask_volumes else 1.0,
                'seal_ratio': near_price_volumes[0] / current_data.auction_volume if current_data.auction_volume > 0 else 0
            }
            
            return total_score, analysis_details
            
        except Exception as e:
            logger.error(f"分析竞价数据异常: {e}")
            return 50, {'error': str(e)}
    
    def generate_signal(self, 
                       stock_code: str,
                       stock_name: str,
                       current_data: AuctionData,
                       historical_data: List[AuctionData],
                       predicted_open: float = None) -> AuctionSignal:
        """
        生成竞价信号
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            current_data: 当前竞价数据
            historical_data: 历史竞价数据
            predicted_open: 预测开盘价
            
        Returns:
            AuctionSignal: 竞价信号
        """
        try:
            # 计算分数和分析详情
            total_score, analysis_details = self.analyze_auction_data(current_data, historical_data)
            
            # 预测开盘价（如果没有提供）
            if predicted_open is None:
                predicted_open = self._predict_open_price(current_data, historical_data)
            
            # 计算置信度
            confidence = self._calculate_confidence(analysis_details)
            
            # 创建信号
            signal = create_auction_signal(
                stock_code=stock_code,
                stock_name=stock_name,
                score=total_score,
                predicted_open=predicted_open,
                confidence=confidence,
                analysis_details=analysis_details
            )
            
            logger.info(f"生成{stock_code}竞价信号: {signal.signal_text} ({signal.signal_score}分)")
            return signal
            
        except Exception as e:
            logger.error(f"生成竞价信号异常: {e}")
            # 返回中性信号
            return create_auction_signal(
                stock_code=stock_code,
                stock_name=stock_name,
                score=50,
                predicted_open=current_data.auction_price,
                confidence=0.5,
                analysis_details={'error': str(e)}
            )
    
    def _predict_open_price(self, current_data: AuctionData, historical_data: List[AuctionData]) -> float:
        """
        预测开盘价
        
        Args:
            current_data: 当前竞价数据
            historical_data: 历史竞价数据
            
        Returns:
            float: 预测开盘价
        """
        # 简单预测：使用当前竞价价格和历史平均价格的加权平均
        if not historical_data:
            return current_data.auction_price
        
        historical_prices = [d.auction_price for d in historical_data if d.auction_price > 0]
        if not historical_prices:
            return current_data.auction_price
        
        # 历史平均价格
        avg_historical = np.mean(historical_prices)
        
        # 加权平均：当前价格权重0.7，历史价格权重0.3
        predicted = current_data.auction_price * 0.7 + avg_historical * 0.3
        
        return round(predicted, 2)
    
    def _calculate_confidence(self, analysis_details: Dict[str, Any]) -> float:
        """
        计算预测置信度
        
        Args:
            analysis_details: 分析详情
            
        Returns:
            float: 置信度 (0-1)
        """
        # 基于分析一致性计算置信度
        scores = analysis_details.get('scores', {})
        if not scores:
            return 0.5
        
        # 计算分数的标准差
        score_values = list(scores.values())
        if len(score_values) < 2:
            return 0.5
        
        std_dev = np.std(score_values)
        
        # 标准差越小，一致性越高，置信度越高
        if std_dev <= 10:
            confidence = 0.9
        elif std_dev <= 20:
            confidence = 0.7
        elif std_dev <= 30:
            confidence = 0.5
        else:
            confidence = 0.3
        
        return confidence

# 测试代码
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建评分器
    scorer = AuctionScorer()
    
    # 测试各维度分数计算
    print("测试评分算法...")
    
    # 1. 测试量比分
    volume_score = scorer.calculate_volume_ratio_score(200000, [100000, 120000, 110000])
    print(f"量比分: {volume_score:.1f}")
    
    # 2. 测试价格趋势分
    price_score = scorer.calculate_price_trend_score([2.80, 2.82, 2.85, 2.88])
    print(f"价格趋势分: {price_score:.1f}")
    
    # 3. 测试撤单率分
    cancel_score = scorer.calculate_cancel_rate_score(10000, 200000)
    print(f"撤单率分: {cancel_score:.1f}")
    
    # 4. 测试委比分
    bid_ask_score = scorer.calculate_bid_ask_ratio_score([50000, 40000, 30000], [30000, 25000, 20000])
    print(f"委比分: {bid_ask_score:.1f}")
    
    # 5. 测试封单力度分
    seal_score = scorer.calculate_seal_strength_score([40000], 200000)
    print(f"封单力度分: {seal_score:.1f}")
    
    # 计算总分
    scores = {
        'volume_ratio': volume_score,
        'price_trend': price_score,
        'cancel_rate': cancel_score,
        'bid_ask_ratio': bid_ask_score,
        'seal_strength': seal_score
    }
    
    total_score = scorer.calculate_total_score(scores)
    print(f"\n总分: {total_score:.1f}")
    
    # 生成信号
    from core.models import AuctionData
    
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
    
    historical_data = [
        AuctionData(
            stock_code="600170",
            stock_name="上海建工",
            market="sh",
            timestamp=datetime.now() - timedelta(days=1),
            auction_price=2.80,
            auction_volume=150000,
            bid_prices=[2.79, 2.78, 2.77],
            ask_prices=[2.81, 2.82, 2.83],
            bid_volumes=[40000, 35000, 30000],
            ask_volumes=[35000, 30000, 25000]
        )
    ]
    
    signal = scorer.generate_signal("600170", "上海建工", current_data, historical_data)
    print(f"\n生成信号: {signal.signal_emoji} {signal.signal_text}")
    print(f"信号分数: {signal.signal_score:.1f}")
    print(f"预测开盘价: {signal.predicted_open_price}")
    print(f"置信度: {signal.confidence:.1%}")