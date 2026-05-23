import os
import tempfile
import shutil
from flask import Flask, render_template, request, jsonify
from converter import scan_files, convert_batch, convert_file
from logger import logger

app = Flask(__name__)

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
                **result
            })
        except Exception as e:
            logger.error(f'转换过程出错: {str(e)}', exc_info=True)
            return jsonify({
                'success': False,
                'error': str(e)
            })

if __name__ == '__main__':
    logger.info('doc2md 服务启动')
    app.run(debug=True, port=5000)
    logger.info('doc2md 服务停止')
