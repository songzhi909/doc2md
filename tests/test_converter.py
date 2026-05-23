import os
import tempfile
import pytest
from converter import scan_files, convert_file, convert_batch

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
            'test.htm',
            'test.csv',
            'test.json',
            'test.xml',
            'test.epub',
            'test.txt',
            'test.md',
            'test.doc',  # 不支持的旧版格式
            'test.exe',  # 不支持的格式
        ]
        for f in test_files:
            with open(os.path.join(tmpdir, f), 'w') as fp:
                pass

        result = scan_files(tmpdir)

        # 应该找到12个支持的文件，排除.doc和.exe
        assert len(result) == 12
        supported_types = {'pdf', 'docx', 'xlsx', 'pptx', 'html', 'htm', 'csv', 'json', 'xml', 'epub', 'txt', 'md'}
        assert all(f['type'] in supported_types for f in result)

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

def test_convert_file_nonexistent_input():
    """测试输入文件不存在时返回错误"""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = os.path.join(tmpdir, 'nonexistent.pdf')
        output_file = os.path.join(tmpdir, 'output.md')

        result = convert_file(input_file, output_file)
        assert result['success'] == False
        assert '输入文件不存在' in result['error']

def test_convert_file_success():
    """测试成功转换文件"""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = os.path.join(tmpdir, 'test.txt')
        output_file = os.path.join(tmpdir, 'sub', 'output.md')

        with open(input_file, 'w', encoding='utf-8') as f:
            f.write('Hello world')

        result = convert_file(input_file, output_file)
        assert result['success'] is True
        assert result['error'] is None
        assert os.path.exists(output_file)

        with open(output_file, encoding='utf-8') as f:
            assert 'Hello world' in f.read()

def test_convert_batch_processes_all_files():
    """测试批量转换处理所有文件"""
    with tempfile.TemporaryDirectory() as input_dir:
        with tempfile.TemporaryDirectory() as output_dir:
            # 创建测试文件结构（使用支持的格式）
            os.makedirs(os.path.join(input_dir, 'subdir'))
            with open(os.path.join(input_dir, 'test1.json'), 'w', encoding='utf-8') as f:
                f.write('{"key": "value1"}')
            with open(os.path.join(input_dir, 'subdir', 'test2.json'), 'w', encoding='utf-8') as f:
                f.write('{"key": "value2"}')

            result = convert_batch(input_dir, output_dir)

            assert result['converted'] == 2
            assert result['failed'] == 0
            assert result['failures'] == []
            assert os.path.exists(os.path.join(output_dir, 'test1.md'))
            assert os.path.exists(os.path.join(output_dir, 'subdir', 'test2.md'))

def test_convert_batch_empty_directory():
    """测试空目录返回零结果"""
    with tempfile.TemporaryDirectory() as input_dir:
        with tempfile.TemporaryDirectory() as output_dir:
            result = convert_batch(input_dir, output_dir)

            assert result['converted'] == 0
            assert result['failed'] == 0
            assert result['failures'] == []

def test_convert_batch_invalid_path():
    """测试无效输入路径返回错误"""
    with tempfile.TemporaryDirectory() as output_dir:
        result = convert_batch('/nonexistent/path', output_dir)

        assert result['converted'] == 0
        assert result['failed'] == 1
        assert len(result['failures']) == 1
        assert '输入路径不存在或不是目录' in result['failures'][0]['error']
