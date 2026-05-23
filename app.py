import warnings
warnings.filterwarnings('ignore', category=RuntimeWarning)

import os
import tempfile
import shutil
import zipfile
import json
from io import BytesIO
from flask import Flask, render_template, request, jsonify, send_file, Response
from converter import scan_files, convert_batch, convert_file, convert_batch_with_progress
from logger import logger
from config import get_config, save_config

app = Flask(__name__)
config = get_config()

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

    if not input_path or not os.path.isdir(input_path):
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

        try:
            # 创建临时目录保存上传的文件
            with tempfile.TemporaryDirectory() as temp_dir:
                logger.debug(f'创建临时目录: {temp_dir}')

                # 保存上传的文件，保持目录结构
                for file in files:
                    # file.webkitRelativePath 格式: "文件夹名/子目录/文件名"
                    # 我们需要去掉第一级文件夹名
                    relative_path = file.filename
                    file_path = os.path.join(temp_dir, relative_path)

                    # 确保目录存在
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)

                    # 保存文件
                    file.save(file_path)
                    logger.debug(f'保存文件: {relative_path}')

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
    else:
        # 本地路径模式
        data = request.get_json()
        input_path = data.get('input_path', '')
        output_path = data.get('output_path', './output')

        logger.info(f'收到本地路径转换请求: {input_path} -> {output_path}')

        if not input_path or not os.path.isdir(input_path):
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
        temp_dir = tempfile.mkdtemp()

        # 保存上传的文件，保持目录结构
        for file in files:
            relative_path = file.filename
            file_path = os.path.join(temp_dir, relative_path)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            file.save(file_path)

        # 确保输出目录存在
        os.makedirs(output_path, exist_ok=True)

        def generate():
            try:
                for event in convert_batch_with_progress(temp_dir, output_path):
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            finally:
                # 清理临时目录
                try:
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass

        return Response(generate(), mimetype='text/event-stream')
    else:
        # 本地路径模式
        data = request.get_json()
        input_path = data.get('input_path', '')
        output_path = data.get('output_path', './output')

        logger.info(f'收到本地路径转换请求（流式）: {input_path} -> {output_path}')

        if not input_path or not os.path.isdir(input_path):
            return jsonify({
                'success': False,
                'error': '无效的输入路径'
            })

        # 确保输出目录存在
        os.makedirs(output_path, exist_ok=True)

        def generate():
            for event in convert_batch_with_progress(input_path, output_path):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

        return Response(generate(), mimetype='text/event-stream')

@app.route('/api/export', methods=['POST'])
def api_export():
    """导出输出目录为 ZIP 文件"""
    data = request.get_json()
    output_path = data.get('output_path', '')

    if not output_path or not os.path.isdir(output_path):
        return jsonify({
            'success': False,
            'error': '输出路径不存在'
        })

    try:
        # 创建内存中的 ZIP 文件
        memory_file = BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(output_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, output_path)
                    zf.write(file_path, arcname)

        memory_file.seek(0)
        logger.info(f'导出 ZIP: {output_path}')

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
    """浏览文件夹，返回子目录列表"""
    data = request.get_json()
    path = data.get('path', '')

    # 如果路径为空，返回驱动器列表（Windows）或根目录
    if not path:
        if os.name == 'nt':
            # Windows: 返回可用驱动器
            import string
            drives = []
            for letter in string.ascii_uppercase:
                drive = f'{letter}:\\'
                if os.path.exists(drive):
                    drives.append({
                        'name': drive,
                        'path': drive,
                        'is_dir': True
                    })
            return jsonify({
                'success': True,
                'items': drives,
                'current_path': ''
            })
        else:
            path = '/'

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
            items.append({
                'name': item,
                'path': item_path,
                'is_dir': os.path.isdir(item_path)
            })

        # 排序：目录在前，文件在后
        items.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))

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
    """保存配置"""
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
