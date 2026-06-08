# 定时任务调度模块
import time
import logging
from datetime import datetime, time as dt_time, timedelta
from typing import Callable, List, Dict, Any
import threading
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import AUCTION_START, AUCTION_END, COLLECTION_INTERVAL
from core.collector import AuctionCollector
from storage.database import AuctionDatabase

logger = logging.getLogger(__name__)

class AuctionScheduler:
    """竞价数据采集调度器"""
    
    def __init__(self, collector: AuctionCollector, database: AuctionDatabase):
        """
        初始化调度器
        
        Args:
            collector: 竞价数据采集器
            database: 数据库实例
        """
        self.collector = collector
        self.database = database
        self.scheduler = BackgroundScheduler()
        self.running = False
        self.collection_job = None
        
    def start(self):
        """启动调度器"""
        if self.running:
            logger.warning("调度器已在运行中")
            return
        
        try:
            # 添加竞价数据采集任务
            self.scheduler.add_job(
                self.collect_auction_data_job,
                trigger=CronTrigger(
                    hour=9,
                    minute=15,
                    second=0,
                    timezone='Asia/Shanghai'
                ),
                id='auction_collection_start',
                name='竞价数据采集开始',
                replace_existing=True
            )
            
            # 添加每5秒采集任务（在竞价时间内）
            self.scheduler.add_job(
                self.collect_auction_data_job,
                trigger=IntervalTrigger(
                    seconds=COLLECTION_INTERVAL,
                    start_date=datetime.now().replace(hour=9, minute=15, second=0),
                    end_date=datetime.now().replace(hour=9, minute=25, second=0),
                    timezone='Asia/Shanghai'
                ),
                id='auction_collection_interval',
                name='竞价数据定时采集',
                replace_existing=True
            )
            
            # 添加9:24推送任务
            self.scheduler.add_job(
                self.push_auction_conclusion,
                trigger=CronTrigger(
                    hour=9,
                    minute=24,
                    second=0,
                    timezone='Asia/Shanghai'
                ),
                id='auction_conclusion_push',
                name='竞价结论推送',
                replace_existing=True
            )
            
            self.scheduler.start()
            self.running = True
            logger.info("竞价数据采集调度器已启动")
            
        except Exception as e:
            logger.error(f"启动调度器失败: {e}")
            raise
    
    def stop(self):
        """停止调度器"""
        if not self.running:
            return
        
        try:
            self.scheduler.shutdown()
            self.running = False
            logger.info("竞价数据采集调度器已停止")
        except Exception as e:
            logger.error(f"停止调度器失败: {e}")
    
    def collect_auction_data_job(self):
        """竞价数据采集任务"""
        try:
            # 检查是否在竞价时间内
            if not self.collector.is_auction_time():
                logger.info("当前不在竞价时间内，跳过采集")
                return
            
            logger.info("开始采集竞价数据...")
            
            # 批量采集竞价数据
            auction_data_list = self.collector.collect_auction_batch()
            
            if not auction_data_list:
                logger.warning("未采集到竞价数据")
                return
            
            # 存储到数据库
            for data in auction_data_list:
                try:
                    self.database.save_auction_data(data)
                    logger.debug(f"保存{data['stock_code']}竞价数据成功")
                except Exception as e:
                    logger.error(f"保存{data['stock_code']}竞价数据失败: {e}")
            
            logger.info(f"竞价数据采集完成，共{len(auction_data_list)}条记录")
            
        except Exception as e:
            logger.error(f"竞价数据采集任务异常: {e}")
    
    def push_auction_conclusion(self):
        """推送竞价结论"""
        try:
            logger.info("开始生成竞价结论...")
            
            # 获取今日竞价数据
            today = datetime.now().strftime("%Y-%m-%d")
            auction_data = self.database.get_auction_data_by_date(today)
            
            if not auction_data:
                logger.warning("今日无竞价数据")
                return
            
            # 这里可以调用信号分析引擎生成结论
            # 暂时记录日志
            logger.info(f"生成竞价结论，共{len(auction_data)}只股票数据")
            
            # TODO: 调用信号分析引擎
            # TODO: 推送到腾讯文档
            
        except Exception as e:
            logger.error(f"推送竞价结论异常: {e}")
    
    def run_manual_collection(self, duration_minutes: int = 10):
        """
        手动运行竞价数据采集
        
        Args:
            duration_minutes: 采集持续时间（分钟）
        """
        try:
            logger.info(f"开始手动采集竞价数据，持续{duration_minutes}分钟...")
            
            # 在后台线程中运行采集
            def collection_thread():
                all_data = []
                start_time = datetime.now()
                end_time = start_time + timedelta(minutes=duration_minutes)
                
                while datetime.now() < end_time:
                    # 检查是否在竞价时间内
                    if not self.collector.is_auction_time():
                        logger.info("当前不在竞价时间内，等待...")
                        time.sleep(30)
                        continue
                    
                    # 采集数据
                    batch_data = self.collector.collect_auction_batch()
                    all_data.extend(batch_data)
                    
                    # 存储到数据库
                    for data in batch_data:
                        try:
                            self.database.save_auction_data(data)
                        except Exception as e:
                            logger.error(f"保存数据失败: {e}")
                    
                    # 等待下一次采集
                    time.sleep(COLLECTION_INTERVAL)
                
                logger.info(f"手动采集完成，共采集{len(all_data)}条记录")
            
            # 启动后台线程
            thread = threading.Thread(target=collection_thread, daemon=True)
            thread.start()
            
            return thread
            
        except Exception as e:
            logger.error(f"手动采集异常: {e}")
            return None

class AuctionTaskManager:
    """竞价任务管理器"""
    
    def __init__(self):
        """初始化任务管理器"""
        self.tasks = {}
        self.running_tasks = {}
        
    def add_task(self, task_id: str, task_func: Callable, task_name: str = ""):
        """
        添加任务
        
        Args:
            task_id: 任务ID
            task_func: 任务函数
            task_name: 任务名称
        """
        self.tasks[task_id] = {
            'func': task_func,
            'name': task_name or task_id,
            'created_at': datetime.now()
        }
        logger.info(f"添加任务: {task_id}")
    
    def run_task(self, task_id: str, *args, **kwargs) -> bool:
        """
        运行任务
        
        Args:
            task_id: 任务ID
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            bool: 是否成功启动
        """
        if task_id not in self.tasks:
            logger.error(f"任务不存在: {task_id}")
            return False
        
        if task_id in self.running_tasks:
            logger.warning(f"任务已在运行: {task_id}")
            return False
        
        try:
            task_info = self.tasks[task_id]
            task_func = task_info['func']
            
            # 在后台线程中运行任务
            def task_wrapper():
                try:
                    logger.info(f"开始运行任务: {task_id}")
                    result = task_func(*args, **kwargs)
                    logger.info(f"任务完成: {task_id}")
                    return result
                except Exception as e:
                    logger.error(f"任务异常: {task_id} - {e}")
                finally:
                    if task_id in self.running_tasks:
                        del self.running_tasks[task_id]
            
            thread = threading.Thread(target=task_wrapper, daemon=True)
            thread.start()
            
            self.running_tasks[task_id] = {
                'thread': thread,
                'started_at': datetime.now()
            }
            
            logger.info(f"任务已启动: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"启动任务失败: {task_id} - {e}")
            return False
    
    def stop_task(self, task_id: str) -> bool:
        """
        停止任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功停止
        """
        if task_id not in self.running_tasks:
            logger.warning(f"任务未在运行: {task_id}")
            return False
        
        try:
            # 注意：Python线程无法强制停止
            # 这里只是从运行列表中移除
            del self.running_tasks[task_id]
            logger.info(f"任务已停止: {task_id}")
            return True
        except Exception as e:
            logger.error(f"停止任务失败: {task_id} - {e}")
            return False
    
    def get_running_tasks(self) -> List[str]:
        """
        获取正在运行的任务列表
        
        Returns:
            List[str]: 任务ID列表
        """
        return list(self.running_tasks.keys())
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            Dict: 任务状态信息
        """
        if task_id not in self.tasks:
            return {'status': 'not_found'}
        
        task_info = self.tasks[task_id]
        
        if task_id in self.running_tasks:
            running_info = self.running_tasks[task_id]
            return {
                'status': 'running',
                'name': task_info['name'],
                'started_at': running_info['started_at'].isoformat(),
                'thread_alive': running_info['thread'].is_alive()
            }
        else:
            return {
                'status': 'idle',
                'name': task_info['name'],
                'created_at': task_info['created_at'].isoformat()
            }

# 测试代码
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建采集器和数据库
    collector = AuctionCollector()
    database = AuctionDatabase()
    
    # 连接eltdx服务器
    if collector.connect():
        print("连接eltdx服务器成功")
        
        # 创建调度器
        scheduler = AuctionScheduler(collector, database)
        
        # 测试手动采集
        print("测试手动采集竞价数据（10秒）...")
        thread = scheduler.run_manual_collection(duration_minutes=0.17)  # 10秒
        
        if thread:
            # 等待采集完成
            thread.join(timeout=15)
            print("手动采集测试完成")
        
        # 断开连接
        collector.disconnect()
    else:
        print("连接eltdx服务器失败")