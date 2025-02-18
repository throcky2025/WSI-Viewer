from fastapi import FastAPI, File, UploadFile, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
import logging
import logging.handlers
import os
import signal
import sys
import traceback
from .routers import wsi
from .services.wsi_service import WSIService

def setup_logging():
    """配置日志系统"""
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(processName)s - %(threadName)s - %(levelname)s - %(message)s'
    )
    
    # 配置文件处理器
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    
    # 配置控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # 设置第三方库的日志级别
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)

# 初始化日志
setup_logging()
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(title="CHIEF WSI Viewer API")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 获取项目根目录
ROOT_DIR = Path(__file__).parent.parent
STATIC_DIR = ROOT_DIR / "static"
SLIDES_DIR = STATIC_DIR / "slides"
TILES_DIR = STATIC_DIR / "tiles"

# 确保必要的目录存在
SLIDES_DIR.mkdir(parents=True, exist_ok=True)
TILES_DIR.mkdir(parents=True, exist_ok=True)

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# 注册路由
app.include_router(wsi.router, prefix="/api/slides", tags=["slides"])

# WebSocket连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket连接建立 - 当前连接数: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket连接断开 - 当前连接数: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"发送消息失败: {str(e)}")
                await self.disconnect(connection)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket错误: {str(e)}")
        manager.disconnect(websocket)

@app.get("/")
async def root():
    """健康检查端点"""
    return {"status": "ok", "message": "CHIEF WSI Viewer API is running"}

def start_server(host="0.0.0.0", port=5000, log_level="info"):
    """启动服务器"""
    # 设置进程启动方法
    if sys.platform == 'darwin':  # macOS
        import multiprocessing as mp
        mp.set_start_method('spawn')
    
    import uvicorn
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=log_level
    )

if __name__ == "__main__":
    start_server()