# Flask应用主文件
from flask import Flask, render_template, jsonify, request
import logging
from datetime import datetime, timedelta
import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import WEB_HOST, WEB_PORT, WEB_DEBUG, WATCHLIST
from core.collector import AuctionCollector
from core.analyzer import AuctionAnalyzer
from core.predictor import AuctionPredictor
from storage.database import AuctionDatabase
from storage.exporter import DataExporter

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)

# 初始化组件
database = AuctionDatabase()
collector = AuctionCollector()
analyzer = AuctionAnalyzer(database)
predictor = AuctionPredictor(database)
exporter = DataExporter(database)

@app.route('/')
def dashboard():
    """竞价看板主页"""
    try:
        # 获取今日信号
        today = datetime.now().strftime('%Y-%m-%d')
        signals = database.get_auction_signals_by_date(today)
        
        # 获取自选股列表
        watchlist = WATCHLIST
        
        return render_template('dashboard.html', 
                             signals=signals, 
                             watchlist=watchlist,
                             today=today)
    except Exception as e:
        logger.error(f"加载看板失败: {e}")
        return render_template('dashboard.html', 
                             signals=[], 
                             watchlist=WATCHLIST,
                             today=datetime.now().strftime('%Y-%m-%d'),
                             error=str(e))

@app.route('/history')
def history():
    """历史竞价查询页面"""
    try:
        # 获取查询参数
        stock_code = request.args.get('stock_code', '')
        days = int(request.args.get('days', 30))
        
        # 获取历史数据
        history_data = []
        if stock_code:
            history_data = database.get_auction_history(stock_code, days)
        
        return render_template('history.html',
                             history_data=history_data,
                             stock_code=stock_code,
                             days=days,
                             watchlist=WATCHLIST)
    except Exception as e:
        logger.error(f"加载历史页面失败: {e}")
        return render_template('history.html',
                             history_data=[],
                             stock_code='',
                             days=30,
                             watchlist=WATCHLIST,
                             error=str(e))

@app.route('/api/auction-data')
def api_auction_data():
    """获取竞价数据API"""
    try:
        trade_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        data = database.get_auction_data_by_date(trade_date)
        
        return jsonify({
            'success': True,
            'data': data,
            'count': len(data)
        })
    except Exception as e:
        logger.error(f"获取竞价数据API失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/auction-signals')
def api_auction_signals():
    """获取竞价信号API"""
    try:
        signal_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        signals = database.get_auction_signals_by_date(signal_date)
        
        return jsonify({
            'success': True,
            'data': signals,
            'count': len(signals)
        })
    except Exception as e:
        logger.error(f"获取竞价信号API失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/auction-history/<stock_code>')
def api_auction_history(stock_code):
    """获取股票竞价历史API"""
    try:
        days = int(request.args.get('days', 30))
        history = database.get_auction_history(stock_code, days)
        
        return jsonify({
            'success': True,
            'data': history,
            'count': len(history)
        })
    except Exception as e:
        logger.error(f"获取{stock_code}竞价历史API失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/collect-auction', methods=['POST'])
def api_collect_auction():
    """手动采集竞价数据API"""
    try:
        # 连接eltdx服务器
        if not collector.connected:
            if not collector.connect():
                return jsonify({
                    'success': False,
                    'error': '无法连接到eltdx服务器'
                })
        
        # 采集数据
        data_list = collector.collect_auction_batch()
        
        # 保存到数据库
        saved_count = 0
        for data in data_list:
            if database.save_auction_data(data):
                saved_count += 1
        
        return jsonify({
            'success': True,
            'message': f'采集完成，保存{saved_count}条数据',
            'total': len(data_list),
            'saved': saved_count
        })
    except Exception as e:
        logger.error(f"手动采集API失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/analyze-signals', methods=['POST'])
def api_analyze_signals():
    """分析竞价信号API"""
    try:
        # 获取今日竞价数据
        today = datetime.now().strftime('%Y-%m-%d')
        auction_data = database.get_auction_data_by_date(today)
        
        if not auction_data:
            return jsonify({
                'success': False,
                'error': '无竞价数据可分析'
            })
        
        # 分析信号
        signals = analyzer.analyze_all_stocks(auction_data)
        
        return jsonify({
            'success': True,
            'message': f'分析完成，生成{len(signals)}个信号',
            'signals': [signal.to_dict() for signal in signals]
        })
    except Exception as e:
        logger.error(f"分析信号API失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/predict-open', methods=['POST'])
def api_predict_open():
    """预测开盘价API"""
    try:
        # 获取请求数据
        data = request.get_json()
        stock_code = data.get('stock_code')
        
        if not stock_code:
            return jsonify({
                'success': False,
                'error': '缺少股票代码'
            })
        
        # 获取最新竞价数据
        latest_data = database.get_latest_auction_data(stock_code)
        
        if not latest_data:
            return jsonify({
                'success': False,
                'error': f'无{stock_code}竞价数据'
            })
        
        # 转换为AuctionData对象
        from core.models import AuctionData
        auction_data = AuctionData(
            stock_code=stock_code,
            stock_name=latest_data.get('stock_name', ''),
            market=latest_data.get('market', 'sh'),
            timestamp=datetime.fromisoformat(latest_data['timestamp']),
            auction_price=latest_data.get('auction_price', 0),
            auction_volume=latest_data.get('auction_volume', 0),
            bid_prices=latest_data.get('bid_prices', []),
            ask_prices=latest_data.get('ask_prices', []),
            bid_volumes=latest_data.get('bid_volumes', []),
            ask_volumes=latest_data.get('ask_volumes', [])
        )
        
        # 预测开盘价
        predicted_price, confidence = predictor.predict_open_price(stock_code, auction_data)
        
        return jsonify({
            'success': True,
            'stock_code': stock_code,
            'current_price': auction_data.auction_price,
            'predicted_price': predicted_price,
            'confidence': confidence
        })
    except Exception as e:
        logger.error(f"预测开盘价API失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/export-data', methods=['POST'])
def api_export_data():
    """导出数据API"""
    try:
        # 获取请求数据
        data = request.get_json()
        trade_date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        export_type = data.get('type', 'all')
        
        # 导出数据
        if export_type == 'all':
            results = exporter.export_all_data(trade_date)
        elif export_type == 'signals':
            filepath = exporter.export_auction_signals_to_csv(trade_date)
            results = {'signals': filepath}
        elif export_type == 'data':
            filepath = exporter.export_auction_data_to_csv(trade_date)
            results = {'data': filepath}
        else:
            return jsonify({
                'success': False,
                'error': f'不支持的导出类型: {export_type}'
            })
        
        return jsonify({
            'success': True,
            'message': '导出完成',
            'files': results
        })
    except Exception as e:
        logger.error(f"导出数据API失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/database-stats')
def api_database_stats():
    """获取数据库统计信息API"""
    try:
        stats = database.get_database_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        logger.error(f"获取数据库统计API失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/daily-report')
def api_daily_report():
    """获取每日报告API"""
    try:
        trade_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        report = analyzer.generate_daily_report(trade_date)
        
        return jsonify({
            'success': True,
            'report': report
        })
    except Exception as e:
        logger.error(f"获取每日报告API失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/stock-summary/<stock_code>')
def api_stock_summary(stock_code):
    """获取股票分析摘要API"""
    try:
        summary = analyzer.get_stock_analysis_summary(stock_code)
        
        return jsonify({
            'success': True,
            'summary': summary
        })
    except Exception as e:
        logger.error(f"获取{stock_code}分析摘要API失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/compare-stocks', methods=['POST'])
def api_compare_stocks():
    """比较多只股票API"""
    try:
        data = request.get_json()
        stock_codes = data.get('stock_codes', [])
        
        if not stock_codes:
            return jsonify({
                'success': False,
                'error': '缺少股票代码列表'
            })
        
        comparison = analyzer.compare_stocks(stock_codes)
        
        return jsonify({
            'success': True,
            'comparison': comparison
        })
    except Exception as e:
        logger.error(f"比较股票API失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/detect-anomalies')
def api_detect_anomalies():
    """检测异常信号API"""
    try:
        trade_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        anomalies = analyzer.detect_anomalies(trade_date)
        
        return jsonify({
            'success': True,
            'anomalies': anomalies,
            'count': len(anomalies)
        })
    except Exception as e:
        logger.error(f"检测异常信号API失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/watchlist')
def api_watchlist():
    """获取自选股列表API"""
    try:
        return jsonify({
            'success': True,
            'watchlist': WATCHLIST
        })
    except Exception as e:
        logger.error(f"获取自选股列表API失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/generate-mock-data', methods=['POST'])
def api_generate_mock_data():
    """生成模拟数据用于测试"""
    try:
        import random
        from datetime import timedelta
        
        today = datetime.now().strftime('%Y-%m-%d')
        mock_signals = []
        
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
            
            # 保存到数据库
            signal_data = {
                'stock_code': stock['code'],
                'stock_name': stock['name'],
                'signal_time': datetime.now(),
                'signal_type': signal_type,
                'signal_score': score,
                'signal_emoji': signal_emoji,
                'signal_text': signal_type,
                'predicted_open_price': predicted_open,
                'confidence': confidence,
                'analysis_details': {
                    'scores': {
                        'volume_ratio': random.randint(40, 95),
                        'price_trend': random.randint(40, 95),
                        'cancel_rate': random.randint(40, 95),
                        'bid_ask_ratio': random.randint(40, 95),
                        'seal_strength': random.randint(40, 95)
                    }
                }
            }
            
            # 保存竞价信号
            from core.models import AuctionSignal
            signal = AuctionSignal(**signal_data)
            database.save_auction_signal(signal)
            
            mock_signals.append({
                'stock_code': stock['code'],
                'stock_name': stock['name'],
                'signal_type': signal_type,
                'signal_score': score,
                'signal_emoji': signal_emoji
            })
        
        return jsonify({
            'success': True,
            'message': f'生成{len(mock_signals)}条模拟数据',
            'signals': mock_signals
        })
    except Exception as e:
        logger.error(f"生成模拟数据失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/health')
def api_health():
    """健康检查API"""
    try:
        # 检查数据库连接
        stats = database.get_database_stats()
        
        # 检查eltdx连接状态
        eltdx_status = 'connected' if collector.connected else 'disconnected'
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'connected',
            'eltdx': eltdx_status,
            'stats': stats
        })
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        })

@app.route('/api/debug')
def api_debug():
    """调试API"""
    try:
        # 直接查询数据库
        import sqlite3
        conn = sqlite3.connect(database.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM auction_signals')
        count = cursor.fetchone()[0]
        
        # 检查数据库对象状态
        conn_valid = database.conn is not None
        cursor_valid = database.cursor is not None
        
        # 尝试直接使用数据库对象的cursor
        direct_cursor_count = None
        if cursor_valid:
            try:
                database.cursor.execute('SELECT COUNT(*) FROM auction_signals')
                direct_cursor_count = database.cursor.fetchone()[0]
            except Exception as e:
                direct_cursor_count = f'Error: {str(e)}'
        
        conn.close()
        
        return jsonify({
            'success': True,
            'db_path': database.db_path,
            'direct_count': count,
            'conn_valid': conn_valid,
            'cursor_valid': cursor_valid,
            'direct_cursor_count': direct_cursor_count,
            'database_stats': database.get_database_stats(),
            'signals_via_method': len(database.get_auction_signals_by_date('2026-06-08'))
        })
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        })

@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return jsonify({
        'success': False,
        'error': '页面未找到'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    return jsonify({
        'success': False,
        'error': '服务器内部错误'
    }), 500

def run_web_server():
    """运行Web服务器"""
    try:
        logger.info(f"启动Web服务器: {WEB_HOST}:{WEB_PORT}")
        app.run(
            host=WEB_HOST,
            port=WEB_PORT,
            debug=WEB_DEBUG,
            use_reloader=False  # 避免重复加载
        )
    except Exception as e:
        logger.error(f"启动Web服务器失败: {e}")
        raise

if __name__ == '__main__':
    run_web_server()