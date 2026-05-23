import os
import tempfile
import shutil
from flask import Flask, render_template, request, jsonify
from converter import scan_files, convert_batch, convert_file

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/scan', methods=['POST'])
def api_scan():
    """扫描文件夹，返回支持的文件列表"""
    data = request.get_json()
    input_path = data.get('input_path', '')

    if not input_path or not os.path.isdir(input_path):
        return jsonify({
            'success': False,
            'error': '无效的输入路径'
        })

    try:
        files = scan_files(input_path)
        return jsonify({
            'success': True,
            'files': files,
            'total': len(files)
        })
    except Exception as e:
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

        if not files:
            return jsonify({
                'success': False,
                'error': '没有上传文件'
            })

        try:
            # 创建临时目录保存上传的文件
            with tempfile.TemporaryDirectory() as temp_dir:
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

                # 确保输出目录存在
                os.makedirs(output_path, exist_ok=True)

                # 执行批量转换
                result = convert_batch(temp_dir, output_path)

                return jsonify({
                    'success': True,
                    **result
                })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            })
    else:
        # 本地路径模式
        data = request.get_json()
        input_path = data.get('input_path', '')
        output_path = data.get('output_path', './output')

        if not input_path or not os.path.isdir(input_path):
            return jsonify({
                'success': False,
                'error': '无效的输入路径'
            })

        try:
            # 确保输出目录存在
            os.makedirs(output_path, exist_ok=True)

            result = convert_batch(input_path, output_path)
            return jsonify({
                'success': True,
                **result
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
