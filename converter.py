import os
from typing import List, Dict, Any
from markitdown import MarkItDown
from logger import logger

SUPPORTED_EXTENSIONS = {
    'pdf', 'docx', 'xlsx', 'pptx', 'html', 'csv', 'json', 'xml', 'epub'
}

_md = MarkItDown()

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

    logger.info(f'开始扫描文件夹: {input_path}')
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

    logger.info(f'扫描完成，找到 {len(files)} 个支持的文件')
    return files

def convert_file(input_file: str, output_file: str, md: MarkItDown = None) -> Dict[str, Any]:
    """
    转换单个文件为Markdown

    Args:
        input_file: 输入文件路径
        output_file: 输出markdown文件路径
        md: MarkItDown实例（可选，默认使用模块级单例）

    Returns:
        dict: {'success': bool, 'error': str or None}
    """
    if md is None:
        md = _md

    if not os.path.exists(input_file):
        return {'success': False, 'error': f'输入文件不存在: {input_file}'}

    try:
        result = md.convert(input_file)

        # 确保输出目录存在
        output_dir = os.path.dirname(output_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        # 写入markdown文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.text_content)

        logger.info(f"转换成功: {input_file} -> {output_file}")
        return {'success': True, 'error': None}
    except PermissionError as e:
        return {'success': False, 'error': f'权限不足: {e}'}
    except Exception as e:
        logger.exception(f"转换失败 {input_file}")
        return {'success': False, 'error': f'转换失败: {e}'}

def convert_batch(input_path: str, output_path: str) -> Dict[str, Any]:
    """
    批量转换文件夹中的所有支持文件

    Args:
        input_path: 输入文件夹路径
        output_path: 输出文件夹路径

    Returns:
        dict: {'converted': int, 'failed': int, 'failures': list}
    """
    if not os.path.isdir(input_path):
        logger.error(f'输入路径不存在或不是目录: {input_path}')
        return {
            'converted': 0,
            'failed': 1,
            'failures': [{'file': input_path, 'error': f'输入路径不存在或不是目录: {input_path}'}]
        }

    logger.info(f'开始批量转换: {input_path} -> {output_path}')
    files = scan_files(input_path)
    converted = 0
    failed = 0
    failures = []

    for i, file_info in enumerate(files, 1):
        input_file = os.path.join(input_path, file_info['path'])
        # 输出文件扩展名改为.md（对多点文件名如 archive.tar.gz 会产生 archive.tar.md）
        output_rel = file_info['path'].rsplit('.', 1)[0] + '.md'
        output_file = os.path.join(output_path, output_rel)

        logger.debug(f'[{i}/{len(files)}] 转换中: {file_info["path"]}')
        result = convert_file(input_file, output_file)

        if result['success']:
            converted += 1
            logger.debug(f'[{i}/{len(files)}] 转换成功: {file_info["path"]}')
        else:
            failed += 1
            failures.append({
                'file': file_info['path'],
                'error': result['error']
            })
            logger.warning(f'[{i}/{len(files)}] 转换失败: {file_info["path"]} - {result["error"]}')

    logger.info(f'批量转换完成: 成功 {converted} 个, 失败 {failed} 个')
    return {
        'converted': converted,
        'failed': failed,
        'failures': failures
    }
