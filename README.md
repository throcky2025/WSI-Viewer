# WSI Viewer

WSI Viewer是一个用于查看WSI（Whole Slide Image）文件的Python模块。它提供了一个完整的Web界面，支持浏览、查看和测量WSI图像。

## 功能特点

- 支持多种WSI文件格式（.svs、.tif、.tiff）
- 提供流畅的图像浏览和缩放体验
- 支持距离和面积测量功能
- 支持添加标注点
- 测量结果可导出为CSV格式
- 提供完整的Python API和命令行接口

## 项目结构

```
wsi_viewer/
├── wsi_viewer/
│   ├── __init__.py              # 包初始化文件
│   ├── viewer.py                # WSIViewer核心类
│   ├── cli.py                   # 命令行接口
│   ├── api/                     # 后端API
│   │   ├── main.py             # FastAPI应用
│   │   ├── routers/
│   │   │   └── wsi.py          # WSI路由处理
│   │   └── services/
│   │       └── wsi_service.py   # WSI服务实现
│   └── frontend/               # 前端Vue.js应用
│       ├── package.json        # 依赖配置
│       ├── vite.config.js      # 构建配置
│       ├── index.html          # HTML入口
│       └── src/
│           ├── main.js         # Vue应用入口
│           ├── App.vue         # 主组件
│           ├── components/
│           │   └── WSIViewer.vue # 查看器组件
│           └── styles/
│               └── main.scss    # 全局样式
├── setup.py                    # 包安装配置
└── README.md                   # 文档
```

## 安装

### 前提条件

1. Python 3.7+
2. Node.js (推荐使用LTS版本)
3. npm (通常随Node.js一起安装)

### 从源代码安装

```bash
# 克隆仓库
git clone <repository-url>
cd chief_wsi_viewer

# 安装开发版本
pip install -e .
```

## 使用方法

### 作为Python模块使用

```python
from wsi_viewer import WSIViewer

# 创建查看器实例
viewer = WSIViewer(
    host="0.0.0.0",           # 可选，默认为0.0.0.0
    backend_port=5000,        # 可选，默认为5000
    frontend_port=3000,       # 可选，默认为3000
    static_dir="path/to/dir", # 可选，用于存储静态文件
    log_level="info"          # 可选，可选值：debug, info, warning, error
)

# 启动查看器服务
viewer.start()

# 停止服务（一般不需要手动调用，按Ctrl+C会自动停止）
viewer.stop()
```

### 通过命令行使用

安装后，你可以使用`chief-wsi-viewer`命令来启动查看器：

```bash
# 使用默认配置启动
chief-wsi-viewer

# 自定义配置启动
wsi-viewer --host 0.0.0.0 --backend-port 5000 --frontend-port 3000 --static-dir /path/to/dir --log-level info
```

可用的命令行参数：
- `--host`: 服务器主机地址 (默认: 0.0.0.0)
- `--backend-port`: 后端服务端口 (默认: 5000)
- `--frontend-port`: 前端服务端口 (默认: 3000)
- `--static-dir`: 静态文件目录路径
- `--log-level`: 日志级别 (可选值: debug, info, warning, error)

## 功能使用说明

### 浏览器访问

启动服务后，在浏览器中访问：`http://localhost:3000`（或你指定的前端端口）

### 工具栏功能

1. 平移工具：用于图像的平移和缩放
2. 测距工具：测量图像上两点之间的距离
3. 面积工具：测量图像上选定区域的面积
4. 标注工具：在图像上添加标注点

### 测量结果

- 所有测量结果将显示在左侧面板中
- 可以删除单个测量结果
- 可以清除所有测量结果
- 可以将测量结果导出为CSV文件

## 开发指南

### 安装开发依赖

```bash
# 后端开发依赖
pip install -e ".[dev]"

# 前端开发依赖
cd wsi_viewer/frontend
npm install
```

### 开发模式运行

```bash
# 运行后端服务
python -m wsi_viewer.cli --log-level debug

# 运行前端开发服务器（新终端）
cd wsi_viewer/frontend
npm run dev
```

### 构建前端

```bash
cd wsi_viewer/frontend
npm run build
```

## 故障排除

如果遇到问题，请尝试以下步骤：

1. 确保所有依赖都已正确安装
2. 检查是否有其他服务占用了端口（5000和3000）
3. 查看日志输出，了解详细错误信息
4. 如果前端依赖安装失败，可以进入frontend目录手动运行`npm install`

## 贡献指南

欢迎提交问题和改进建议！

1. Fork 这个项目
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的改动 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

## 许可证

MIT

## 技术栈

### 后端
- Python 3.7+
- FastAPI
- OpenSlide
- NumPy
- OpenCV

### 前端
- Vue.js 3
- Element Plus
- OpenSeadragon
- Vite
