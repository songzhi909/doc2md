import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {
    'pdf', 'docx', 'xlsx', 'pptx', 'html', 'csv', 'json', 'xml', 'epub'
}

def scan_files(input_path: str) -> List[Dict[str, Any]]:
    """
    扫描输入文件夹，返回支持的文件列表

    Args:
        input_path: 输入文件夹路径

    Returns:
        list: 文件列表，每个元素是 dict，包含 path, size, type

    Raises:
        ValueError: 输入路径不存在或不是目录
    """
    if not os.path.isdir(input_path):
        raise ValueError(f"输入路径不存在或不是目录: {input_path}")

    files = []

    for root, dirs, filenames in os.walk(input_path):
        for filename in filenames:
            ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
            if ext in SUPPORTED_EXTENSIONS:
                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, input_path)
                try:
                    size = os.path.getsize(full_path)
                except OSError as e:
                    logger.warning(f"无法获取文件大小 {full_path}: {e}")
                    continue

                files.append({
                    'path': rel_path,
                    'size': size,
                    'type': ext
                })

    return files
