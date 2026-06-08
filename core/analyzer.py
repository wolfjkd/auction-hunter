# 信号分析引擎
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import numpy as np
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import WATCHLIST, SIGNAL_THRESHOLDS
from core.models import AuctionData, AuctionSignal, get_signal_type
from core.scorer import AuctionScorer

logger = logging.getLogger(__name__)

class AuctionAnalyzer:
    """竞价信号分析器"""
    
    def __init__(self, database=None):
        """
        初始化分析器
        
        Args:
            database: 数据库实例
        """
        if database is None:
            from storage.database import AuctionDatabase
            database = AuctionDatabase()
        self.database = database
        self.scorer = AuctionScorer()
        
    def analyze_stock(self, stock_code: str, stock_name: str, current_data: Dict[str, Any]) -> Optional[AuctionSignal]:
        """
        分析单只股票
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            current_data: 当前竞价数据
            
        Returns:
            Optional[AuctionSignal]: 竞价信号
        """
        try:
            # 获取历史数据
            historical_data = self._get_historical_data(stock_code)
            
            # 转换当前数据为AuctionData对象
            current_auction_data = self._convert_to_auction_data(stock_code, stock_name, current_data)
            
            if not current_auction_data:
                logger.error(f"转换{stock_code}数据失败")
                return None
            
            # 生成信号
            signal = self.scorer.generate_signal(
                stock_code=stock_code,
                stock_name=stock_name,
                current_data=current_auction_data,
                historical_data=historical_data
            )
            
            # 保存信号到数据库
            self.database.save_auction_signal(signal)
            
            return signal
            
        except Exception as e:
            logger.error(f"分析{stock_code}异常: {e}")
            return None
    
    def analyze_all_stocks(self, auction_data_list: List[Dict[str, Any]]) -> List[AuctionSignal]:
        """
        分析所有股票
        
        Args:
            auction_data_list: 竞价数据列表
            
        Returns:
            List[AuctionSignal]: 竞价信号列表
        """
        signals = []
        
        for data in auction_data_list:
            stock_code = data.get('stock_code')
            stock_name = data.get('stock_name')
            
            if not stock_code:
                continue
            
            signal = self.analyze_stock(stock_code, stock_name, data)
            if signal:
                signals.append(signal)
        
        # 按信号分数排序
        signals.sort(key=lambda x: x.signal_score, reverse=True)
        
        logger.info(f"分析完成，共{len(signals)}只股票")
        return signals
    
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
                # 这里简化处理，实际应该从数据库中获取完整的竞价数据
                # 暂时创建模拟数据
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
    
    def _convert_to_auction_data(self, stock_code: str, stock_name: str, data: Dict[str, Any]) -> Optional[AuctionData]:
        """
        转换数据为AuctionData对象
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            data: 原始数据
            
        Returns:
            Optional[AuctionData]: AuctionData对象
        """
        try:
            return AuctionData(
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
        except Exception as e:
            logger.error(f"转换数据异常: {e}")
            return None
    
    def generate_daily_report(self, trade_date: str = None) -> Dict[str, Any]:
        """
        生成每日报告
        
        Args:
            trade_date: 交易日期，默认今天
            
        Returns:
            Dict: 报告数据
        """
        if trade_date is None:
            trade_date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            # 获取当日信号
            signals = self.database.get_auction_signals_by_date(trade_date)
            
            # 统计信号分布
            signal_distribution = {
                'strong_buy': 0,
                'weak_buy': 0,
                'neutral': 0,
                'weak_sell': 0,
                'strong_sell': 0
            }
            
            for signal in signals:
                signal_type = signal.get('signal_type', '').lower()
                if '强抢筹' in signal_type:
                    signal_distribution['strong_buy'] += 1
                elif '弱抢筹' in signal_type:
                    signal_distribution['weak_buy'] += 1
                elif '中性' in signal_type:
                    signal_distribution['neutral'] += 1
                elif '弱出货' in signal_type:
                    signal_distribution['weak_sell'] += 1
                elif '强出货' in signal_type:
                    signal_distribution['strong_sell'] += 1
            
            # 计算平均分数
            scores = [s.get('signal_score', 0) for s in signals if s.get('signal_score')]
            avg_score = np.mean(scores) if scores else 0
            
            # 生成报告
            report = {
                'trade_date': trade_date,
                'total_stocks': len(signals),
                'signal_distribution': signal_distribution,
                'average_score': avg_score,
                'top_signals': signals[:5] if signals else [],  # 前5个信号
                'generated_at': datetime.now().isoformat()
            }
            
            logger.info(f"生成{trade_date}每日报告完成")
            return report
            
        except Exception as e:
            logger.error(f"生成每日报告异常: {e}")
            return {}
    
    def get_stock_analysis_summary(self, stock_code: str) -> Dict[str, Any]:
        """
        获取股票分析摘要
        
        Args:
            stock_code: 股票代码
            
        Returns:
            Dict: 分析摘要
        """
        try:
            # 获取最新信号
            latest_signals = self.database.get_auction_signals_by_date(datetime.now().strftime('%Y-%m-%d'))
            latest_signal = None
            
            for signal in latest_signals:
                if signal['stock_code'] == stock_code:
                    latest_signal = signal
                    break
            
            # 获取历史数据
            history = self.database.get_auction_history(stock_code, 30)
            
            # 计算历史平均分数
            historical_scores = [h.get('signal_score', 0) for h in history if h.get('signal_score')]
            avg_historical_score = np.mean(historical_scores) if historical_scores else 0
            
            # 计算信号一致性
            if historical_scores:
                score_std = np.std(historical_scores)
                consistency = max(0, 1 - score_std / 50)  # 标准差越小，一致性越高
            else:
                consistency = 0.5
            
            summary = {
                'stock_code': stock_code,
                'latest_signal': latest_signal,
                'historical_average_score': avg_historical_score,
                'signal_consistency': consistency,
                'total_signals': len(historical_scores),
                'analysis_date': datetime.now().isoformat()
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"获取{stock_code}分析摘要异常: {e}")
            return {}
    
    def compare_stocks(self, stock_codes: List[str]) -> Dict[str, Any]:
        """
        比较多只股票
        
        Args:
            stock_codes: 股票代码列表
            
        Returns:
            Dict: 比较结果
        """
        comparison = {}
        
        for stock_code in stock_codes:
            summary = self.get_stock_analysis_summary(stock_code)
            comparison[stock_code] = summary
        
        # 按最新信号分数排序
        sorted_stocks = sorted(
            comparison.items(),
            key=lambda x: x[1].get('latest_signal', {}).get('signal_score', 0) if x[1].get('latest_signal') else 0,
            reverse=True
        )
        
        return {
            'comparison': comparison,
            'ranking': [stock_code for stock_code, _ in sorted_stocks],
            'generated_at': datetime.now().isoformat()
        }
    
    def detect_anomalies(self, trade_date: str = None) -> List[Dict[str, Any]]:
        """
        检测异常信号
        
        Args:
            trade_date: 交易日期
            
        Returns:
            List[Dict]: 异常信号列表
        """
        if trade_date is None:
            trade_date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            signals = self.database.get_auction_signals_by_date(trade_date)
            anomalies = []
            
            for signal in signals:
                # 检测异常条件
                is_anomaly = False
                reasons = []
                
                # 1. 极端分数
                score = signal.get('signal_score', 0)
                if score >= 95 or score <= 5:
                    is_anomaly = True
                    reasons.append(f"极端分数: {score}")
                
                # 2. 高置信度
                confidence = signal.get('confidence', 0)
                if confidence >= 0.9:
                    is_anomaly = True
                    reasons.append(f"高置信度: {confidence:.1%}")
                
                # 3. 信号类型与历史不符
                stock_code = signal.get('stock_code')
                history = self.database.get_auction_history(stock_code, 10)
                if history:
                    recent_signals = [h.get('signal_type', '') for h in history[:3]]
                    current_type = signal.get('signal_type', '')
                    
                    # 如果最近3天都是同类型信号，可能是趋势
                    if len(set(recent_signals)) == 1 and recent_signals[0] == current_type:
                        is_anomaly = True
                        reasons.append("连续相同信号")
                
                if is_anomaly:
                    anomalies.append({
                        'stock_code': stock_code,
                        'stock_name': signal.get('stock_name'),
                        'signal': signal,
                        'reasons': reasons,
                        'detected_at': datetime.now().isoformat()
                    })
            
            logger.info(f"检测到{len(anomalies)}个异常信号")
            return anomalies
            
        except Exception as e:
            logger.error(f"检测异常信号异常: {e}")
            return []

# 测试代码
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建分析器
    analyzer = AuctionAnalyzer()
    
    # 测试生成每日报告
    print("测试生成每日报告...")
    today = datetime.now().strftime('%Y-%m-%d')
    report = analyzer.generate_daily_report(today)
    
    print(f"报告日期: {report.get('trade_date')}")
    print(f"股票数量: {report.get('total_stocks')}")
    print(f"平均分数: {report.get('average_score', 0):.1f}")
    print(f"信号分布: {report.get('signal_distribution')}")
    
    # 测试检测异常
    print("\n测试检测异常信号...")
    anomalies = analyzer.detect_anomalies(today)
    print(f"检测到{len(anomalies)}个异常信号")
    
    for anomaly in anomalies:
        print(f"  {anomaly['stock_code']} - {anomaly['reasons']}")