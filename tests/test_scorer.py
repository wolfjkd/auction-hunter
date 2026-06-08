# 评分算法测试
import unittest
import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.scorer import AuctionScorer
from core.models import AuctionData

class TestAuctionScorer(unittest.TestCase):
    """竞价评分器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.scorer = AuctionScorer()
    
    def test_volume_ratio_score(self):
        """测试量比分计算"""
        print("\n测试量比分计算...")
        
        # 测试用例1: 高量比
        score1 = self.scorer.calculate_volume_ratio_score(300000, [100000, 120000, 110000])
        print(f"高量比 (3.0): {score1:.1f}")
        self.assertGreater(score1, 80)
        
        # 测试用例2: 正常量比
        score2 = self.scorer.calculate_volume_ratio_score(120000, [100000, 120000, 110000])
        print(f"正常量比 (1.1): {score2:.1f}")
        self.assertGreater(score2, 40)
        self.assertLess(score2, 70)
        
        # 测试用例3: 低量比
        score3 = self.scorer.calculate_volume_ratio_score(50000, [100000, 120000, 110000])
        print(f"低量比 (0.5): {score3:.1f}")
        self.assertLess(score3, 40)
        
        # 测试用例4: 无历史数据
        score4 = self.scorer.calculate_volume_ratio_score(100000, [])
        print(f"无历史数据: {score4:.1f}")
        self.assertEqual(score4, 50)
    
    def test_price_trend_score(self):
        """测试价格趋势分计算"""
        print("\n测试价格趋势分计算...")
        
        # 测试用例1: 稳步上涨
        score1 = self.scorer.calculate_price_trend_score([2.80, 2.82, 2.85, 2.88])
        print(f"稳步上涨: {score1:.1f}")
        self.assertGreater(score1, 60)
        
        # 测试用例2: 稳步下跌
        score2 = self.scorer.calculate_price_trend_score([2.90, 2.88, 2.85, 2.82])
        print(f"稳步下跌: {score2:.1f}")
        self.assertLess(score2, 40)
        
        # 测试用例3: 震荡行情
        score3 = self.scorer.calculate_price_trend_score([2.80, 2.85, 2.82, 2.86])
        print(f"震荡行情: {score3:.1f}")
        self.assertGreater(score3, 40)
        self.assertLess(score3, 60)
        
        # 测试用例4: 单一价格
        score4 = self.scorer.calculate_price_trend_score([2.80])
        print(f"单一价格: {score4:.1f}")
        self.assertEqual(score4, 50)
    
    def test_cancel_rate_score(self):
        """测试撤单率分计算"""
        print("\n测试撤单率分计算...")
        
        # 测试用例1: 低撤单率
        score1 = self.scorer.calculate_cancel_rate_score(5000, 200000)
        print(f"低撤单率 (2.5%): {score1:.1f}")
        self.assertGreater(score1, 80)
        
        # 测试用例2: 中等撤单率
        score2 = self.scorer.calculate_cancel_rate_score(30000, 200000)
        print(f"中等撤单率 (15%): {score2:.1f}")
        self.assertGreater(score2, 40)
        self.assertLess(score2, 70)
        
        # 测试用例3: 高撤单率
        score3 = self.scorer.calculate_cancel_rate_score(80000, 200000)
        print(f"高撤单率 (40%): {score3:.1f}")
        self.assertLess(score3, 30)
        
        # 测试用例4: 无挂单
        score4 = self.scorer.calculate_cancel_rate_score(0, 0)
        print(f"无挂单: {score4:.1f}")
        self.assertEqual(score4, 50)
    
    def test_bid_ask_ratio_score(self):
        """测试委比分计算"""
        print("\n测试委比分计算...")
        
        # 测试用例1: 强买盘
        score1 = self.scorer.calculate_bid_ask_ratio_score([80000, 70000, 60000], [30000, 25000, 20000])
        print(f"强买盘: {score1:.1f}")
        self.assertGreater(score1, 70)
        
        # 测试用例2: 均衡市场
        score2 = self.scorer.calculate_bid_ask_ratio_score([50000, 45000, 40000], [50000, 45000, 40000])
        print(f"均衡市场: {score2:.1f}")
        self.assertGreater(score2, 40)
        self.assertLess(score2, 60)
        
        # 测试用例3: 强卖盘
        score3 = self.scorer.calculate_bid_ask_ratio_score([30000, 25000, 20000], [80000, 70000, 60000])
        print(f"强卖盘: {score3:.1f}")
        self.assertLess(score3, 30)
        
        # 测试用例4: 空数据
        score4 = self.scorer.calculate_bid_ask_ratio_score([], [])
        print(f"空数据: {score4:.1f}")
        self.assertEqual(score4, 50)
    
    def test_seal_strength_score(self):
        """测试封单力度分计算"""
        print("\n测试封单力度分计算...")
        
        # 测试用例1: 高封单比例
        score1 = self.scorer.calculate_seal_strength_score([160000], 200000)
        print(f"高封单比例 (80%): {score1:.1f}")
        self.assertGreater(score1, 80)
        
        # 测试用例2: 中等封单比例
        score2 = self.scorer.calculate_seal_strength_score([100000], 200000)
        print(f"中等封单比例 (50%): {score2:.1f}")
        self.assertGreater(score2, 40)
        self.assertLess(score2, 70)
        
        # 测试用例3: 低封单比例
        score3 = self.scorer.calculate_seal_strength_score([20000], 200000)
        print(f"低封单比例 (10%): {score3:.1f}")
        self.assertLess(score3, 30)
        
        # 测试用例4: 无成交量
        score4 = self.scorer.calculate_seal_strength_score([], 0)
        print(f"无成交量: {score4:.1f}")
        self.assertEqual(score4, 50)
    
    def test_total_score_calculation(self):
        """测试总分计算"""
        print("\n测试总分计算...")
        
        # 测试用例1: 高分情况
        scores1 = {
            'volume_ratio': 90,
            'price_trend': 85,
            'cancel_rate': 80,
            'bid_ask_ratio': 75,
            'seal_strength': 70
        }
        total1 = self.scorer.calculate_total_score(scores1)
        print(f"高分情况: {total1:.1f}")
        self.assertGreater(total1, 80)
        
        # 测试用例2: 低分情况
        scores2 = {
            'volume_ratio': 20,
            'price_trend': 25,
            'cancel_rate': 30,
            'bid_ask_ratio': 35,
            'seal_strength': 40
        }
        total2 = self.scorer.calculate_total_score(scores2)
        print(f"低分情况: {total2:.1f}")
        self.assertLess(total2, 30)
        
        # 测试用例3: 中等分数
        scores3 = {
            'volume_ratio': 50,
            'price_trend': 50,
            'cancel_rate': 50,
            'bid_ask_ratio': 50,
            'seal_strength': 50
        }
        total3 = self.scorer.calculate_total_score(scores3)
        print(f"中等分数: {total3:.1f}")
        self.assertEqual(total3, 50)
    
    def test_signal_generation(self):
        """测试信号生成"""
        print("\n测试信号生成...")
        
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
        
        # 生成信号
        signal = self.scorer.generate_signal("600170", "上海建工", current_data, historical_data)
        
        print(f"信号类型: {signal.signal_emoji} {signal.signal_text}")
        print(f"信号分数: {signal.signal_score:.1f}")
        print(f"预测开盘价: {signal.predicted_open_price}")
        print(f"置信度: {signal.confidence:.1%}")
        
        # 验证信号结构
        self.assertIn('stock_code', signal.to_dict())
        self.assertIn('signal_score', signal.to_dict())
        self.assertIn('signal_type', signal.to_dict())
        
        # 验证分数范围
        self.assertGreaterEqual(signal.signal_score, 0)
        self.assertLessEqual(signal.signal_score, 100)
        
        # 验证置信度范围
        self.assertGreaterEqual(signal.confidence, 0)
        self.assertLessEqual(signal.confidence, 1)
    
    def test_edge_cases(self):
        """测试边界情况"""
        print("\n测试边界情况...")
        
        # 测试用例1: 零值数据
        score1 = self.scorer.calculate_volume_ratio_score(0, [0, 0, 0])
        print(f"零值数据: {score1:.1f}")
        self.assertEqual(score1, 50)
        
        # 测试用例2: 极端高值
        score2 = self.scorer.calculate_volume_ratio_score(1000000, [100000, 120000, 110000])
        print(f"极端高值: {score2:.1f}")
        self.assertGreater(score2, 90)
        
        # 测试用例3: 极端低值
        score3 = self.scorer.calculate_volume_ratio_score(1000, [100000, 120000, 110000])
        print(f"极端低值: {score3:.1f}")
        self.assertLess(score3, 10)

if __name__ == '__main__':
    # 设置日志
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # 运行测试
    unittest.main(verbosity=2)