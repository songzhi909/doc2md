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

def test_browse_api_returns_directories(client):
    """测试浏览API返回目录列表"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建子目录和文件
        os.makedirs(os.path.join(tmpdir, 'subdir1'))
        os.makedirs(os.path.join(tmpdir, 'subdir2'))
        open(os.path.join(tmpdir, 'file.txt'), 'w').close()

        response = client.post('/api/browse', json={
            'path': tmpdir
        })

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert len(data['items']) == 3
        # 目录应该排在前面
        assert data['items'][0]['is_dir'] == True
        assert data['items'][1]['is_dir'] == True
        assert data['items'][2]['is_dir'] == False

def test_browse_api_invalid_path(client):
    """测试浏览API处理无效路径"""
    response = client.post('/api/browse', json={
        'path': '/nonexistent/path'
    })

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == False
    assert 'error' in data

def test_browse_api_empty_path(client):
    """测试浏览API空路径返回驱动器列表"""
    response = client.post('/api/browse', json={
        'path': ''
    })

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True
    # Windows 应该返回驱动器列表
    if os.name == 'nt':
        assert len(data['items']) > 0
        assert data['items'][0]['path'].endswith(':\\')

def test_config_api(client):
    """测试配置API"""
    response = client.get('/api/config')

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True
    assert 'config' in data
    assert 'server' in data['config']
    assert 'supported_extensions' in data['config']

def test_export_api_returns_zip(client):
    """测试导出API返回ZIP文件"""
    import zipfile
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建测试文件
        with open(os.path.join(tmpdir, 'test1.md'), 'w') as f:
            f.write('# Test 1')
        with open(os.path.join(tmpdir, 'test2.md'), 'w') as f:
            f.write('# Test 2')

        response = client.post('/api/export', json={
            'output_path': tmpdir
        })

        assert response.status_code == 200
        assert response.content_type == 'application/zip'

        # 验证 ZIP 内容
        import io
        zip_data = io.BytesIO(response.data)
        with zipfile.ZipFile(zip_data, 'r') as zf:
            names = zf.namelist()
            assert 'test1.md' in names
            assert 'test2.md' in names

def test_export_api_invalid_path(client):
    """测试导出API处理无效路径"""
    response = client.post('/api/export', json={
        'output_path': '/nonexistent/path'
    })

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == False
    assert 'error' in data
