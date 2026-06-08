#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""生成模拟数据用于测试"""

import sys
import os
import random
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import WATCHLIST
from core.models import AuctionSignal
from storage.database import AuctionDatabase

def generate_mock_data():
    """生成模拟数据"""
    database = AuctionDatabase()
    
    today = datetime.now().strftime('%Y-%m-%d')
    mock_signals = []
    
    print(f"生成{today}模拟数据...")
    
    for stock in WATCHLIST:
        # 生成随机分数
        score = random.randint(20, 95)
        
        # 根据分数确定信号类型
        if score >= 80:
            signal_type = '强抢筹'
            signal_emoji = '🔴'
        elif score >= 60:
            signal_type = '弱抢筹'
            signal_emoji = '🟡'
        elif score >= 40:
            signal_type = '中性'
            signal_emoji = '⚪'
        elif score >= 20:
            signal_type = '弱出货'
            signal_emoji = '🟡'
        else:
            signal_type = '强出货'
            signal_emoji = '🔴'
        
        # 生成模拟数据
        base_price = round(random.uniform(2.5, 4.0), 2)
        predicted_open = round(base_price * (1 + random.uniform(-0.02, 0.03)), 2)
        confidence = round(random.uniform(0.5, 0.95), 2)
        
        # 创建信号对象
        signal = AuctionSignal(
            stock_code=stock['code'],
            stock_name=stock['name'],
            signal_time=datetime.now(),
            signal_type=signal_type,
            signal_score=score,
            signal_emoji=signal_emoji,
            signal_text=signal_type,
            predicted_open_price=predicted_open,
            confidence=confidence,
            analysis_details={
                'scores': {
                    'volume_ratio': random.randint(40, 95),
                    'price_trend': random.randint(40, 95),
                    'cancel_rate': random.randint(40, 95),
                    'bid_ask_ratio': random.randint(40, 95),
                    'seal_strength': random.randint(40, 95)
                }
            }
        )
        
        # 保存到数据库
        database.save_auction_signal(signal)
        
        mock_signals.append({
            'stock_code': stock['code'],
            'stock_name': stock['name'],
            'signal_type': signal_type,
            'signal_score': score,
            'signal_emoji': signal_emoji
        })
        
        print(f"  {stock['code']} {stock['name']}: {signal_emoji} {signal_type} ({score}分)")
    
    print(f"\n生成完成，共{len(mock_signals)}条模拟数据")
    
    # 关闭数据库
    database.disconnect()
    
    return mock_signals

if __name__ == '__main__':
    generate_mock_data()