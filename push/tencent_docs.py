# 腾讯文档推送模块
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import PUSH_TENCENT_DOCS
from core.models import AuctionSignal
from storage.database import AuctionDatabase

logger = logging.getLogger(__name__)

class TencentDocsPusher:
    """腾讯文档推送器"""
    
    def __init__(self, database: AuctionDatabase = None):
        """
        初始化推送器
        
        Args:
            database: 数据库实例
        """
        self.database = database or AuctionDatabase()
        self.enabled = PUSH_TENCENT_DOCS
        
    def push_daily_report(self, trade_date: str = None) -> bool:
        """
        推送每日报告到腾讯文档
        
        Args:
            trade_date: 交易日期，默认今天
            
        Returns:
            bool: 是否推送成功
        """
        if not self.enabled:
            logger.info("腾讯文档推送已禁用")
            return False
        
        if trade_date is None:
            trade_date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            # 获取今日信号
            signals = self.database.get_auction_signals_by_date(trade_date)
            
            if not signals:
                logger.warning(f"无{trade_date}信号数据可推送")
                return False
            
            # 生成报告内容
            report_content = self._generate_report_content(signals, trade_date)
            
            # 推送到腾讯文档
            success = self._push_to_tencent_docs(report_content, trade_date)
            
            if success:
                logger.info(f"推送{trade_date}每日报告成功")
            else:
                logger.error(f"推送{trade_date}每日报告失败")
            
            return success
            
        except Exception as e:
            logger.error(f"推送每日报告异常: {e}")
            return False
    
    def _generate_report_content(self, signals: List[Dict[str, Any]], trade_date: str) -> str:
        """
        生成报告内容
        
        Args:
            signals: 信号数据列表
            trade_date: 交易日期
            
        Returns:
            str: 报告内容
        """
        # 按信号分数排序
        sorted_signals = sorted(signals, key=lambda x: x.get('signal_score', 0), reverse=True)
        
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
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # 生成报告内容
        content = f"""
# 集合竞价猎手 - 每日报告

**报告日期**: {trade_date}
**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**监控股票**: {len(signals)}只
**平均分数**: {avg_score:.1f}分

## 信号分布

- 🔴 强抢筹: {signal_distribution['strong_buy']}只
- 🟡 弱抢筹: {signal_distribution['weak_buy']}只
- ⚪ 中性: {signal_distribution['neutral']}只
- 🟡 弱出货: {signal_distribution['weak_sell']}只
- 🔴 强出货: {signal_distribution['strong_sell']}只

## 重点信号

"""
        
        # 添加前5个信号
        for i, signal in enumerate(sorted_signals[:5], 1):
            signal_emoji = signal.get('signal_emoji', '⚪')
            signal_text = signal.get('signal_text', '中性')
            stock_name = signal.get('stock_name', '')
            stock_code = signal.get('stock_code', '')
            score = signal.get('signal_score', 0)
            predicted_open = signal.get('predicted_open_price', 0)
            confidence = signal.get('confidence', 0)
            
            content += f"""
### {i}. {stock_name} ({stock_code})

- **信号类型**: {signal_emoji} {signal_text}
- **信号分数**: {score:.1f}分
- **预测开盘价**: {predicted_open:.2f}
- **置信度**: {confidence:.1%}

"""
        
        # 添加完整信号列表
        content += """
## 完整信号列表

| 排名 | 股票代码 | 股票名称 | 信号类型 | 信号分数 | 预测开盘价 | 置信度 |
|------|----------|----------|----------|----------|------------|--------|
"""
        
        for i, signal in enumerate(sorted_signals, 1):
            stock_code = signal.get('stock_code', '')
            stock_name = signal.get('stock_name', '')
            signal_emoji = signal.get('signal_emoji', '⚪')
            signal_text = signal.get('signal_text', '中性')
            score = signal.get('signal_score', 0)
            predicted_open = signal.get('predicted_open_price', 0)
            confidence = signal.get('confidence', 0)
            
            content += f"| {i} | {stock_code} | {stock_name} | {signal_emoji} {signal_text} | {score:.1f} | {predicted_open:.2f} | {confidence:.1%} |\n"
        
        content += f"""

---
*报告由集合竞价猎手自动生成*
*数据来源: eltdx TDX郑州节点*
"""
        
        return content
    
    def _push_to_tencent_docs(self, content: str, trade_date: str) -> bool:
        """
        推送内容到腾讯文档
        
        Args:
            content: 报告内容
            trade_date: 交易日期
            
        Returns:
            bool: 是否推送成功
        """
        try:
            # 这里应该调用腾讯文档MCP接口
            # 由于没有实际的MCP接口，这里模拟推送
            
            # 保存到本地文件
            report_filename = f"daily_report_{trade_date}.md"
            report_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'reports', report_filename)
            
            # 确保目录存在
            os.makedirs(os.path.dirname(report_path), exist_ok=True)
            
            # 写入文件
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"报告已保存到本地: {report_path}")
            
            # TODO: 调用腾讯文档MCP接口
            # 这里应该使用 mcp__tencent-docs__create_smartcanvas_by_mdx
            
            return True
            
        except Exception as e:
            logger.error(f"推送到腾讯文档失败: {e}")
            return False
    
    def push_signal_alert(self, signal: AuctionSignal) -> bool:
        """
        推送信号预警
        
        Args:
            signal: 竞价信号
            
        Returns:
            bool: 是否推送成功
        """
        if not self.enabled:
            return False
        
        try:
            # 只推送强信号
            if signal.signal_score < 80:
                return False
            
            # 生成预警内容
            alert_content = f"""
# 🚨 竞价信号预警

**股票**: {signal.stock_name} ({signal.stock_code})
**信号类型**: {signal.signal_emoji} {signal.signal_text}
**信号分数**: {signal.signal_score:.1f}分
**预测开盘价**: {signal.predicted_open_price:.2f}
**置信度**: {signal.confidence:.1%}
**预警时间**: {signal.signal_time.strftime('%Y-%m-%d %H:%M:%S')}

## 分析详情

"""
            
            # 添加分析详情
            analysis_details = signal.analysis_details
            if 'scores' in analysis_details:
                scores = analysis_details['scores']
                alert_content += "### 评分明细\n\n"
                for dimension, score in scores.items():
                    alert_content += f"- {dimension}: {score:.1f}分\n"
            
            # 保存预警文件
            alert_filename = f"alert_{signal.stock_code}_{signal.signal_time.strftime('%Y%m%d_%H%M%S')}.md"
            alert_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'alerts', alert_filename)
            
            os.makedirs(os.path.dirname(alert_path), exist_ok=True)
            
            with open(alert_path, 'w', encoding='utf-8') as f:
                f.write(alert_content)
            
            logger.info(f"信号预警已保存: {alert_path}")
            
            # TODO: 推送到腾讯文档
            
            return True
            
        except Exception as e:
            logger.error(f"推送信号预警异常: {e}")
            return False
    
    def get_push_history(self) -> List[Dict[str, Any]]:
        """
        获取推送历史
        
        Returns:
            List[Dict]: 推送历史列表
        """
        try:
            reports_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'reports')
            
            if not os.path.exists(reports_dir):
                return []
            
            history = []
            for filename in os.listdir(reports_dir):
                if filename.endswith('.md'):
                    filepath = os.path.join(reports_dir, filename)
                    stat = os.stat(filepath)
                    
                    history.append({
                        'filename': filename,
                        'filepath': filepath,
                        'size': stat.st_size,
                        'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
            
            # 按修改时间排序
            history.sort(key=lambda x: x['modified_at'], reverse=True)
            
            return history
            
        except Exception as e:
            logger.error(f"获取推送历史异常: {e}")
            return []

# 测试代码
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建推送器
    pusher = TencentDocsPusher()
    
    # 测试推送每日报告
    print("测试推送每日报告...")
    today = datetime.now().strftime('%Y-%m-%d')
    
    success = pusher.push_daily_report(today)
    
    if success:
        print("推送成功")
        
        # 显示推送历史
        history = pusher.get_push_history()
        print(f"\n推送历史 ({len(history)}条):")
        for record in history[:5]:  # 显示最近5条
            print(f"  {record['filename']} - {record['modified_at']}")
    else:
        print("推送失败")