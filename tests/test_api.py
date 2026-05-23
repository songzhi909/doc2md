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
