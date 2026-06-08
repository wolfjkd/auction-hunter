# SQLite数据库操作模块
import sqlite3
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Tuple
import json
import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DATABASE_PATH
from core.models import AuctionData, AuctionSignal, AuctionHistory

logger = logging.getLogger(__name__)

class AuctionDatabase:
    """竞价数据库操作类"""
    
    def __init__(self, db_path: str = DATABASE_PATH):
        """
        初始化数据库连接
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
        # 确保数据库目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # 初始化数据库
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表结构"""
        try:
            self.connect()
            self._create_tables()
            logger.info(f"数据库初始化完成: {self.db_path}")
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    def connect(self):
        """建立数据库连接"""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # 返回字典格式结果
            self.cursor = self.conn.cursor()
            logger.debug("数据库连接成功")
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            raise
    
    def disconnect(self):
        """关闭数据库连接"""
        if self.conn:
            try:
                self.conn.close()
                self.conn = None
                self.cursor = None
                logger.debug("数据库连接已关闭")
            except Exception as e:
                logger.error(f"关闭数据库连接失败: {e}")
    
    def _create_tables(self):
        """创建数据库表"""
        # 竞价数据表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS auction_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT NOT NULL,
                stock_name TEXT,
                market TEXT,
                trade_date TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                auction_price REAL,
                auction_volume INTEGER,
                bid_prices TEXT,  -- JSON数组
                ask_prices TEXT,  -- JSON数组
                bid_volumes TEXT, -- JSON数组
                ask_volumes TEXT, -- JSON数组
                quote_data TEXT,  -- JSON对象
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(stock_code, trade_date, timestamp)
            )
        ''')
        
        # 竞价信号表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS auction_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT NOT NULL,
                stock_name TEXT,
                signal_date TEXT NOT NULL,
                signal_time TEXT NOT NULL,
                signal_type TEXT,
                signal_score REAL,
                signal_emoji TEXT,
                signal_text TEXT,
                predicted_open_price REAL,
                confidence REAL,
                analysis_details TEXT,  -- JSON对象
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(stock_code, signal_date, signal_time)
            )
        ''')
        
        # 竞价历史表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS auction_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT NOT NULL,
                stock_name TEXT,
                trade_date TEXT NOT NULL,
                auction_start_price REAL,
                auction_end_price REAL,
                auction_high_price REAL,
                auction_low_price REAL,
                auction_volume INTEGER,
                auction_amount REAL,
                open_price REAL,
                signal_type TEXT,
                signal_score REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(stock_code, trade_date)
            )
        ''')
        
        # 股票信息表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_info (
                code TEXT PRIMARY KEY,
                name TEXT,
                market TEXT,
                industry TEXT,
                sector TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建索引
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_auction_data_stock_date 
            ON auction_data(stock_code, trade_date)
        ''')
        
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_auction_signals_stock_date 
            ON auction_signals(stock_code, signal_date)
        ''')
        
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_auction_history_stock_date 
            ON auction_history(stock_code, trade_date)
        ''')
        
        self.conn.commit()
        logger.debug("数据库表创建完成")
    
    def save_auction_data(self, data: Dict[str, Any]) -> bool:
        """
        保存竞价数据
        
        Args:
            data: 竞价数据字典
            
        Returns:
            bool: 是否保存成功
        """
        try:
            # 准备数据
            stock_code = data.get('stock_code')
            stock_name = data.get('stock_name', '')
            market = data.get('market', '')
            timestamp = data.get('timestamp')
            trade_date = timestamp.strftime('%Y-%m-%d') if isinstance(timestamp, datetime) else timestamp[:10]
            
            # 检查是否已存在
            self.cursor.execute('''
                SELECT id FROM auction_data 
                WHERE stock_code = ? AND trade_date = ? AND timestamp = ?
            ''', (stock_code, trade_date, timestamp.isoformat() if isinstance(timestamp, datetime) else timestamp))
            
            if self.cursor.fetchone():
                logger.debug(f"竞价数据已存在: {stock_code} {timestamp}")
                return True
            
            # 插入数据
            self.cursor.execute('''
                INSERT INTO auction_data (
                    stock_code, stock_name, market, trade_date, timestamp,
                    auction_price, auction_volume, bid_prices, ask_prices,
                    bid_volumes, ask_volumes, quote_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                stock_code,
                stock_name,
                market,
                trade_date,
                timestamp.isoformat() if isinstance(timestamp, datetime) else timestamp,
                data.get('auction_price', 0),
                data.get('auction_volume', 0),
                json.dumps(data.get('bid_price', []), ensure_ascii=False),
                json.dumps(data.get('ask_price', []), ensure_ascii=False),
                json.dumps(data.get('bid_volume', []), ensure_ascii=False),
                json.dumps(data.get('ask_volume', []), ensure_ascii=False),
                json.dumps(data.get('quote', {}), ensure_ascii=False)
            ))
            
            self.conn.commit()
            logger.debug(f"保存竞价数据成功: {stock_code}")
            return True
            
        except Exception as e:
            logger.error(f"保存竞价数据失败: {e}")
            self.conn.rollback()
            return False
    
    def save_auction_signal(self, signal: AuctionSignal) -> bool:
        """
        保存竞价信号
        
        Args:
            signal: 竞价信号对象
            
        Returns:
            bool: 是否保存成功
        """
        try:
            # 检查是否已存在
            self.cursor.execute('''
                SELECT id FROM auction_signals 
                WHERE stock_code = ? AND signal_date = ? AND signal_time = ?
            ''', (
                signal.stock_code,
                signal.signal_time.strftime('%Y-%m-%d'),
                signal.signal_time.isoformat()
            ))
            
            if self.cursor.fetchone():
                logger.debug(f"竞价信号已存在: {signal.stock_code}")
                return True
            
            # 插入数据
            self.cursor.execute('''
                INSERT INTO auction_signals (
                    stock_code, stock_name, signal_date, signal_time,
                    signal_type, signal_score, signal_emoji, signal_text,
                    predicted_open_price, confidence, analysis_details
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                signal.stock_code,
                signal.stock_name,
                signal.signal_time.strftime('%Y-%m-%d'),
                signal.signal_time.isoformat(),
                signal.signal_type,
                signal.signal_score,
                signal.signal_emoji,
                signal.signal_text,
                signal.predicted_open_price,
                signal.confidence,
                json.dumps(signal.analysis_details, ensure_ascii=False)
            ))
            
            self.conn.commit()
            logger.debug(f"保存竞价信号成功: {signal.stock_code}")
            return True
            
        except Exception as e:
            logger.error(f"保存竞价信号失败: {e}")
            self.conn.rollback()
            return False
    
    def save_auction_history(self, history: AuctionHistory) -> bool:
        """
        保存竞价历史记录
        
        Args:
            history: 竞价历史记录对象
            
        Returns:
            bool: 是否保存成功
        """
        try:
            # 检查是否已存在
            self.cursor.execute('''
                SELECT id FROM auction_history 
                WHERE stock_code = ? AND trade_date = ?
            ''', (history.stock_code, history.trade_date))
            
            if self.cursor.fetchone():
                # 更新记录
                self.cursor.execute('''
                    UPDATE auction_history SET
                        stock_name = ?,
                        auction_start_price = ?,
                        auction_end_price = ?,
                        auction_high_price = ?,
                        auction_low_price = ?,
                        auction_volume = ?,
                        auction_amount = ?,
                        open_price = ?,
                        signal_type = ?,
                        signal_score = ?
                    WHERE stock_code = ? AND trade_date = ?
                ''', (
                    history.stock_name,
                    history.auction_start_price,
                    history.auction_end_price,
                    history.auction_high_price,
                    history.auction_low_price,
                    history.auction_volume,
                    history.auction_amount,
                    history.open_price,
                    history.signal_type,
                    history.signal_score,
                    history.stock_code,
                    history.trade_date
                ))
            else:
                # 插入新记录
                self.cursor.execute('''
                    INSERT INTO auction_history (
                        stock_code, stock_name, trade_date,
                        auction_start_price, auction_end_price,
                        auction_high_price, auction_low_price,
                        auction_volume, auction_amount,
                        open_price, signal_type, signal_score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    history.stock_code,
                    history.stock_name,
                    history.trade_date,
                    history.auction_start_price,
                    history.auction_end_price,
                    history.auction_high_price,
                    history.auction_low_price,
                    history.auction_volume,
                    history.auction_amount,
                    history.open_price,
                    history.signal_type,
                    history.signal_score
                ))
            
            self.conn.commit()
            logger.debug(f"保存竞价历史成功: {history.stock_code}")
            return True
            
        except Exception as e:
            logger.error(f"保存竞价历史失败: {e}")
            self.conn.rollback()
            return False
    
    def get_auction_data_by_date(self, trade_date: str) -> List[Dict[str, Any]]:
        """
        获取指定日期的竞价数据
        
        Args:
            trade_date: 交易日期 (YYYY-MM-DD)
            
        Returns:
            List[Dict]: 竞价数据列表
        """
        try:
            self.cursor.execute('''
                SELECT * FROM auction_data 
                WHERE trade_date = ? 
                ORDER BY stock_code, timestamp
            ''', (trade_date,))
            
            rows = self.cursor.fetchall()
            result = []
            
            for row in rows:
                data = dict(row)
                # 解析JSON字段
                for field in ['bid_prices', 'ask_prices', 'bid_volumes', 'ask_volumes', 'quote_data']:
                    if data[field]:
                        data[field] = json.loads(data[field])
                result.append(data)
            
            return result
            
        except Exception as e:
            logger.error(f"获取竞价数据失败: {e}")
            return []
    
    def get_auction_data_by_stock(self, stock_code: str, trade_date: str = None) -> List[Dict[str, Any]]:
        """
        获取指定股票的竞价数据
        
        Args:
            stock_code: 股票代码
            trade_date: 交易日期 (可选)
            
        Returns:
            List[Dict]: 竞价数据列表
        """
        try:
            if trade_date:
                self.cursor.execute('''
                    SELECT * FROM auction_data 
                    WHERE stock_code = ? AND trade_date = ? 
                    ORDER BY timestamp
                ''', (stock_code, trade_date))
            else:
                self.cursor.execute('''
                    SELECT * FROM auction_data 
                    WHERE stock_code = ? 
                    ORDER BY trade_date DESC, timestamp
                ''', (stock_code,))
            
            rows = self.cursor.fetchall()
            result = []
            
            for row in rows:
                data = dict(row)
                # 解析JSON字段
                for field in ['bid_prices', 'ask_prices', 'bid_volumes', 'ask_volumes', 'quote_data']:
                    if data[field]:
                        data[field] = json.loads(data[field])
                result.append(data)
            
            return result
            
        except Exception as e:
            logger.error(f"获取股票竞价数据失败: {e}")
            return []
    
    def get_auction_signals_by_date(self, signal_date: str) -> List[Dict[str, Any]]:
        """
        获取指定日期的竞价信号
        
        Args:
            signal_date: 信号日期 (YYYY-MM-DD)
            
        Returns:
            List[Dict]: 竞价信号列表
        """
        try:
            self.cursor.execute('''
                SELECT * FROM auction_signals 
                WHERE signal_date = ? 
                ORDER BY signal_score DESC
            ''', (signal_date,))
            
            rows = self.cursor.fetchall()
            result = []
            
            for row in rows:
                data = dict(row)
                # 解析JSON字段
                if data['analysis_details']:
                    data['analysis_details'] = json.loads(data['analysis_details'])
                result.append(data)
            
            return result
            
        except Exception as e:
            logger.error(f"获取竞价信号失败: {e}")
            return []
    
    def get_auction_history(self, stock_code: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        获取股票竞价历史
        
        Args:
            stock_code: 股票代码
            days: 获取天数
            
        Returns:
            List[Dict]: 竞价历史列表
        """
        try:
            self.cursor.execute('''
                SELECT * FROM auction_history 
                WHERE stock_code = ? 
                ORDER BY trade_date DESC 
                LIMIT ?
            ''', (stock_code, days))
            
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"获取竞价历史失败: {e}")
            return []
    
    def get_latest_auction_data(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        获取股票最新的竞价数据
        
        Args:
            stock_code: 股票代码
            
        Returns:
            Optional[Dict]: 最新竞价数据
        """
        try:
            self.cursor.execute('''
                SELECT * FROM auction_data 
                WHERE stock_code = ? 
                ORDER BY trade_date DESC, timestamp DESC 
                LIMIT 1
            ''', (stock_code,))
            
            row = self.cursor.fetchone()
            if row:
                data = dict(row)
                # 解析JSON字段
                for field in ['bid_prices', 'ask_prices', 'bid_volumes', 'ask_volumes', 'quote_data']:
                    if data[field]:
                        data[field] = json.loads(data[field])
                return data
            
            return None
            
        except Exception as e:
            logger.error(f"获取最新竞价数据失败: {e}")
            return None
    
    def cleanup_old_data(self, days: int = 90):
        """
        清理旧数据
        
        Args:
            days: 保留天数
        """
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            # 清理竞价数据
            self.cursor.execute('''
                DELETE FROM auction_data 
                WHERE trade_date < ?
            ''', (cutoff_date,))
            
            # 清理竞价信号
            self.cursor.execute('''
                DELETE FROM auction_signals 
                WHERE signal_date < ?
            ''', (cutoff_date,))
            
            self.conn.commit()
            logger.info(f"清理{days}天前的旧数据完成")
            
        except Exception as e:
            logger.error(f"清理旧数据失败: {e}")
            self.conn.rollback()
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        获取数据库统计信息
        
        Returns:
            Dict: 统计信息
        """
        try:
            # 确保连接有效
            if not self.conn or not self.cursor:
                logger.warning("数据库连接无效，尝试重新连接")
                self.connect()
            
            stats = {}
            
            # 竞价数据统计
            self.cursor.execute('SELECT COUNT(*) FROM auction_data')
            stats['auction_data_count'] = self.cursor.fetchone()[0]
            
            # 竞价信号统计
            self.cursor.execute('SELECT COUNT(*) FROM auction_signals')
            stats['auction_signals_count'] = self.cursor.fetchone()[0]
            
            # 竞价历史统计
            self.cursor.execute('SELECT COUNT(*) FROM auction_history')
            stats['auction_history_count'] = self.cursor.fetchone()[0]
            
            # 最新数据日期
            self.cursor.execute('''
                SELECT MAX(trade_date) FROM auction_data
            ''')
            result = self.cursor.fetchone()
            stats['latest_data_date'] = result[0] if result[0] else '无数据'
            
            # 数据库文件大小
            if os.path.exists(self.db_path):
                stats['database_size_mb'] = os.path.getsize(self.db_path) / (1024 * 1024)
            else:
                stats['database_size_mb'] = 0
            
            return stats
            
        except Exception as e:
            logger.error(f"获取数据库统计失败: {e}")
            import traceback
            traceback.print_exc()
            return {}

# 测试代码
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    # 测试数据库
    print("测试数据库初始化...")
    db = AuctionDatabase()
    
    # 获取统计信息
    stats = db.get_database_stats()
    print(f"数据库统计: {stats}")
    
    # 测试保存竞价数据
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
    
    print("\n测试保存竞价数据...")
    if db.save_auction_data(test_data):
        print("保存成功")
        
        # 查询数据
        today = datetime.now().strftime('%Y-%m-%d')
        data = db.get_auction_data_by_date(today)
        print(f"查询到{len(data)}条数据")
    else:
        print("保存失败")
    
    # 关闭连接
    db.disconnect()
    print("\n数据库测试完成")