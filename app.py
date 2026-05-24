import warnings
warnings.filterwarnings('ignore', message='.*ffmpeg.*', category=RuntimeWarning)
warnings.filterwarnings('ignore', message='.*FontBBox.*', category=UserWarning)

import os
import sys
import tempfile
import shutil
import zipfile
import json
from io import BytesIO
from flask import Flask, render_template, request, jsonify, send_file, Response
from converter import scan_files, convert_batch, convert_file, convert_batch_with_progress
from logger import logger
from config import get_config, save_config, get_base_dir

# 获取基础路径（支持 PyInstaller 打包）
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
    TEMPLATE_DIR = os.path.join(sys._MEIPASS, 'templates')
    STATIC_DIR = os.path.join(sys._MEIPASS, 'static')
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
    STATIC_DIR = os.path.join(BASE_DIR, 'static')

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
config = get_config()

# 临时目录配置
TEMP_DIR = os.path.join(BASE_DIR, config.get('temp', {}).get('dir', './temp'))
os.makedirs(TEMP_DIR, exist_ok=True)

# 安全配置
MAX_ZIP_SIZE = 500 * 1024 * 1024  # 500MB
MAX_ZIP_FILES = 10000
ALLOWED_BROWSE_ROOTS = [BASE_DIR, os.path.expanduser('~')]

def _is_path_allowed(path: str) -> bool:
    """检查路径是否在允许的范围内"""
    real_path = os.path.realpath(path)
    for root in ALLOWED_BROWSE_ROOTS:
        if real_path.startswith(os.path.realpath(root)):
            return True
    # 也允许访问系统临时目录
    temp_dir = os.path.realpath(tempfile.gettempdir())
    if real_path.startswith(temp_dir):
        return True
    return False

def _save_uploaded_files(files, temp_dir: str) -> None:
    """保存上传的文件到临时目录，保持目录结构"""
    for file in files:
        relative_path = file.filename
        file_path = os.path.join(temp_dir, relative_path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        file.save(file_path)
        logger.debug(f'保存文件: {relative_path}')

@app.route('/')
def index():
    logger.info('访问首页')
    return render_template('index.html')

@app.route('/api/scan', methods=['POST'])
def api_scan():
    """扫描文件夹，返回支持的文件列表"""
    data = request.get_json()
    input_path = data.get('input_path', '')

    logger.info(f'开始扫描文件夹: {input_path}')

    # 安全检查：验证路径在允许范围内
    if not input_path or not _is_path_allowed(input_path):
        logger.warning(f'不允许访问的路径: {input_path}')
        return jsonify({
            'success': False,
            'error': '不允许访问该路径'
        })

    if not os.path.isdir(input_path):
        logger.warning(f'无效的输入路径: {input_path}')
        return jsonify({
            'success': False,
            'error': '无效的输入路径'
        })

    try:
        files = scan_files(input_path)
        logger.info(f'扫描完成，找到 {len(files)} 个支持的文件')
        return jsonify({
            'success': True,
            'files': files,
            'total': len(files)
        })
    except Exception as e:
        logger.error(f'扫描失败: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/convert', methods=['POST'])
def api_convert():
    """执行批量转换（支持文件上传或本地路径）"""
    # 检查是否是文件上传
    if 'files' in request.files:
        # 文件上传模式
        files = request.files.getlist('files')
        output_path = request.form.get('output_path', './output')

        logger.info(f'收到文件上传请求，共 {len(files)} 个文件，输出路径: {output_path}')

        if not files:
            logger.warning('没有上传文件')
            return jsonify({
                'success': False,
                'error': '没有上传文件'
            })

        temp_dir = tempfile.mkdtemp(dir=TEMP_DIR)
        try:
            logger.debug(f'创建临时目录: {temp_dir}')
            _save_uploaded_files(files, temp_dir)

            # 确保输出目录存在
            os.makedirs(output_path, exist_ok=True)

            # 执行批量转换
            logger.info('开始批量转换...')
            result = convert_batch(temp_dir, output_path)

            logger.info(f'转换完成: 成功 {result["converted"]} 个, 失败 {result["failed"]} 个')
            if result['failures']:
                for failure in result['failures']:
                    logger.warning(f'转换失败 - {failure["file"]}: {failure["error"]}')

            return jsonify({
                'success': True,
                'output_path': os.path.abspath(output_path),
                **result
            })
        except Exception as e:
            logger.error(f'转换过程出错: {str(e)}', exc_info=True)
            return jsonify({
                'success': False,
                'error': str(e)
            })
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    else:
        # 本地路径模式
        data = request.get_json()
        input_path = data.get('input_path', '')
        output_path = data.get('output_path', './output')

        logger.info(f'收到本地路径转换请求: {input_path} -> {output_path}')

        # 安全检查：验证路径在允许范围内
        if not input_path or not _is_path_allowed(input_path):
            logger.warning(f'不允许访问的路径: {input_path}')
            return jsonify({
                'success': False,
                'error': '不允许访问该路径'
            })

        if not os.path.isdir(input_path):
            logger.warning(f'无效的输入路径: {input_path}')
            return jsonify({
                'success': False,
                'error': '无效的输入路径'
            })

        try:
            # 确保输出目录存在
            os.makedirs(output_path, exist_ok=True)

            # 执行批量转换
            logger.info('开始批量转换...')
            result = convert_batch(input_path, output_path)

            logger.info(f'转换完成: 成功 {result["converted"]} 个, 失败 {result["failed"]} 个')
            if result['failures']:
                for failure in result['failures']:
                    logger.warning(f'转换失败 - {failure["file"]}: {failure["error"]}')

            return jsonify({
                'success': True,
                'output_path': os.path.abspath(output_path),
                **result
            })
        except Exception as e:
            logger.error(f'转换过程出错: {str(e)}', exc_info=True)
            return jsonify({
                'success': False,
                'error': str(e)
            })

@app.route('/api/convert-stream', methods=['POST'])
def api_convert_stream():
    """执行批量转换（带进度流）"""
    # 检查是否是文件上传
    if 'files' in request.files:
        # 文件上传模式
        files = request.files.getlist('files')
        output_path = request.form.get('output_path', './output')

        logger.info(f'收到文件上传请求（流式），共 {len(files)} 个文件，输出路径: {output_path}')

        if not files:
            return jsonify({
                'success': False,
                'error': '没有上传文件'
            })

        # 创建临时目录保存上传的文件
        temp_dir = tempfile.mkdtemp(dir=TEMP_DIR)
        _save_uploaded_files(files, temp_dir)

        # 确保输出目录存在
        os.makedirs(output_path, exist_ok=True)

        def generate():
            try:
                for event in convert_batch_with_progress(temp_dir, output_path):
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            finally:
                # 清理临时目录
                shutil.rmtree(temp_dir, ignore_errors=True)

        return Response(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'
            }
        )
    else:
        # 本地路径模式
        data = request.get_json()
        input_path = data.get('input_path', '')
        output_path = data.get('output_path', './output')

        logger.info(f'收到本地路径转换请求（流式）: {input_path} -> {output_path}')

        # 安全检查：验证路径在允许范围内
        if not input_path or not _is_path_allowed(input_path):
            return jsonify({
                'success': False,
                'error': '不允许访问该路径'
            })

        if not os.path.isdir(input_path):
            return jsonify({
                'success': False,
                'error': '无效的输入路径'
            })

        # 确保输出目录存在
        os.makedirs(output_path, exist_ok=True)

        def generate():
            for event in convert_batch_with_progress(input_path, output_path):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

        return Response(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'
            }
        )

@app.route('/api/export', methods=['POST'])
def api_export():
    """导出输出目录为 ZIP 文件"""
    data = request.get_json()
    output_path = data.get('output_path', '')

    # 安全检查：验证路径在允许范围内
    if not output_path or not _is_path_allowed(output_path):
        return jsonify({
            'success': False,
            'error': '不允许访问该路径'
        })

    if not os.path.isdir(output_path):
        return jsonify({
            'success': False,
            'error': '输出路径不存在'
        })

    try:
        # 预检查文件数量和大小
        file_count = 0
        total_size = 0
        for root, dirs, files in os.walk(output_path):
            for file in files:
                file_count += 1
                if file_count > MAX_ZIP_FILES:
                    return jsonify({
                        'success': False,
                        'error': f'文件数量超过限制（最大 {MAX_ZIP_FILES} 个）'
                    })
                total_size += os.path.getsize(os.path.join(root, file))
                if total_size > MAX_ZIP_SIZE:
                    return jsonify({
                        'success': False,
                        'error': f'文件总大小超过限制（最大 {MAX_ZIP_SIZE // 1024 // 1024}MB）'
                    })

        # 创建内存中的 ZIP 文件
        memory_file = BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(output_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, output_path)
                    zf.write(file_path, arcname)

        memory_file.seek(0)
        logger.info(f'导出 ZIP: {output_path}，包含 {file_count} 个文件')

        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name='converted_docs.zip'
        )
    except Exception as e:
        logger.error(f'导出失败: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/browse', methods=['POST'])
def api_browse():
    """浏览文件夹，返回子目录列表（支持任意路径）"""
    data = request.get_json()
    path = data.get('path', '')

    # 如果路径为空，返回系统根目录
    if not path:
        items = []
        if os.name == 'nt':
            # Windows: 列出所有磁盘分区
            import string
            for letter in string.ascii_uppercase:
                drive = f'{letter}:\\'
                if os.path.exists(drive):
                    items.append({
                        'name': drive,
                        'path': drive,
                        'is_dir': True
                    })
        else:
            # Linux/Mac: 返回根目录
            items.append({
                'name': '/',
                'path': '/',
                'is_dir': True
            })
        return jsonify({
            'success': True,
            'items': items,
            'current_path': ''
        })

    # 规范化路径
    path = os.path.normpath(path)

    if not os.path.exists(path):
        return jsonify({
            'success': False,
            'error': f'路径不存在: {path}'
        })

    if not os.path.isdir(path):
        return jsonify({
            'success': False,
            'error': f'不是目录: {path}'
        })

    try:
        items = []
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            # 只显示目录（文件浏览器只需要选择目录）
            if os.path.isdir(item_path):
                items.append({
                    'name': item,
                    'path': item_path,
                    'is_dir': True
                })

        # 排序：按名称排序
        items.sort(key=lambda x: x['name'].lower())

        return jsonify({
            'success': True,
            'items': items,
            'current_path': path
        })
    except PermissionError:
        return jsonify({
            'success': False,
            'error': f'没有权限访问: {path}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/config', methods=['GET'])
def api_get_config():
    """获取配置"""
    return jsonify({
        'success': True,
        'config': config
    })

@app.route('/api/config', methods=['POST'])
def api_save_config():
    """保存配置（仅限本地访问）"""
    # 安全检查：只允许本地访问
    if request.remote_addr not in ('127.0.0.1', '::1', 'localhost'):
        return jsonify({
            'success': False,
            'error': '配置修改仅限本地访问'
        }), 403

    data = request.get_json()
    if not data:
        return jsonify({
            'success': False,
            'error': '无效的配置数据'
        })

    try:
        save_config(data)
        global config
        config = get_config()
        return jsonify({
            'success': True,
            'message': '配置已保存'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    server_config = config.get('server', {})
    host = server_config.get('host', '127.0.0.1')
    port = server_config.get('port', 5000)
    debug = server_config.get('debug', True)

    logger.info(f'doc2md 服务启动: {host}:{port}')
    app.run(host=host, port=port, debug=debug)
    logger.info('doc2md 服务停止')
