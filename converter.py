import os

SUPPORTED_EXTENSIONS = {
    'pdf', 'docx', 'xlsx', 'pptx', 'html', 'csv', 'json', 'xml', 'epub'
}

def scan_files(input_path):
    """
    扫描输入文件夹，返回支持的文件列表

    Args:
        input_path: 输入文件夹路径

    Returns:
        list: 文件列表，每个元素是 dict，包含 path, size, type
    """
    files = []

    for root, dirs, filenames in os.walk(input_path):
        for filename in filenames:
            ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
            if ext in SUPPORTED_EXTENSIONS:
                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, input_path)
                size = os.path.getsize(full_path)

                files.append({
                    'path': rel_path,
                    'size': size,
                    'type': ext
                })

    return files
