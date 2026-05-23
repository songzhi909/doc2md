import os
from flask import Flask, render_template, request, jsonify
from converter import scan_files, convert_batch

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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
