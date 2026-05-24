import json
import os
import sys

_config = None

def get_base_dir():
    """获取基础路径（支持 PyInstaller 打包）"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def load_config(config_path=None):
    """加载配置文件"""
    global _config
    if config_path is None:
        config_path = os.path.join(get_base_dir(), 'config.json')

    if not os.path.exists(config_path):
        _config = get_default_config()
        return _config

    with open(config_path, 'r', encoding='utf-8') as f:
        _config = json.load(f)
    return _config

def get_config():
    """获取配置，如果未加载则自动加载"""
    global _config
    if _config is None:
        load_config()
    return _config

def get_default_config():
    """返回默认配置"""
    return {
        "server": {
            "host": "127.0.0.1",
            "port": 5000,
            "debug": True
        },
        "output": {
            "default_path": "./output"
        },
        "temp": {
            "dir": "./temp"
        },
        "supported_extensions": [
            "pdf", "doc", "docx", "xlsx", "pptx",
            "csv", "json", "xml",
            "html", "htm",
            "epub",
            "txt", "md"
        ],
        "log": {
            "dir": "logs",
            "max_bytes": 10485760,
            "backup_count": 5,
            "console_level": "INFO",
            "file_level": "DEBUG"
        }
    }

def save_config(config, config_path=None):
    """保存配置到文件"""
    global _config
    if config_path is None:
        config_path = os.path.join(get_base_dir(), 'config.json')
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)
    _config = config

# 启动时加载配置
load_config()
