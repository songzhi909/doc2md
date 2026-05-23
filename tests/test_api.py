import pytest
import tempfile
import os
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_scan_api_returns_file_list(client):
    """测试扫描API返回文件列表"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建测试文件
        open(os.path.join(tmpdir, 'test.pdf'), 'w').close()

        response = client.post('/api/scan', json={
            'input_path': tmpdir
        })

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert len(data['files']) == 1
        assert data['files'][0]['type'] == 'pdf'

def test_scan_api_invalid_path(client):
    """测试扫描API处理无效路径"""
    response = client.post('/api/scan', json={
        'input_path': '/nonexistent/path'
    })

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == False
    assert 'error' in data

def test_convert_api_executes_conversion(client):
    """测试转换API执行转换（本地路径模式）"""
    with tempfile.TemporaryDirectory() as input_dir:
        with tempfile.TemporaryDirectory() as output_dir:
            # 创建测试文件
            with open(os.path.join(input_dir, 'test.json'), 'w', encoding='utf-8') as f:
                f.write('{"key": "value"}')

            response = client.post('/api/convert', json={
                'input_path': input_dir,
                'output_path': output_dir
            })

            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] == True
            assert 'converted' in data
            assert 'failed' in data

def test_convert_api_file_upload(client):
    """测试转换API文件上传模式"""
    with tempfile.TemporaryDirectory() as output_dir:
        # 创建测试文件内容
        import io
        file_content = '{"key": "value"}'
        file_data = (io.BytesIO(file_content.encode('utf-8')), 'test_folder/test.json')

        response = client.post('/api/convert',
            data={
                'output_path': output_dir,
                'files': file_data
            },
            content_type='multipart/form-data'
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert 'converted' in data
        assert 'failed' in data
