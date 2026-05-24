"""打包脚本 - 将 doc2md 打包为可执行文件"""
import os
import sys
import shutil
import subprocess

def clean():
    """清理构建目录"""
    for d in ['build', 'dist']:
        if os.path.exists(d):
            shutil.rmtree(d)
            print(f'已清理: {d}/')

def get_magika_dir():
    """获取 magika 包目录路径"""
    try:
        result = subprocess.run(
            [sys.executable, '-c', 'import magika; import os; print(os.path.dirname(magika.__file__))'],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except Exception:
        pass
    return None

def build():
    """执行 PyInstaller 打包"""
    sep = ';' if os.name == 'nt' else ':'
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--name=doc2md',
        '--onefile',
        '--noconfirm',
        '--clean',
        # 添加数据文件
        f'--add-data=templates{sep}templates',
        f'--add-data=static{sep}static',
        f'--add-data=config.json{sep}.',
        # 隐藏导入
        '--hidden-import=markitdown',
        '--hidden-import=markitdown.converters',
        '--hidden-import=doc2docx',
        '--hidden-import=flask',
        '--hidden-import=pythoncom',
        # 收集 doc2docx 的完整包（包括元数据）
        '--collect-all=doc2docx',
    ]

    # 添加 magika 数据文件（models 和 config 目录）
    magika_dir = get_magika_dir()
    if magika_dir:
        for subdir in ['models', 'config']:
            subdir_path = os.path.join(magika_dir, subdir)
            if os.path.exists(subdir_path):
                cmd.append(f'--add-data={subdir_path}{sep}magika/{subdir}')
                print(f'找到 magika 目录: {subdir_path}')
    else:
        print('警告: 未找到 magika 包目录，转换功能可能不可用')

    # 入口文件
    cmd.append('app.py')

    print('开始打包...')
    print(f'命令: {" ".join(cmd)}')
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print('打包失败:')
        print(result.stderr)
        return False

    print('打包成功!')
    return True

def copy_extra_files():
    """复制额外需要的文件到 dist 目录"""
    dist_dir = 'dist'
    # 复制配置文件（覆盖打包内的默认配置）
    if os.path.exists('config.json'):
        shutil.copy('config.json', dist_dir)
        print(f'已复制: config.json -> {dist_dir}/')

def create_run_script():
    """创建运行脚本"""
    # Windows 批处理
    with open('dist/start.bat', 'w', encoding='utf-8') as f:
        f.write('@echo off\n')
        f.write('echo doc2md 文档转换工具\n')
        f.write('echo 启动中...\n')
        f.write('doc2md.exe\n')
        f.write('pause\n')
    print('已创建: dist/start.bat')

    # Linux shell 脚本
    with open('dist/start.sh', 'w', encoding='utf-8') as f:
        f.write('#!/bin/bash\n')
        f.write('echo "doc2md 文档转换工具"\n')
        f.write('echo "启动中..."\n')
        f.write('./doc2md\n')
    os.chmod('dist/start.sh', 0o755)
    print('已创建: dist/start.sh')

def main():
    # 切换到脚本所在目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    print('=' * 50)
    print('doc2md 打包工具')
    print('=' * 50)

    clean()

    if not build():
        sys.exit(1)

    copy_extra_files()
    create_run_script()

    print('\n' + '=' * 50)
    print('打包完成! 可执行文件在 dist/ 目录下')
    print('- Windows: dist/doc2md.exe 或 dist/start.bat')
    print('- Linux:   dist/doc2md 或 dist/start.sh')
    print('=' * 50)

if __name__ == '__main__':
    main()
