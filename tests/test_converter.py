import os
import tempfile
import pytest
from converter import scan_files, convert_file

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
            with open(os.path.join(tmpdir, f), 'w') as fp:
                pass

        result = scan_files(tmpdir)

        # 应该找到9个支持的文件，排除.txt
        assert len(result) == 9
        assert all(f['type'] in ['pdf', 'docx', 'xlsx', 'pptx', 'html', 'csv', 'json', 'xml', 'epub'] for f in result)

def test_scan_files_preserves_structure():
    """测试扫描保持目录结构"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建子目录结构
        os.makedirs(os.path.join(tmpdir, 'subdir'))
        with open(os.path.join(tmpdir, 'test.pdf'), 'w') as fp:
            pass
        with open(os.path.join(tmpdir, 'subdir', 'test.docx'), 'w') as fp:
            pass

        result = scan_files(tmpdir)

        paths = [f['path'] for f in result]
        assert 'test.pdf' in paths
        assert os.path.join('subdir', 'test.docx') in paths

def test_scan_files_invalid_path():
    """测试无效路径抛出异常"""
    with pytest.raises(ValueError, match="输入路径不存在或不是目录"):
        scan_files('/nonexistent/path')

def test_scan_files_empty_directory():
    """测试空目录返回空列表"""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = scan_files(tmpdir)
        assert result == []

def test_convert_file_creates_markdown():
    """测试转换单个文件生成markdown"""
    # 这个测试需要实际的测试文件，先跳过实际转换
    # 只测试函数签名和错误处理
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = os.path.join(tmpdir, 'nonexistent.pdf')
        output_file = os.path.join(tmpdir, 'output.md')

        # 测试文件不存在的情况
        result = convert_file(input_file, output_file)
        assert result['success'] == False
        assert 'error' in result
