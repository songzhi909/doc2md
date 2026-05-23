import os
import tempfile
import pytest
from converter import scan_files

def test_scan_files_finds_supported_formats():
    """测试扫描能找到所有支持的格式"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建测试文件
        test_files = [
            'test.pdf',
            'test.docx',
            'test.xlsx',
            'test.pptx',
            'test.html',
            'test.csv',
            'test.json',
            'test.xml',
            'test.epub',
            'test.txt',  # 不支持的格式
        ]
        for f in test_files:
            open(os.path.join(tmpdir, f), 'w').close()

        result = scan_files(tmpdir)

        # 应该找到9个支持的文件，排除.txt
        assert len(result) == 9
        assert all(f['type'] in ['pdf', 'docx', 'xlsx', 'pptx', 'html', 'csv', 'json', 'xml', 'epub'] for f in result)

def test_scan_files_preserves_structure():
    """测试扫描保持目录结构"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建子目录结构
        os.makedirs(os.path.join(tmpdir, 'subdir'))
        open(os.path.join(tmpdir, 'test.pdf'), 'w').close()
        open(os.path.join(tmpdir, 'subdir', 'test.docx'), 'w').close()

        result = scan_files(tmpdir)

        paths = [f['path'] for f in result]
        assert 'test.pdf' in paths
        assert os.path.join('subdir', 'test.docx') in paths
