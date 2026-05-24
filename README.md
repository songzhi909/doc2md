# doc2md - 文档转 Markdown 工具

一个基于 Web 界面的批量文档转换工具，支持将多种文档格式转换为 Markdown。

## 功能特性

- **多格式支持**：PDF、Word (.doc/.docx)、Excel (.xlsx)、PowerPoint (.pptx)、CSV、JSON、XML、HTML、EPUB、TXT
- **Web 界面**：浏览器操作，支持文件夹选择和文件上传
- **实时进度**：SSE 流式推送转换进度
- **批量转换**：一次性转换整个文件夹的文档
- **ZIP 导出**：转换完成后可打包下载
- **文件夹浏览**：自由选择输出路径
- **跨平台打包**：支持 Windows / Linux 独立运行

## 快速开始

### 方式一：源码运行

1. 安装依赖（推荐使用 conda 环境）：

```bash
pip install -r requirements.txt
```

2. 启动服务：

```bash
python app.py
```

3. 打开浏览器访问 http://127.0.0.1:5000

### 方式二：使用打包版本

1. 运行打包脚本：

```bash
python build.py
```

2. 进入 `dist` 目录：
   - Windows：双击 `start.bat` 或运行 `doc2md.exe`
   - Linux：运行 `./start.sh` 或 `./doc2md`

## 使用说明

1. **选择源文件夹**：点击「选择文件夹」按钮，选择包含文档的目录
2. **扫描文件**：点击「扫描」按钮，查看支持的文件列表
3. **设置输出路径**：默认 `./output`，可手动输入或点击「浏览」选择
4. **开始转换**：点击「开始转换」，实时查看进度
5. **导出结果**：转换完成后点击「导出 ZIP」下载

## 配置文件

编辑 `config.json` 自定义配置：

```json
{
    "server": {
        "host": "127.0.0.1",
        "port": 5000,
        "debug": true
    },
    "output": {
        "default_path": "./output"
    },
    "temp": {
        "dir": "./temp"
    },
    "supported_extensions": [
        "pdf", "doc", "docx", "xlsx", "pptx",
        "csv", "json", "xml",
        "html", "htm",
        "epub",
        "txt", "md"
    ],
    "log": {
        "dir": "logs",
        "max_bytes": 10485760,
        "backup_count": 5,
        "console_level": "INFO",
        "file_level": "DEBUG"
    }
}
```

| 配置项 | 说明 |
|--------|------|
| `server.host` | 监听地址 |
| `server.port` | 监听端口 |
| `output.default_path` | 默认输出目录 |
| `temp.dir` | 临时文件目录 |
| `supported_extensions` | 支持的文件扩展名 |
| `log.dir` | 日志目录 |
| `log.max_bytes` | 单个日志文件最大大小 |

## 项目结构

```
doc2md/
├── app.py              # Flask 主程序
├── converter.py        # 文档转换核心逻辑
├── config.py           # 配置管理
├── config.json         # 配置文件
├── logger.py           # 日志配置
├── build.py            # PyInstaller 打包脚本
├── requirements.txt    # Python 依赖
├── templates/
│   └── index.html      # Web 前端页面
├── static/
│   └── style.css       # 样式文件
└── tests/
    ├── test_api.py     # API 测试
    ├── test_converter.py
    └── test_integration.py
```

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/scan` | POST | 扫描文件夹，返回支持的文件列表 |
| `/api/convert` | POST | 批量转换（支持文件上传或本地路径） |
| `/api/convert-stream` | POST | 批量转换（SSE 流式进度） |
| `/api/export` | POST | 导出输出目录为 ZIP |
| `/api/browse` | POST | 浏览文件夹，返回子目录列表 |
| `/api/config` | GET/POST | 获取/保存配置 |

## 运行测试

```bash
python -m pytest tests/ -v
```

## 注意事项

- `.doc` 格式需要系统安装 Microsoft Word（通过 COM 调用转换）
- 从网上下载的 `.doc` 文件可能被 Word 安全策略阻止，需先右键属性解除锁定
- 打包版本首次启动较慢（需解压临时文件）

## 许可证

MIT License
