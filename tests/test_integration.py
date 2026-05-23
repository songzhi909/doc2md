import pytest
import tempfile
import os
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_full_workflow(client):
    """测试完整工作流程：扫描 -> 转换"""
    with tempfile.TemporaryDirectory() as input_dir:
        with tempfile.TemporaryDirectory() as output_dir:
            # 创建测试文件（使用支持的格式）
            with open(os.path.join(input_dir, 'test.json'), 'w', encoding='utf-8') as f:
                f.write('{"key": "value"}')

            # 1. 扫描
            scan_response = client.post('/api/scan', json={
                'input_path': input_dir
            })
            scan_data = scan_response.get_json()
            assert scan_data['success'] == True
            assert len(scan_data['files']) == 1
            assert scan_data['files'][0]['type'] == 'json'

            # 2. 转换
            convert_response = client.post('/api/convert', json={
                'input_path': input_dir,
                'output_path': output_dir
            })
            convert_data = convert_response.get_json()
            assert convert_data['success'] == True
            assert convert_data['converted'] == 1
            assert convert_data['failed'] == 0
            assert os.path.exists(os.path.join(output_dir, 'test.md'))
