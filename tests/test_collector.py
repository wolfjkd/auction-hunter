# 数据采集测试
import unittest
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.collector import AuctionCollector
from storage.database import AuctionDatabase

class TestAuctionCollector(unittest.TestCase):
    """竞价数据采集器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.collector = AuctionCollector()
        self.database = AuctionDatabase()
    
    def test_connection(self):
        """测试连接"""
        print("测试连接到eltdx服务器...")
        result = self.collector.connect()
        
        # 注意：这个测试需要实际的eltdx服务器连接
        # 在CI/CD环境中可能失败
        if result:
            print("连接成功")
            self.assertTrue(result)
            self.assertTrue(self.collector.connected)
        else:
            print("连接失败（可能服务器不可用）")
            # 在测试环境中，我们允许连接失败
            self.skipTest("eltdx服务器不可用")
    
    def test_get_auction_data(self):
        """测试获取竞价数据"""
        print("测试获取竞价数据...")
        
        # 先连接
        if not self.collector.connect():
            self.skipTest("eltdx服务器不可用")
        
        # 测试获取上海建工数据
        data = self.collector.get_auction_data("600170")
        
        if data:
            print(f"获取成功: {data['stock_code']}")
            self.assertIn('stock_code', data)
            self.assertIn('timestamp', data)
            self.assertIn('auction_price', data)
            self.assertIn('auction_volume', data)
        else:
            print("获取失败（可能不在竞价时间）")
    
    def test_collect_auction_batch(self):
        """测试批量采集"""
        print("测试批量采集...")
        
        # 先连接
        if not self.collector.connect():
            self.skipTest("eltdx服务器不可用")
        
        # 测试批量采集
        data_list = self.collector.collect_auction_batch()
        
        print(f"批量采集完成，获取{len(data_list)}只股票数据")
        
        # 验证数据结构
        for data in data_list:
            self.assertIn('stock_code', data)
            self.assertIn('stock_name', data)
            self.assertIn('timestamp', data)
    
    def test_is_auction_time(self):
        """测试竞价时间检查"""
        print("测试竞价时间检查...")
        
        # 获取当前时间
        now = datetime.now()
        print(f"当前时间: {now.strftime('%H:%M:%S')}")
        
        # 检查是否在竞价时间内
        is_auction = self.collector.is_auction_time()
        print(f"是否在竞价时间内: {is_auction}")
        
        # 这个测试只是验证方法能正常运行
        self.assertIsInstance(is_auction, bool)
    
    def test_database_operations(self):
        """测试数据库操作"""
        print("测试数据库操作...")
        
        # 测试保存数据
        test_data = {
            'stock_code': '600170',
            'stock_name': '上海建工',
            'market': 'sh',
            'timestamp': datetime.now(),
            'auction_price': 2.85,
            'auction_volume': 150000,
            'bid_price': [2.84, 2.83, 2.82],
            'ask_price': [2.86, 2.87, 2.88],
            'bid_volume': [50000, 30000, 20000],
            'ask_volume': [40000, 25000, 15000],
            'quote': {'price': 2.85, 'open': 2.84}
        }
        
        # 保存数据
        result = self.database.save_auction_data(test_data)
        self.assertTrue(result)
        print("保存数据成功")
        
        # 查询数据
        today = datetime.now().strftime('%Y-%m-%d')
        data = self.database.get_auction_data_by_date(today)
        self.assertIsInstance(data, list)
        print(f"查询到{len(data)}条数据")
    
    def tearDown(self):
        """测试后清理"""
        # 断开连接
        if self.collector.connected:
            self.collector.disconnect()
        
        # 关闭数据库
        self.database.disconnect()

class TestDatabaseOperations(unittest.TestCase):
    """数据库操作测试"""
    
    def setUp(self):
        """测试前准备"""
        self.database = AuctionDatabase()
    
    def test_database_stats(self):
        """测试数据库统计"""
        print("测试数据库统计...")
        
        stats = self.database.get_database_stats()
        
        self.assertIn('auction_data_count', stats)
        self.assertIn('auction_signals_count', stats)
        self.assertIn('auction_history_count', stats)
        self.assertIn('latest_data_date', stats)
        self.assertIn('database_size_mb', stats)
        
        print(f"数据库统计: {stats}")
    
    def test_save_and_query(self):
        """测试保存和查询"""
        print("测试保存和查询...")
        
        # 保存测试数据
        test_data = {
            'stock_code': '600170',
            'stock_name': '上海建工',
            'market': 'sh',
            'timestamp': datetime.now(),
            'auction_price': 2.85,
            'auction_volume': 150000,
            'bid_price': [2.84, 2.83, 2.82],
            'ask_price': [2.86, 2.87, 2.88],
            'bid_volume': [50000, 30000, 20000],
            'ask_volume': [40000, 25000, 15000],
            'quote': {'price': 2.85, 'open': 2.84}
        }
        
        # 保存数据
        result = self.database.save_auction_data(test_data)
        self.assertTrue(result)
        
        # 查询数据
        today = datetime.now().strftime('%Y-%m-%d')
        data = self.database.get_auction_data_by_date(today)
        
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        
        # 验证数据内容
        latest_data = data[-1]
        self.assertEqual(latest_data['stock_code'], '600170')
        self.assertEqual(latest_data['stock_name'], '上海建工')
        print(f"查询到数据: {latest_data['stock_code']} - {latest_data['stock_name']}")
    
    def test_get_latest_data(self):
        """测试获取最新数据"""
        print("测试获取最新数据...")
        
        # 获取最新数据
        latest = self.database.get_latest_auction_data('600170')
        
        if latest:
            print(f"最新数据: {latest['stock_code']} - {latest['timestamp']}")
            self.assertIn('stock_code', latest)
            self.assertIn('timestamp', latest)
        else:
            print("无最新数据")
    
    def tearDown(self):
        """测试后清理"""
        self.database.disconnect()

if __name__ == '__main__':
    # 设置日志
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # 运行测试
    unittest.main(verbosity=2)