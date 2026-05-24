import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from config import get_config, get_base_dir

def setup_logger(name='doc2md'):
    """配置日志记录器"""
    config = get_config()
    log_config = config.get('log', {})
    log_dir = os.path.join(get_base_dir(), log_config.get('dir', 'logs'))

    # 创建日志目录
    os.makedirs(log_dir, exist_ok=True)

    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # 避免重复添加处理器
    if logger.handlers:
        return logger

    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 日志级别映射
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }

    # 控制台处理器
    console_level = level_map.get(log_config.get('console_level', 'INFO'), logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件处理器（按日期命名，自动轮转）
    file_level = level_map.get(log_config.get('file_level', 'DEBUG'), logging.DEBUG)
    log_file = os.path.join(log_dir, f'doc2md_{datetime.now().strftime("%Y%m%d")}.log')
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=log_config.get('max_bytes', 10*1024*1024),
        backupCount=log_config.get('backup_count', 5),
        encoding='utf-8'
    )
    file_handler.setLevel(file_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

# 创建默认日志记录器
logger = setup_logger()
