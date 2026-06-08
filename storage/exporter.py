# CSV导出模块
import csv
import logging
from datetime import datetime, date
from typing import Dict, List, Any, Optional
import os
import sys
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import CSV_EXPORT_PATH
from storage.database import AuctionDatabase

logger = logging.getLogger(__name__)

class DataExporter:
    """数据导出器"""
    
    def __init__(self, database: AuctionDatabase, export_path: str = CSV_EXPORT_PATH):
        """
        初始化导出器
        
        Args:
            database: 数据库实例
            export_path: 导出路径
        """
        self.database = database
        self.export_path = export_path
        
        # 确保导出目录存在
        os.makedirs(export_path, exist_ok=True)
    
    def export_auction_data_to_csv(self, trade_date: str, filename: str = None) -> Optional[str]:
        """
        导出竞价数据到CSV
        
        Args:
            trade_date: 交易日期 (YYYY-MM-DD)
            filename: 文件名（可选）
            
        Returns:
            Optional[str]: 导出文件路径
        """
        try:
            # 获取数据
            data = self.database.get_auction_data_by_date(trade_date)
            if not data:
                logger.warning(f"无{trade_date}竞价数据可导出")
                return None
            
            # 生成文件名
            if filename is None:
                filename = f"auction_data_{trade_date}.csv"
            
            filepath = os.path.join(self.export_path, filename)
            
            # 写入CSV
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                
                # 写入表头
                headers = [
                    '股票代码', '股票名称', '市场', '交易日期', '时间戳',
                    '竞价价格', '竞价成交量', '委买价格', '委卖价格',
                    '委买数量', '委卖数量', '行情数据'
                ]
                writer.writerow(headers)
                
                # 写入数据
                for row in data:
                    writer.writerow([
                        row['stock_code'],
                        row['stock_name'],
                        row['market'],
                        row['trade_date'],
                        row['timestamp'],
                        row['auction_price'],
                        row['auction_volume'],
                        row['bid_prices'],
                        row['ask_prices'],
                        row['bid_volumes'],
                        row['ask_volumes'],
                        row['quote_data']
                    ])
            
            logger.info(f"导出竞价数据成功: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"导出竞价数据失败: {e}")
            return None
    
    def export_auction_signals_to_csv(self, signal_date: str, filename: str = None) -> Optional[str]:
        """
        导出竞价信号到CSV
        
        Args:
            signal_date: 信号日期 (YYYY-MM-DD)
            filename: 文件名（可选）
            
        Returns:
            Optional[str]: 导出文件路径
        """
        try:
            # 获取数据
            signals = self.database.get_auction_signals_by_date(signal_date)
            if not signals:
                logger.warning(f"无{signal_date}竞价信号可导出")
                return None
            
            # 生成文件名
            if filename is None:
                filename = f"auction_signals_{signal_date}.csv"
            
            filepath = os.path.join(self.export_path, filename)
            
            # 写入CSV
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                
                # 写入表头
                headers = [
                    '股票代码', '股票名称', '信号日期', '信号时间',
                    '信号类型', '信号分数', '信号图标', '信号文本',
                    '预测开盘价', '置信度', '分析详情'
                ]
                writer.writerow(headers)
                
                # 写入数据
                for signal in signals:
                    writer.writerow([
                        signal['stock_code'],
                        signal['stock_name'],
                        signal['signal_date'],
                        signal['signal_time'],
                        signal['signal_type'],
                        signal['signal_score'],
                        signal['signal_emoji'],
                        signal['signal_text'],
                        signal['predicted_open_price'],
                        signal['confidence'],
                        signal['analysis_details']
                    ])
            
            logger.info(f"导出竞价信号成功: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"导出竞价信号失败: {e}")
            return None
    
    def export_auction_history_to_csv(self, stock_code: str, days: int = 30, filename: str = None) -> Optional[str]:
        """
        导出竞价历史到CSV
        
        Args:
            stock_code: 股票代码
            days: 导出天数
            filename: 文件名（可选）
            
        Returns:
            Optional[str]: 导出文件路径
        """
        try:
            # 获取数据
            history = self.database.get_auction_history(stock_code, days)
            if not history:
                logger.warning(f"无{stock_code}竞价历史可导出")
                return None
            
            # 生成文件名
            if filename is None:
                filename = f"auction_history_{stock_code}_{days}days.csv"
            
            filepath = os.path.join(self.export_path, filename)
            
            # 写入CSV
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                
                # 写入表头
                headers = [
                    '股票代码', '股票名称', '交易日期',
                    '竞价开始价', '竞价结束价', '竞价最高价', '竞价最低价',
                    '竞价成交量', '竞价成交额', '开盘价',
                    '信号类型', '信号分数'
                ]
                writer.writerow(headers)
                
                # 写入数据
                for record in history:
                    writer.writerow([
                        record['stock_code'],
                        record['stock_name'],
                        record['trade_date'],
                        record['auction_start_price'],
                        record['auction_end_price'],
                        record['auction_high_price'],
                        record['auction_low_price'],
                        record['auction_volume'],
                        record['auction_amount'],
                        record['open_price'],
                        record['signal_type'],
                        record['signal_score']
                    ])
            
            logger.info(f"导出竞价历史成功: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"导出竞价历史失败: {e}")
            return None
    
    def export_daily_report(self, trade_date: str, filename: str = None) -> Optional[str]:
        """
        导出每日竞价报告
        
        Args:
            trade_date: 交易日期 (YYYY-MM-DD)
            filename: 文件名（可选）
            
        Returns:
            Optional[str]: 导出文件路径
        """
        try:
            # 获取数据
            signals = self.database.get_auction_signals_by_date(trade_date)
            auction_data = self.database.get_auction_data_by_date(trade_date)
            
            if not signals and not auction_data:
                logger.warning(f"无{trade_date}数据可生成报告")
                return None
            
            # 生成文件名
            if filename is None:
                filename = f"daily_report_{trade_date}.csv"
            
            filepath = os.path.join(self.export_path, filename)
            
            # 写入CSV
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                
                # 写入报告标题
                writer.writerow([f'集合竞价猎手 - 每日报告'])
                writer.writerow([f'报告日期: {trade_date}'])
                writer.writerow([])
                
                # 写入信号汇总
                writer.writerow(['竞价信号汇总'])
                writer.writerow(['股票代码', '股票名称', '信号类型', '信号分数', '预测开盘价', '置信度'])
                
                for signal in signals:
                    writer.writerow([
                        signal['stock_code'],
                        signal['stock_name'],
                        signal['signal_emoji'] + ' ' + signal['signal_text'],
                        signal['signal_score'],
                        signal['predicted_open_price'],
                        f"{signal['confidence']:.1%}"
                    ])
                
                writer.writerow([])
                
                # 写入竞价数据统计
                writer.writerow(['竞价数据统计'])
                writer.writerow(['股票代码', '股票名称', '竞价成交量', '竞价价格'])
                
                # 按股票分组统计
                stock_stats = {}
                for data in auction_data:
                    code = data['stock_code']
                    if code not in stock_stats:
                        stock_stats[code] = {
                            'name': data['stock_name'],
                            'volume': 0,
                            'prices': []
                        }
                    stock_stats[code]['volume'] += data['auction_volume']
                    stock_stats[code]['prices'].append(data['auction_price'])
                
                for code, stats in stock_stats.items():
                    avg_price = sum(stats['prices']) / len(stats['prices']) if stats['prices'] else 0
                    writer.writerow([
                        code,
                        stats['name'],
                        stats['volume'],
                        f"{avg_price:.2f}"
                    ])
            
            logger.info(f"导出每日报告成功: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"导出每日报告失败: {e}")
            return None
    
    def export_all_data(self, trade_date: str) -> Dict[str, Optional[str]]:
        """
        导出所有数据
        
        Args:
            trade_date: 交易日期
            
        Returns:
            Dict: 导出结果
        """
        results = {}
        
        # 导出竞价数据
        results['auction_data'] = self.export_auction_data_to_csv(trade_date)
        
        # 导出竞价信号
        results['auction_signals'] = self.export_auction_signals_to_csv(trade_date)
        
        # 导出每日报告
        results['daily_report'] = self.export_daily_report(trade_date)
        
        return results
    
    def get_export_files(self) -> List[str]:
        """
        获取导出文件列表
        
        Returns:
            List[str]: 文件路径列表
        """
        try:
            files = []
            for filename in os.listdir(self.export_path):
                if filename.endswith('.csv'):
                    filepath = os.path.join(self.export_path, filename)
                    files.append(filepath)
            
            return sorted(files, key=os.path.getmtime, reverse=True)
            
        except Exception as e:
            logger.error(f"获取导出文件列表失败: {e}")
            return []

# 测试代码
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建数据库和导出器
    db = AuctionDatabase()
    exporter = DataExporter(db)
    
    # 测试导出
    today = datetime.now().strftime('%Y-%m-%d')
    
    print(f"测试导出{today}数据...")
    results = exporter.export_all_data(today)
    
    for data_type, filepath in results.items():
        if filepath:
            print(f"{data_type}: {filepath}")
        else:
            print(f"{data_type}: 无数据")
    
    # 显示导出文件列表
    print("\n导出文件列表:")
    files = exporter.get_export_files()
    for file in files:
        print(f"  {file}")
    
    # 关闭数据库
    db.disconnect()
    print("\n导出测试完成")